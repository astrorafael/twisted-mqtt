# -*- test-case-name: mqtt.client.test.test_subscriber -*-
# ----------------------------------------------------------------------
# Copyright (C) 2015 by Rafael Gonzalez 
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ----------------------------------------------------------------------

# ----------------
# Standard modules
# ----------------

from collections import deque

# ----------------
# Twisted  modules
# ----------------

from zope.interface   import implementer
from twisted.internet import defer, reactor, error
from twisted.logger   import Logger


# -----------
# Own modules
# -----------

from ..          import v31, PY2
from ..error     import MQTTWindowError
from ..pdu       import SUBSCRIBE, UNSUBSCRIBE, PUBACK, PUBREC, PUBCOMP
from .interfaces import IMQTTSubscriber
from .base       import MQTTBaseProtocol,  ConnectedState as BaseConnectedState
from .interval   import Interval


log = Logger()

# ---------------------------------
# MQTT Client Connected State Class
# ---------------------------------

class ConnectedState(BaseConnectedState):

    def subscribe(self, request):
        return self.protocol.doSubscribe(request)

    def unsubscribe(self, request):
        return self.protocol.doUnsubscribe(request)
    
    def handleSUBACK(self, response):
        self.protocol.handleSUBACK(response)

    def handleUNSUBACK(self, response):
        self.protocol.handleUNSUBACK(response)

    def handlePUBLISH(self, response):
        self.protocol.handlePUBLISH(response)

    # QoS=2 packets
    def handlePUBREL(self, response):
        self.protocol.handlePUBREL(response)

# ------------------------
# MQTT Client Protocol Class
# ------------------------

@implementer(IMQTTSubscriber)
class MQTTProtocol(MQTTBaseProtocol):
    '''
    Subscriber role MQTTClient Protocol
    '''   

    def __init__(self, factory):
        MQTTBaseProtocol.__init__(self, factory)
        # patches the state machine
        MQTTBaseProtocol.CONNECTED = ConnectedState(self) 
        self._onPublish        = None
        self._queueSubscribe   = deque()
        self._queueUnsubscribe = deque()

    # ------------------------------
    # IMQTTSubscriber Implementation
    # ------------------------------
  
    # --------------------------------------------------------------------------

    def subscribe(self, topics, qos=0):
        '''
        API entry point.
        '''
        request = SUBSCRIBE()
        request.topics = topics
        request.qos    = qos
        return self.state.subscribe(request)

    # --------------------------------------------------------------------------

    def unsubscribe(self, topics):
        '''
        API entry point.
        '''
        request = UNSUBSCRIBE()
        request.topics = topics
        return self.state.unsubscribe(request)

    # --------------------------------------------------------------------------

    def setPublishHandler(self, callback):
        '''
        API entry point
        '''
        self._onPublish = callback


    # ------------------------------------------
    # Southbound interface: Network entry points
    # ------------------------------------------

    def handleSUBACK(self, response):
        '''
        Handle SUBACK control packet received.
        '''
        log.debug("<== {packet:7} (id={response.msgId:04x})" , packet="SUBACK",  response=response)
        request = self._queueSubscribe.popleft()
        request.alarm.cancel()
        request.deferred.callback(response.granted)
       
    # --------------------------------------------------------------------------

    def handleUNSUBACK(self, response):
        '''
        Handle UNSUBACK control packet received.
        '''
        log.debug("<== {packet:7} (id={response.msgId:04x})" , packet="UNSUBACK",  response=response)
        request = self._queueUnsubscribe.popleft()
        request.alarm.cancel()
        request.deferred.callback(response.msgId)

    # --------------------------------------------------------------------------

    def handlePUBLISH(self, response):
        '''
        Handle PUBLISH control packet received.
        '''
        if  response.qos == 0:
            log.debug("==> {packet:7} (id={response.msgId} qos={response.qos} dup={response.dup} retain={response.retain})" , packet="PUBLISH", response=response)
            self._deliver(response)
        elif response.qos == 1:
            log.debug("==> {packet:7} (id={response.msgId:04x} qos={response.qos} dup={response.dup} retain={response.retain})" , packet="PUBLISH", response=response)
            reply = PUBACK()
            reply.msgId = response.msgId
            log.debug("<== {packet:7} (id={response.msgId:04x})" , packet="PUBACK", response=response)
            self.transport.write(reply.encode())
            self._deliver(response)
        elif response.qos == 2:
            log.debug("==> {packet:7} (id={response.msgId:04x} qos={response.qos} dup={response.dup} retain={response.retain})" , packet="PUBLISH", response=response)
            self.factory.queuePublishRx.append(response)
            reply = PUBREC()
            reply.msgId = response.msgId
            log.debug("<== {packet:7} (id={response.msgId:04x})" , packet="PUBREC", response=response)
            self.transport.write(reply.encode())

    # --------------------------------------------------------------------------

    def handlePUBREL(self, response):
        '''
        Handle PUBREL control packet received.
        '''
        log.debug("==> {packet:7}(id={response.msgId:04x} dup={response.dup})" , packet="PUBREL", response=response)
        msg = self.factory.queuePublishRx.popleft()
        self._deliver(msg)
        reply = PUBCOMP()
        reply.msgId = response.msgId
        reply.encode()
        log.debug("<== {packet:7} (id={response.msgId:04})" , packet="PUBCOMP", response=response)
        self.transport.write(reply.encode())

    # --------------------------
    # Twisted Protocol Interface
    # --------------------------

    def connectionLost(self, reason):
        MQTTBaseProtocol.connectionLost(self, reason)
        # Find out pending deferreds
        if len(self._queueSubscribe) or len(self._queueUnsubscribe):
            pendingDeferred = True
        else:
            pendingDeferred = False
        # Cancel Alarms first
        for request in self._queueSubscribe:
            if request.alarm is not None:
                request.alarm.cancel()
                request.alarm = None
        for request in self._queueUnsubscribe:
            if request.alarm is not None:
                request.alarm.cancel()
                request.alarm = None
        # Then, invoke errbacks anyway, 
        # since we do not persist SUBCRIBE/UNSUBSCRIBE ack state
        while len(self._queueSubscribe):
            request = self._queueSubscribe.popleft()
            request.deferred.errback(reason)
        while len(self._queueUnsubscribe):
            request = self._queueUnsubscribe.popleft()
            request.deferred.errback(reason)
        # Invoke disconnect callback if applicable
        if not pendingDeferred and self._onDisconnect:
            self._onDisconnect(reason)


    # ---------------------------
    # State Machine API callbacks
    # ---------------------------

    def doSubscribe(self, request):
        '''
        Send an SUBSCRIBE control packet.
        '''
        
        if isinstance(request.topics, str):
            request.topics = [(request.topics, request.qos)] 
        elif isinstance(request.topics, tuple):
            request.topics = [(request.topics[0], request.topics[1])] 
        try:
            self._checkSubscribe(request)
            request.msgId = self.factory.makeId()
            request.encode()
        except Exception as e:
            return defer.fail(e)
        request.interval = Interval()
        request.deferred = defer.Deferred()
        request.deferred.msgId = request.msgId
        self._queueSubscribe.append(request)
        self._retrySubscribe(request, False)
        return  request.deferred 

    # --------------------------------------------------------------------------

    def doUnsubscribe(self, request):
        '''
        Send an UNSUBSCRIBE control packet
        '''
        request.msgId = self.factory.makeId()
        if isinstance(request.topics, str):
            request.topics = [request.topics]
        try:
            self._checkUnsubscribe(request)
            request.msgId = self.factory.makeId()
            request.encode() 
        except Exception as e:
            return defer.fail(e)
        request.interval = Interval()
        request.deferred = defer.Deferred()
        request.deferred.msgId = request.msgId
        self._queueUnsubscribe.append(request)
        self._retryUnsubscribe(request, False)
        return  request.deferred 

    # --------------
    # Helper methods
    # --------------

    def _retrySubscribe(self, request, dup):
        '''
        Transmit/Retransmit SUBSCRIBE packet
        '''
        if self._version == v31:
            request.encoded[0] |=  (dup << 3)   # set the dup flag
        interval = request.interval() + 0.25*len(self._queueSubscribe)
        request.alarm = self.callLater(
            interval, self._subscribeError, request)
        log.debug("==> {packet:7} (id={request.msgId:04x} dup={dup})", packet="SUBSCRIBE", request=request, dup=dup)
        self.transport.write(str(request.encoded) if PY2 else bytes(request.encoded))

    # --------------------------------------------------------------------------

    def _retryUnsubscribe(self, request, dup):
        '''
        Transmit/Retransmit UNSUBSCRIBE packet
        '''
        if self._version == v31:
            request.encoded[0] |=  (dup << 3)   # set the dup flag
        interval = request.interval() + 0.25*len(self._queueUnsubscribe)
        request.alarm = self.callLater(
            interval, self._unsubscribeError, request)
        log.debug("==> {packet:7} (id={request.msgId:04x} dup={dup})", packet="UNSUBSCRIBE", request=request, dup=dup)
        self.transport.write(str(request.encoded) if PY2 else bytes(request.encoded))

    # --------------------------------------------------------------------------

    def _deliver(self, pdu):
        '''Deliver the message to the client if registered a callback'''
        if self._onPublish:
            self._onPublish(pdu.topic, pdu.payload, pdu.qos, pdu.dup, pdu.retain, pdu.msgId)

    # --------------------------------------------------------------------------

    def _subscribeError(self, request):
        '''
        Handle lack of SUBACK
        '''
        log.error("{packet:7} (id={request.msgId:04x}) {timeout}, retransmitting", packet="SUBSCRIBE", request=request,  timeout="timeout")
        self._retrySubscribe(request,  True)

    # --------------------------------------------------------------------------

    def _unsubscribeError(self, request):
        '''
        Handle ack of UNSUBACK packet
        '''
        log.error("{packet:7} (id={request.msgId:04x}) {timeout}, retransmitting", packet="UNSUBSCRIBE", request=request,  timeout="timeout")
        self.reUnubscribe(request,  True)

    # --------------------------------------------------------------------------

    def _checkSubscribe(self, request):
        '''
        Assert subscribe parameters
        '''
        if len(self._queueSubscribe) == self._window:
            raise MQTTWindowError("subscription requests exceeded limit", self._window)
        if not isinstance(request.topics, list):
            raise TypeError("Invalid parameter type 'topic'", type(topic))
        for (topic, qos) in request.topics:
            if not ( 0<= qos <= 3):
                raise ValueError("Last Will QoS out of [0..3] range", qos)

    # --------------------------------------------------------------------------

    def _checkUnsubscribe(self, request):
        '''
        Assert unsubscribe parameters
        '''
        if len(self._queueUnsubscribe) == self._window:
            raise MQTTWindowError("unsubscription requests exceeded limit", self._window)
        if not isinstance(request.topics, list):
            raise TypeError("Invalid parameter type 'topic'", type(topic))


    # --------------------------------------------------------------------------



__all__ = [MQTTProtocol]

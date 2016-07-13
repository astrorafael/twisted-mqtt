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
from ..error     import MQTTWindowError, QoSValueError, TopicTypeError
from ..pdu       import SUBSCRIBE, UNSUBSCRIBE, PUBACK, PUBREC, PUBCOMP, PUBLISH, PUBREL
from .interfaces import IMQTTSubscriber, IMQTTPublisher
from .interval   import Interval, IntervalLinear
from .base       import MQTTBaseProtocol, IdleState as BaseIdleState, ConnectingState as BaseConnectingState, ConnectedState as BaseConnectedState


log = Logger(namespace='mqtt')


class MQTTSessionCleared(Exception):
    '''MQTT persitent session cleared and message could not be published.'''
    def __str__(self):
        return self.__doc__

# ---------------------------------------------
# MQTT Client Idle State Class (for subscriber)
# ---------------------------------------------

class IdleState(BaseIdleState):

    def setPublishHandler(self, callback):
        self.protocol.doSetPublishHandler(callback)


# --------------------------------------------------
# MQTT Client Connecting State Class (for publisher)
# --------------------------------------------------

class ConnectingState(BaseConnectingState):

    def handleCONNACK(self, response):
        self.protocol.handleCONNACK(response)

    # The standard allows publishing data without waiting for CONNACK
    def publish(self, request):
        return self.protocol.doPublish(request)

    def setPublishHandler(self, callback):
        self.protocol.doSetPublishHandler(callback)

# ---------------------------------
# MQTT Client Connected State Class
# ---------------------------------

class ConnectedState(BaseConnectedState):

    def publish(self, request):
        return self.protocol.doPublish(request)

    def subscribe(self, request):
        return self.protocol.doSubscribe(request)

    def unsubscribe(self, request):
        return self.protocol.doUnsubscribe(request)

    def setPublishHandler(self, callback):
        self.protocol.doSetPublishHandler(callback)
    
    def handleSUBACK(self, response):
        self.protocol.handleSUBACK(response)

    def handleUNSUBACK(self, response):
        self.protocol.handleUNSUBACK(response)

    def handlePUBLISH(self, response):
        self.protocol.handlePUBLISH(response)

    # QoS=1 packets forwarded to subscriber
    def handlePUBACK(self, response):
        self.protocol.handlePUBACK(response)

    # QoS=2 packets forwarded to publisher
    def handlePUBREC(self, response):
        self.protocol.handlePUBREC(response)

    # QoS=2 packets forwarded to subscriber
    def handlePUBREL(self, dup, response):
        self.protocol.handlePUBREL(dup, response)

    # QoS=2 packets forwarded to publisher
    def handlePUBCOMP(self, response):
        self.protocol.handlePUBCOMP(response)

# --------------------------
# MQTT Client Protocol Class
# --------------------------

@implementer(IMQTTSubscriber, IMQTTPublisher)
class MQTTProtocol(MQTTBaseProtocol):
    '''
    MQTTClient publish/subscribe Protocol
    '''

    DEFAULT_BANDWITH = 10000

    def __init__(self, factory):
        MQTTBaseProtocol.__init__(self, factory) 
        # patches and reparent the state machine
        self.IDLE          = IdleState(self)
        self.CONNECTING    = ConnectingState(self)
        self.CONNECTED     = ConnectedState(self)
        self.state         = self.IDLE
        # Estimated bandwith in bytes/sec for PUBLISH PDUs
        self._bandwith     =  self.DEFAULT_BANDWITH
        # additional, per-connection subscriber state
        self._onPublish   = None
        
      
       
    # -----------------------------
    # IMQTTPublisher Implementation
    # -----------------------------
  
    def setBandwith(self, bandwith):
        if bandwith <= 0:
            raise VauleError("Bandwith should be a positive number")
        self._bandwith = bandwith

    
    def publish(self, topic, message, qos=0, retain=False):
        '''
        API entry point.
        '''
        request = PUBLISH()
        request.qos     = qos
        request.topic   = topic
        request.payload = message
        request.retain  = retain
        request.dup     = False
        return self.state.publish(request)


    # ---------------------------------
    # IMQTTSubscriber Implementation
    # ---------------------------------

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
        API entry 
        '''
        self.state.setPublishHandler(callback)


    # ------------------------------------------
    # Southbound interface: Network entry points
    # ------------------------------------------

    # handleSUBACK(), handleUNSUBACK() handlePUBLISH() & handlePUBREL() for subscribers
    def handleSUBACK(self, response):
        '''
        Handle SUBACK control packet received.
        '''
        log.debug("<== {packet:7} (id={response.msgId:04x})" , packet="SUBACK",  response=response)
        request = self.factory.windowSubscribe[self.factory.addr][response.msgId]
        del self.factory.windowSubscribe[self.factory.addr][response.msgId]
        request.alarm.cancel()
        request.deferred.callback(response.granted)
       
    # --------------------------------------------------------------------------

    def handleUNSUBACK(self, response):
        '''
        Handle UNSUBACK control packet received.
        '''
        log.debug("<== {packet:7} (id={response.msgId:04x})" , packet="UNSUBACK",  response=response)
        request = self.factory.windowUnsubscribe[self.factory.addr][response.msgId]
        del self.factory.windowUnsubscribe[self.factory.addr][response.msgId]
        request.alarm.cancel()
        request.deferred.callback(response.msgId)

    # --------------------------------------------------------------------------

    def handlePUBLISH(self, response):
        '''
        Handle PUBLISH control packet received.
        '''
        if  response.qos == 0:
            log.debug("==> {packet:7} (id={response.msgId} qos={response.qos} dup={response.dup} retain={response.retain} topic={response.topic})" , packet="PUBLISH", response=response)
            self._deliver(response)
        elif response.qos == 1:
            log.debug("==> {packet:7} (id={response.msgId:04x} qos={response.qos} dup={response.dup} retain={response.retain} topic={response.topic})" , packet="PUBLISH", response=response)
            reply = PUBACK()
            reply.msgId = response.msgId
            log.debug("<== {packet:7} (id={response.msgId:04x})" , packet="PUBACK", response=response)
            self.transport.write(reply.encode())
            self._deliver(response)
        elif response.qos == 2:
            log.debug("==> {packet:7} (id={response.msgId:04x} qos={response.qos} dup={response.dup} retain={response.retain} topic={response.topic})" , packet="PUBLISH", response=response)
            self.factory.windowPubRx[self.factory.addr][response.msgId] = response
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
        msg = self.factory.windowPubRx[self.factory.addr][response.msgId]
        del self.factory.windowPubRx[self.factory.addr][response.msgId]
        self._deliver(msg)
        reply = PUBCOMP()
        reply.msgId = response.msgId
        reply.encode()
        log.debug("<== {packet:7} (id={response.msgId:04})" , packet="PUBCOMP", response=response)
        self.transport.write(reply.encode())

    # --------------------------------------------------------------------------

    # handlePUBACK(), handlePUBREC() & handlePUBCOMP() are for publisher

    def handlePUBACK(self, response):
        '''
        Handle PUBACK control packet received (QoS=1).
        '''
        # so:  response.msgId == windowPublish[self.factory.addr][0].msgId
        log.debug("<== {packet:7} (id={response.msgId:04x})", packet="PUBACK", response=response)
        request = self.factory.windowPublish[self.factory.addr][response.msgId]
        request.alarm.cancel()
        request.deferred.callback(request.msgId)
        del self.factory.windowPublish[self.factory.addr][response.msgId]
        self._refillPublish(dup=False)

    # --------------------------------------------------------------------------

    def handlePUBREC(self, response):
        '''
        Handle PUBREC control packet received (QoS=2).
        '''
        # so:  response.msgId == windowPublish[self.factory.addr][0].msgId
        log.debug("<== {packet:7} (id={response.msgId:04x})", packet="PUBREC", response=response)
        request = self.factory.windowPublish[self.factory.addr][response.msgId]
        request.alarm.cancel()
        del self.factory.windowPublish[self.factory.addr][response.msgId]
        reply = PUBREL()
        reply.msgId = response.msgId
        reply.interval = Interval()
        reply.deferred = request.deferred       # Transfer the deferred to PUBREL
        reply.encode()
        self.factory.windowPubRelease[self.factory.addr][reply.msgId] = reply
        self._retryRelease(reply, False)


    # --------------------------------------------------------------------------

    def handlePUBCOMP(self, response):
        '''
        Handle PUBCOMP control packet received (QoS=2).
        '''
        # Same comment as PUBACK
        log.debug("<== {packet:7} (id={response.msgId:04x})", packet="PUBCOMP", response=response)
        reply = self.factory.windowPubRelease[self.factory.addr][response.msgId]
        reply.alarm.cancel()
        reply.deferred.callback(reply.msgId)
        del self.factory.windowPubRelease[self.factory.addr][reply.msgId]
        self._refillPublish(dup=False)


    # --------------------------
    # Twisted Protocol Interface
    # --------------------------

    def connectionLost(self, reason):
        log.debug("CONNECTION LOST")
        MQTTBaseProtocol.connectionLost(self, reason)
        disconnectAllowed1 = self._subs_connectionLost(reason)
        disconnectAllowed2 = self._pub_connectionLost(reason)
        if disconnectAllowed1 and disconnectAllowed2 and self._onDisconnect:
            self._onDisconnect(reason)



    # ---------------------------
    # Protocol API for subclasses
    # ---------------------------

    def mqttConnectionMade(self):
        '''
        Called when a CONNACK has been received (publisher only).
        '''
        if self._cleanStart:
            self._purgeSession()
        else:
            self._syncSession()

    # ---------------------------
    # State Machine API callbacks
    # ---------------------------

    def doSubscribe(self, request):
        '''
        Send a SUBSCRIBE control packet.
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
        self.factory.windowSubscribe[self.factory.addr][request.msgId] = request
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
        self.factory.windowUnsubscribe[self.factory.addr][request.msgId] = request
        self._retryUnsubscribe(request, dup=False)
        return  request.deferred

    # --------------------------------------------------------------------------

    def doSetPublishHandler(self, callback):
        '''
        Stores the publish callback
        '''
        self._onPublish = callback

    # --------------------------------------------------------------------------

    def doPublish(self, request):
        '''
        Send PUBLISH control packet
        '''

        try:
            self._checkPublish(request)
        except Exception as e:
            return defer.fail(e)

        if request.qos == 0:
            request.msgId    = None
            request.deferred = defer.succeed(None)
            request.interval = None
        else:
            request.msgId    = self.factory.makeId()
            request.deferred = defer.Deferred()
            request.interval = IntervalLinear(bandwith=self._bandwith)
        
        try:
            request.encode()
        except Exception as e:
            return defer.fail(e)

        self.factory.queuePublishTx[self.factory.addr].append(request)
        request.deferred.msgId = request.msgId
        self._refillPublish(dup=False)
        return  request.deferred 


    # --------------------------
    # Helper methods (subscriber)
    # ---------------------------

    def _retrySubscribe(self, request, dup):
        '''
        Transmit/Retransmit SUBSCRIBE packet
        '''
        if self._version == v31:
            request.encoded[0] |=  (dup << 3)   # set the dup flag
        interval = request.interval() + 0.25*len(self.factory.windowSubscribe[self.factory.addr])
        request.alarm = self.callLater(interval, self._subscribeError, request)
        log.debug("==> {packet:7} (id={request.msgId:04x} dup={dup})", packet="SUBSCRIBE", request=request, dup=dup)
        self.transport.write(str(request.encoded) if PY2 else bytes(request.encoded))

    # --------------------------------------------------------------------------

    def _retryUnsubscribe(self, request, dup):
        '''
        Transmit/Retransmit UNSUBSCRIBE packet
        '''
        if self._version == v31:
            request.encoded[0] |=  (dup << 3)   # set the dup flag
        interval = request.interval() + 0.25*len(self.factory.windowUnsubscribe[self.factory.addr])
        request.alarm = self.callLater(interval, self._unsubscribeError, request)
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
        self._retrySubscribe(request,  dup=True)

    # --------------------------------------------------------------------------

    def _unsubscribeError(self, request):
        '''
        Handle ack of UNSUBACK packet
        '''
        log.error("{packet:7} (id={request.msgId:04x}) {timeout}, retransmitting", packet="UNSUBSCRIBE", request=request,  timeout="timeout")
        self.reUnubscribe(request,  dup=True)

    # --------------------------------------------------------------------------

    def _checkSubscribe(self, request):
        '''
        Assert subscribe parameters
        '''
        if len(self.factory.windowSubscribe[self.factory.addr]) == self._window:
            raise MQTTWindowError("subscription requests exceeded limit", self._window)
        if not isinstance(request.topics, list):
            raise TopicTypeError(type(topic))
        for (topic, qos) in request.topics:
            if not ( 0<= qos < 3):
                raise QoSValueError("subscribe", qos)

    # --------------------------------------------------------------------------

    def _checkUnsubscribe(self, request):
        '''
        Assert unsubscribe parameters
        '''
        if len(self.factory.windowUnsubscribe[self.factory.addr]) == self._window:
            raise MQTTWindowError("unsubscription requests exceeded limit", self._window)
        if not isinstance(request.topics, list):
            raise TopicTypeError(type(topic))

    # --------------------------
    # Helper methods (publisher)
    # --------------------------

    def _refillPublish(self, dup):
        '''
        Refills the Publisher transmission window from the queue 
        '''
        cnx = self.factory.addr
        N = min(self._window - len(self.factory.windowPublish[cnx]), len(self.factory.queuePublishTx[cnx]))
        for i in range(0,N):
            request = self.factory.queuePublishTx[cnx].popleft()
            if request.msgId:   # only form QoS 1 & 2
                self.factory.windowPublish[cnx][request.msgId] = request
            self._retryPublish(request, dup)


    def _retryPublish(self, request, dup):
        '''
        Transmit/Retransmit one PUBLISH packet 
        '''
        request.encoded[0] |=  (dup << 3)   # set the dup flag
        request.dup = dup
        if request.interval:    # Handle timeouts for QoS 1 and 2
            request.alarm = self.callLater(request.interval(len(request.encoded)), self._publishError, request)
        if request.msgId is None:
            log.debug("==> {packet:7} (id={request.msgId} qos={request.qos} dup={dup})", packet="PUBLISH", request=request, dup=dup)
        else:
            log.debug("==> {packet:7} (id={request.msgId:04x} qos={request.qos} dup={dup})", packet="PUBLISH", request=request, dup=dup)
        self.transport.write(str(request.encoded) if PY2 else bytes(request.encoded))

    # --------------------------------------------------------------------------

    def _retryRelease(self, reply, dup):
        '''
        Transmit/Retransmit PUBREL packet 
        '''
        if self._version == v31:
            reply.encoded[0] |=  (dup << 3)   # set the dup flag
            reply.dup = dup
        reply.alarm = self.callLater(reply.interval(), self._pubrelError, reply)
        log.debug("==> {packet:7} (id={reply.msgId:04x} dup={dup})", packet="PUBREL", reply=reply, dup=dup)
        self.transport.write(str(reply.encoded) if PY2 else bytes(reply.encoded))

    # --------------------------------------------------------------------------


    # According to QoS = 1 we should never give up _retryPublish as long as 
    # we are connected to a server. So there is no retry count.

    def _publishError(self, request):
        '''
        Handle the absence of PUBACK / PUBREC 
        '''
        log.error("{packet:7} (id={request.msgId:04x} qos={request.qos}) {timeout}, _retryPublish", packet="PUBREC/PUBACK", request=request, timeout="timeout")
        self._retryPublish(request, dup=True)

    # --------------------------------------------------------------------------

    def _pubrelError(self, reply):
        '''
        Handle the absence of PUBCOMP 
        '''
        log.error("{packet:7} (id={request.msgId:04x} qos={request.qos}) {timeout}, _retryPublish", packet="PUBCOMP", request=request, timeout="timeout")
        self._retryRelease(reply, dup=True)

    # --------------------------------------------------------------------------

    def _checkPublish(self, request):
        '''
        Assert publish parameters
        '''
        if not ( 0<= request.qos < 3):
            raise QoSValueError("publish()",request.qos)
    
    # --------------------------------------------------------------------------

    def _syncSession(self):
        '''
        Tries to restore the session state upon a new MQTT connection made (publisher)
        '''
        log.debug("{event}", event="Sync Persistent Session")
        for _, reply in self.factory.windowPubRelease[self.factory.addr].items():
            self._retryRelease(reply, dup=True)
        for _, request in self.factory.windowPublish[self.factory.addr].items():
            self._retryPublish(request, dup=True)

    # --------------------------------------------------------------------------

    def _purgeSession(self):
        '''
        Purges the persistent state in the client 
        '''
        log.debug("{event}", event="Clean Persistent Session")
        for k in self.factory.windowPublish[self.factory.addr].keys():
            request = self.factory.windowPublish[self.factory.addr][k]
            del self.factory.windowPublish[self.factory.addr][k]
            request.deferred.errback(MQTTSessionCleared)

        for k in self.factory.windowPubRelease[self.factory.addr].keys():
            request = self.factory.windowPubRelease[self.factory.addr][k]
            del self.factory.windowPubRelease[self.factory.addr][k]
            request.deferred.errback(MQTTSessionCleared)


    # -------------------------------------
    # Helper methods (publisher/subscriber)
    # -------------------------------------

    def _subs_connectionLost(self, reason):
        '''
        Subscriber connection lost handling.
        Returns True if we can invoke the disconnect callback
        '''
       
        # Find out pending deferreds
        if len(self.factory.windowSubscribe[self.factory.addr]) or len(self.factory.windowUnsubscribe[self.factory.addr]):
            pendingDeferred = True
        else:
            pendingDeferred = False
        # Cancel Alarms first
        for _, request in self.factory.windowSubscribe[self.factory.addr].items():
            if request.alarm is not None:
                request.alarm.cancel()
                request.alarm = None
        for _, request in self.factory.windowUnsubscribe[self.factory.addr].items():
            if request.alarm is not None:
                request.alarm.cancel()
                request.alarm = None
        # Then, invoke errbacks anyway if we do not persist state
        if self._cleanStart:
            for k in self.factory.windowSubscribe[self.factory.addr].keys():
                request = self.factory.windowSubscribe[self.factory.addr][k]
                del self.factory.windowSubscribe[self.factory.addr][k]
                request.deferred.errback(reason)
            for k in self.factory.windowUnsubscribe[self.factory.addr].keys():
                request = self.factory.windowUnsubscribe[self.factory.addr][k]
                del self.factory.windowUnsubscribe[self.factory.addr][k]
                request.deferred.errback(reason)
        return not pendingDeferred
       


    def _pub_connectionLost(self, reason):
        '''
        Publisher connection lost handling. 
        Returns True if we can invoke the disconnect callback
        '''
         # Find out pending deferreds
        if len(self.factory.windowPubRelease[self.factory.addr]) or len(self.factory.windowPublish[self.factory.addr]):
            pendingDeferred = True
        else:
            pendingDeferred = False
        # Cancel Alarms first
        for _, request in self.factory.windowPublish[self.factory.addr].items():
            if request.alarm is not None:
                request.alarm.cancel()
                request.alarm = None
        for _, request in self.factory.windowPubRelease[self.factory.addr].items():
            if request.alarm is not None:
                request.alarm.cancel()
                request.alarm = None
        # Then, invoke errbacks if we do not persist state
        if self._cleanStart:
            for k in self.factory.windowPubRelease[self.factory.addr].keys():
                request = self.factory.windowPubRelease[self.factory.addr][k]
                del self.factory.windowPubRelease[self.factory.addr][k]
                request.deferred.errback(reason)
                
            for k in self.factory.windowPublish[self.factory.addr].keys():
                request = self.factory.windowPublish[self.factory.addr][k]
                del self.factory.windowPublish[self.factory.addr][k]
                request.deferred.errback(reason)   

        return not (pendingDeferred and self._cleanStart)

__all__ = [MQTTProtocol]

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
from ..pdu       import PUBLISH, PUBREL
from .interfaces import IMQTTPublisher
from .base       import MQTTBaseProtocol 
from .base       import ConnectingState as BaseConnectingState, ConnectedState as BaseConnectedState
from .interval   import Interval

log = Logger()



class MQTTSessionCleared(Exception):
    '''MQTT persitent session cleared and message could not be published.'''
    def __str__(self):
        return self.__doc__
    
# ---------------------------------------
# MQTT Client Connecting State Class
# ---------------------------------------

class ConnectingState(BaseConnectingState):

    def handleCONNACK(self, response):
        self.protocol.handleCONNACK(response)

    # The standard allows publishing data without waiting for CONNACK
    def publish(self, request):
        return self.protocol.doPublish(request)


# ---------------------------------
# MQTT Client Connected State Class
# ---------------------------------

class ConnectedState(BaseConnectedState):

    def publish(self, request):
        return self.protocol.doPublish(request)

    def handlePUBACK(self, response):
        self.protocol.handlePUBACK(response)

    def handlePUBREC(self, response):
        self.protocol.handlePUBREC(response)

    def handlePUBCOMP(self, response):
        self.protocol.handlePUBCOMP(response)

   

# ------------------------
# MQTT Client Protocol Class
# ------------------------

@implementer(IMQTTPublisher)
class MQTTProtocol(MQTTBaseProtocol):
    '''
    Publisher role MQTT Client Protocol
    '''
    

    def __init__(self, factory):
        MQTTBaseProtocol.__init__(self, factory)
        # patches the state machine
        MQTTBaseProtocol.CONNECTING = ConnectingState(self) 
        MQTTBaseProtocol.CONNECTED  = ConnectedState(self)   

    # -----------------------------
    # IMQTTPublisher Implementation
    # -----------------------------
  
    # --------------------------------------------------------------------------
    
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
    
    # ---------------------------
    # Protocol API for subclasses
    # ---------------------------

    def mqttConnectionMade(self):
        '''
        Called when a CONNACK has been received.
        '''
        if self._cleanStart:
            self._purgeSession()
        else:
            self._syncSession()

    # ------------------------------------------
    # Southbound interface: Network entry points
    # ------------------------------------------

    def handlePUBACK(self, response):
        '''
        Handle PUBACK control packet received (QoS=1).
        '''
        # By design PUBACK cannot arrive unordered, and we always pop the oldest one from the queue,
        # so:  response.msgId == queuePublishTx[0].msgId
        log.debug("<== {packet:7} (id={response.msgId:04x})", packet="PUBACK", response=response)
        request = self.factory.queuePublishTx.popleft()
        request.alarm.cancel()
        request.deferred.callback(request.msgId)

    # --------------------------------------------------------------------------

    def handlePUBREC(self, response):
        '''
        Handle PUBREC control packet received (QoS=2).
        '''
        # By design PUBREC cannot arrive unordered, and we always pop the oldest one from the queue,
        # so:  response.msgId == queuePublishTx[0].msgId
        log.debug("<== {packet:7} (id={response.msgId:04x})", packet="PUBREC", response=response)
        request = self.factory.queuePublishTx.popleft()
        request.alarm.cancel()
        reply = PUBREL()
        reply.msgId = response.msgId
        reply.interval = Interval()
        reply.deferred = request.deferred       # Transfer the deferred to PUBREL
        reply.encode()
        self.factory.queuePubRelease.append(reply)
        self._retryRelease(reply, False)


    # --------------------------------------------------------------------------

    def handlePUBCOMP(self, response):
        '''
        Handle PUBCOMP control packet received (QoS=2).
        '''
        # Same comment as PUBACK
        log.debug("<== {packet:7} (id={response.msgId:04x})", packet="PUBCOMP", response=response)
        reply = self.factory.queuePubRelease.popleft() 
        reply.alarm.cancel()
        reply.deferred.callback(reply.msgId)
         

    # --------------------------
    # Twisted Protocol Interface
    # --------------------------

    def connectionLost(self, reason):
        MQTTBaseProtocol.connectionLost(self, reason)
         # Find out pending deferreds
        if len(self.factory.queuePubRelease) or len(self.factory.queuePublishTx):
            pendingDeferred = True
        else:
            pendingDeferred = False
        # Cancel Alarms first
        for request in self.factory.queuePublishTx:
            if request.alarm is not None:
                request.alarm.cancel()
                request.alarm = None
        for request in self.factory.queuePubRelease:
            if request.alarm is not None:
                request.alarm.cancel()
                request.alarm = None
        # Then, invoke errbacks if we do not persist state
        if self._cleanStart:
            while len(self.factory.queuePubRelease):
                request = self.factory.queuePubRelease.popleft()
                request.deferred.errback(reason)
            while len(self.factory.queuePublishTx):
                request = self.factory.queuePublishTx.popleft()
                request.deferred.errback(reason)
        # Invoke disconnect callback if applicable
        if not (pendingDeferred and self._cleanStart) and self._onDisconnect:
            self._onDisconnect(reason)


    # ---------------------------
    # State Machine API callbacks
    # ---------------------------

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
            request.interval = Interval()
            self.factory.queuePublishTx.append(request)
            
        try:
            request.encode()
        except Exception as e:
            return defer.fail(e)
        
        request.deferred.msgId = request.msgId
        self._retryPublish(request, False)
        return  request.deferred 

    
    # -------------
    # Helper methods
    # --------------

    def _retryPublish(self, request, dup):
        '''
        Transmit/Retransmit PUBLISH packet
        '''
        request.encoded[0] |=  (dup << 3)   # set the dup flag
        request.dup = dup
        if request.interval:
            request.alarm = self.callLater(
            request.interval(), self._publishError, request)
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
        reply.alarm = self.callLater(
            reply.interval(), self._pubrelError, reply)
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
        self._retryPublish(request, True)

    # --------------------------------------------------------------------------

    def _pubrelError(self, reply):
        '''
        Handle the absence of PUBCOMP
        '''
        log.error("{packet:7} (id={request.msgId:04x} qos={request.qos}) {timeout}, _retryPublish", packet="PUBCOMP", request=request, timeout="timeout")
        self._retryRelease(reply, True)

    # --------------------------------------------------------------------------

    def _checkPublish(self, request):
        '''
        Assert publish parameters
        '''
        if len(self.factory.queuePublishTx) + len(self.factory.queuePubRelease) == self._window:
            raise MQTTWindowError("unsubscription requests exceeded limit", self._window)
    
        if not ( 0<= request.qos <= 3):
            raise ValueError("Publish QoS out of [0..3] range", request.qos)
    
    # --------------------------------------------------------------------------

    def _syncSession(self):
        '''
        Tries to restore the session state upon a new MQTT connection made
        '''
        log.debug("{event}", event="Sync Persistent Session")
        for reply in self.factory.queuePubRelease:
            self._retryRelease(reply, True)
        for request in self.factory.queuePublishTx:
            self._retryPublish(request, True)

    # --------------------------------------------------------------------------

    def _purgeSession(self):
        '''
        Purges the persistent state in the client
        '''
        log.debug("{event}", event="Clean Persistent Session")
        while len(self.factory.queuePublishTx):
            request = self.factory.queuePublishTx.popleft()
            request.deferred.errback(MQTTSessionCleared)
        while len(self.factory.queuePubRelease):
            request = self.factory.queuePubRelease.popleft()
            request.deferred.errback(MQTTSessionCleared)


__all__ = [MQTTProtocol]

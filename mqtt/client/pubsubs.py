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

from zope.interface import implementer
from twisted.internet import defer, reactor
from twisted.logger   import Logger

# -----------
# Own modules
# -----------

from .interfaces import IMQTTSubscriber, IMQTTPublisher
from .base       import MQTTBaseProtocol, MQTTWindowError
from .base       import IdleState, ConnectedState as BaseConnectedState
from .subscriber import MQTTProtocol as MQTTSubscriberProtocol
from .publisher  import MQTTProtocol as MQTTPublisherProtocol, ConnectingState


log = Logger()

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

    def __init__(self, factory):
        # order is imporant to patch the states since the
        # delegats patches teh state as well
        self.subscriber = MQTTSubscriberProtocol(factory)
        self.publisher  = MQTTPublisherProtocol(factory)
        MQTTBaseProtocol.__init__(self, factory) 
        # patches and reparent the state machine
        MQTTBaseProtocol.CONNECTING = ConnectingState(self)
        MQTTBaseProtocol.CONNECTED  = ConnectedState(self)
        self._expectedDisc = None  # these two are ethe only extra state
        self._nDisc        = None  
       
    # ---------------------------------
    # IMQTTClientControl Implementation
    # ---------------------------------

    def setDisconnectCallback(self, callback):
        '''
        API Entry Point
        '''
        self._onDisconnect = callback
        self.subscriber.setDisconnectCallback(self._trapDisconnect)
        self.publisher.setDisconnectCallback(self._trapDisconnect)

    # ---------------------------------
    # IMQTTSubscriber Implementation
    # ---------------------------------
  
    def subscribe(self, topic, qos=0):
        '''
        API entry point.
        '''
        return self.subscriber.subscribe(topic, qos)

    def unsubscribe(self, topic):
        '''
        API entry point.
        '''
        return self.subscriber.unsubscribe(topic)

    def setPublishHandler(self, callback):
        '''
        API entry point
        '''
        self.subscriber.setPublishHandler(callback)

    # -----------------------------
    # IMQTTPublisher Implementation
    # -----------------------------

    def publish(self, topic, message, qos=0, retain=False):
        '''
        API entry point.
        '''
        return self.publisher.publish(topic, message, qos, retain)

    # --------------------------
    # Twisted Protocol Interface
    # --------------------------

    def connectionLost(self, reason):
        self._expectedDisc = 0
        self._nDisc        = 0
        flagPub  = (len(self.factory.queuePubRelease)    or len(self.factory.queuePublishTx)) != 0
        flagSubs = (len(self.subscriber._queueSubscribe) or len(self.subscriber._queueUnsubscribe)) != 0
        if not flagSubs:
            self._expectedDisc += 1
        if not(flagPub and self._cleanStart):
            self._expectedDisc += 1
        self.subscriber.connectionLost(reason)
        self.publisher.connectionLost(reason)

    # ---------------------------
    # Protocol API for subclasses
    # ---------------------------

    def mqttConnectionMade(self):
        '''
        Called when a CONNACK has been received.
        Overriden in subscriber/publisher to do additional session sync
        '''
        # Important to share this with the publisher for disconnections
        self.publisher._cleanStart = self._cleanStart
         # I need to share the transport with my own delegates
        self.subscriber.transport = self.transport
        self.publisher.transport  = self.transport
        # propagate this
        self.subscriber.mqttConnectionMade()
        self.publisher.mqttConnectionMade()


    # -------------------------------
    # Handle traffic form the network
    # -------------------------------
        
    def handleSUBACK(self, response):
        '''
        Handle SUBACK control packet received.
        '''
        self.subscriber.handleSUBACK(response)

    def handleUNSUBACK(self, response):
        '''
        Handle UNSUBACK control packet received.
        '''
        self.subscriber.handleUNSUBACK(response)

    def handlePUBLISH(self, response):
        '''
        Handle PUBLISH control packet received.
        '''
        self.subscriber.handlePUBLISH(response)

    def handlePUBACK(self, response):
        '''
        Handle PUBACK control packet received.
        ''' 
        self.publisher.handlePUBACK(response)

    def handlePUBREC(self, response):
        '''
        Handle PUBREC control packet received.
        ''' 
        self.publisher.handlePUBREC(response)

    def handlePUBREL(self, response):
        '''
        Handle PUBREL control packet received.
        '''
        self.subscriber.handlePUBREL(response)

    def handlePUBCOMP(self, response):
        '''
        Handle PUBCOMP control packet received.
        ''' 
        self.publisher.handlePUBCOMP(response)

    # ---------------------------
    # State Machine API callbacks
    # ---------------------------

    def doSubscribe(self, request):
        '''
        Send an UNSUBSCRIBE control packet.
        '''
        return self.subscriber.doSubscribe(request)

    def doUnsubscribe(self, topic):
        '''
        Send an UNSUBSCRIBE control packet
        ''' 
        return self.subscriber.doUnsubscribe(request)
    
    def doPublish(self, request):
        '''
        Send PUBLISH control packet
        '''
        return self.publisher.doPublish(request)

    # --------------
    # Helper methods
    # --------------

    def _trapDisconnect(self, reason):
        self._nDisc += 1
        if self._nDisc == self._expectedDisc and self._onDisconnect:
            self._onDisconnect(reason)


__all__ = [MQTTProtocol]

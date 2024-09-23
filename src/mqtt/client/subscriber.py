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

# ----------------
# Twisted  modules
# ----------------

from zope.interface   import implementer
from twisted.logger   import Logger


# -----------
# Own modules
# -----------

from .interfaces import IMQTTSubscriber
from .base       import ConnectedState as BaseConnectedState
from .pubsubs    import MQTTProtocol as PubSubsMQTTProtocol


log = Logger(namespace='mqtt')

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
class MQTTProtocol(PubSubsMQTTProtocol):
    '''
    Subscriber role MQTTClient Protocol
    '''   

    def __init__(self, factory, addr):
        PubSubsMQTTProtocol.__init__(self, factory, addr)
        # patches the state machine
        self.CONNECTED = ConnectedState(self)
        

__all__ = [ "MQTTProtocol" ]

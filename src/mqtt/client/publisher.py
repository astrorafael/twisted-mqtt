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

from .interfaces import IMQTTPublisher
from .base       import IdleState, ConnectingState as BaseConnectingState, ConnectedState as BaseConnectedState
from .pubsubs    import MQTTProtocol    as PubSubsMQTTProtocol

log = Logger(namespace='mqtt')

# --------------------------------------------------
# MQTT Client Connecting State Class (for publisher)
# --------------------------------------------------

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
class MQTTProtocol(PubSubsMQTTProtocol):
    '''
    Publisher role MQTT Client Protocol
    '''

    def __init__(self, factory, addr):
        PubSubsMQTTProtocol.__init__(self, factory, addr)
        # patches the state machine
        self.IDLE       = IdleState(self)
        self.CONNECTING = ConnectingState(self) 
        self.CONNECTED  = ConnectedState(self)
        self.state      = self.IDLE


__all__ = [ "MQTTProtocol" ]

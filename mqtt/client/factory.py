# -*- test-case-name: mqtt.client.test.test_factory -*-
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

# ReconnectingClientFactory is becoming obsolete
# since applications now have ClientService and its retryPolicy parameter
# See chapter "Getting Connected with Endpoints" in the Twisted manual
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.logger import Logger

# -----------
# Own modules
# -----------

from ..      import __version__
from ..error import ProfileValueError

log = Logger(namespace='mqtt')

class MQTTFactory(ReconnectingClientFactory):


    SUBSCRIBER = 0x1
    PUBLISHER  = 0x2


    def __init__(self, profile):
        self.profile  = profile
        self.factor   = 2
        self.maxDelay = 2*3600
        # Packet Id generator
        self.id       = 0
        self.queuePublishTx    = {} # PUBLISH messages waiting before being transmitted
        self.windowPublish     = {} # PUBLISH messages window waiting for PUBREC/PUBACK
        self.windowPubRelease  = {} # PUBREL  messages (qos=2) window waiting for PUBCOMP (publisher)
        self.windowPubRx       = {} # PUBLISH messages (qos=2) window waiting for PUBREL (subscriber side)
        self.windowSubscribe   = {} # SUBSCRIBE messages window, waiting fr SUBACK
        self.windowUnsubscribe = {} # UNSUBSCRIBE messages window, waiting fr UNSUBACK

        log.info("MQTT Client library version {version}", version=__version__)
    

    def buildProtocol(self, addr):
        if   self.profile == self.SUBSCRIBER:
            from mqtt.client.subscriber import MQTTProtocol
        elif self.profile == self.PUBLISHER:
            from mqtt.client.publisher import MQTTProtocol
        elif self.profile == (self.SUBSCRIBER | self.PUBLISHER):
            from mqtt.client.pubsubs import MQTTProtocol
        else:
            raise ProfileValueError("profile value not supported" , self.profile)
        
        v = self.queuePublishTx.get(addr, deque())
        self.queuePublishTx[addr] = v
        v = self.windowPublish.get(addr, dict() )
        self.windowPublish[addr] = v
        v = self.windowPubRelease.get(addr, dict() )
        self.windowPubRelease[addr] = v
        v = self.windowPubRx.get(addr, dict())
        self.windowPubRx[addr] = v
        v = self.windowSubscribe.get(addr, dict() )
        self.windowSubscribe[addr] = v
        v = self.windowUnsubscribe.get(addr, dict())
        self.windowUnsubscribe[addr] = v

        # Keeps a persistent reference to the last protocol built
        # This is ok *only* when connecting to a single broker. 
        self.protocol = MQTTProtocol(self, addr)
        return self.protocol


    def clientConnectionLost(self, connector, reason):
        log.warn('Lost connection. Reason {reason!r}:', reason=reason)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)


    def clientConnectionFailed(self, connector, reason):
        log.warn('Conenction failed. Reason {reason!r}:', reason=reason)
        ReconnectingClientFactory.clientConnectionFailed(self, connector,
                                                         reason)

    # -------------
    # Helper methods
    # --------------

    def makeId(self):
        '''Produce ids for Protocol packets, outliving their sessions'''
        self.id = (self.id + 1) % 65536
        self.id = self.id or 1   # avoid id 0
        return self.id


__all__ = [MQTTFactory]

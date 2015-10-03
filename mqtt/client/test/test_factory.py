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

from twisted.trial import unittest
from twisted.test import proto_helpers

from mqtt.client.factory    import MQTTFactory
from mqtt.client.subscriber import MQTTProtocol as MQTTSubscriberProtocol
from mqtt.client.publisher  import MQTTProtocol as MQTTPublisherProtocol
from mqtt.client.pubsubs    import MQTTProtocol as MQTTPubSubsProtocol


class PDUTestCase(unittest.TestCase):

    
    def test_buildProtocol_publisher(self):
        self.factory = MQTTFactory(MQTTFactory.PUBLISHER)
        p = self.factory.buildProtocol(0)
        self.assertIsInstance(p, MQTTPublisherProtocol)
        
    
    def test_buildProtocol_subscriber(self):
        self.factory = MQTTFactory(MQTTFactory.SUBSCRIBER)
        p = self.factory.buildProtocol(0)
        self.assertIsInstance(p, MQTTSubscriberProtocol)
        

    def test_buildProtocol_pubsubs(self):
        self.factory = MQTTFactory(MQTTFactory.SUBSCRIBER + 
            MQTTFactory.PUBLISHER)
        p = self.factory.buildProtocol(0)
        self.assertIsInstance(p, MQTTPubSubsProtocol)

    def test_buildProtocol_other(self):
        self.factory = MQTTFactory(0)
        self.assertRaises(ValueError, self.factory.buildProtocol, 0)

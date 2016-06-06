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

from twisted.trial    import unittest
from twisted.test     import proto_helpers
from twisted.internet import task, error
from twisted.python   import log


from mqtt import v31, v311
from mqtt.pdu import CONNACK, PINGREQ, PINGRES
from mqtt.client.factory    import MQTTFactory
from mqtt.client.subscriber import MQTTProtocol as MQTTSubscriberProtocol
from mqtt.client.publisher  import MQTTProtocol as MQTTPublisherProtocol
from mqtt.client.pubsubs    import MQTTProtocol as MQTTPubSubsProtocol

from mqtt.client.base       import MQTTBaseProtocol
from mqtt.error             import MQTTTimeoutError



class TestMQTTBaseProtocol1(unittest.TestCase):

    def setUp(self):
        self.transport = proto_helpers.StringTransportWithDisconnection()
        self.clock     = task.Clock()
        self.factory   = MQTTFactory(MQTTFactory.PUBLISHER)
        self.protocol  = MQTTBaseProtocol(self.factory)
        self.transport.protocol = self.protocol
        MQTTBaseProtocol.callLater = self.clock.callLater
        self.protocol.makeConnection(self.transport)
       

    def test_connect(self):
        self.CONNACK = CONNACK()
        self.CONNACK.session = False
        self.CONNACK.resultCode = 0
        self.CONNACK.encode()
        d = self.protocol.connect("TwistedMQTT-pub", keepalive=0, version=v31)
        self.transport.clear()
        self.assertEqual(self.protocol.state, self.protocol.CONNECTING)
        self.protocol.dataReceived(self.CONNACK.encoded)
        self.assertEqual(self.protocol.state, self.protocol.CONNECTED)
        self.assertEqual(self.CONNACK.session, self.successResultOf(d))
 

    def test_connect_timeout(self):
        d = self.protocol.connect("TwistedMQTT-pub", keepalive=0, version=v31)
        self.transport.clear()
        self.assertEqual(self.protocol.state, self.protocol.CONNECTING)
        self.assertNoResult(d)
        self.clock.advance(11)
        self.failureResultOf(d).trap(MQTTTimeoutError)

class TestMQTTBaseProtocol2(unittest.TestCase):

    def setUp(self):
        '''
        Set up a conencted state
        '''
        self.transport = proto_helpers.StringTransportWithDisconnection()
        self.clock     = task.Clock()
        MQTTBaseProtocol.callLater = self.clock.callLater
        self.factory   = MQTTFactory(MQTTFactory.SUBSCRIBER)
        self._rebuild()
      
    def tearDown(self):
        '''
        Needed because ping sets up a LoopingCall, outside Clock simulated callLater()
        '''
        self.transport.loseConnection()

    def _connect(self, keepalive=0, cleanStart=True):
        '''
        Go to connected state
        '''
        ack = CONNACK()
        ack.session = False
        ack.resultCode = 0
        ack.encode()
        self.protocol.connect("TwistedMQTT-sub", keepalive=keepalive, cleanStart=cleanStart, version=v31)
        self.transport.clear()
        self.protocol.dataReceived(ack.encoded)

    def _rebuild(self):
        self.protocol  = self.factory.buildProtocol(0)
        self.transport.protocol = self.protocol
        self.protocol.makeConnection(self.transport)


    def test_disconnect(self):
        self._connect()
        self.assertEqual(self.protocol.state, self.protocol.CONNECTED)
        self.protocol.disconnect()
        self.transport.clear()

    def test_ping(self):
        self._connect(keepalive=5)
        self.protocol.dataReceived(PINGRES().encode())
        self.transport.clear()
        self.assertEqual(self.protocol.state, self.protocol.CONNECTED)
      
    def test_ping_timeout(self):
        self._connect(keepalive=5)
        self.protocol.ping()
        self.transport.clear()
        self.clock.advance(6)
        self.assertEqual(self.protocol.state, self.protocol.IDLE)
        
class TestMQTTBaseExceptions(unittest.TestCase):

    def setUp(self):
        self.transport = proto_helpers.StringTransportWithDisconnection()
        self.clock     = task.Clock()
        self.factory   = MQTTFactory(MQTTFactory.PUBLISHER)
        self.protocol  = MQTTBaseProtocol(self.factory)
        self.transport.protocol = self.protocol
        MQTTBaseProtocol.callLater = self.clock.callLater
        self.protocol.makeConnection(self.transport)
       

    def test_connect_version(self):
        clientId="1234567890ABCDEFGHIJ1234567890"
        d = self.protocol.connect(clientId, keepalive=0, version=0)
        self.failureResultOf(d).trap(ValueError)
        self.assertEqual(self.protocol.state, self.protocol.IDLE)

    def test_connect_client_id_v31(self):
        clientId="1234567890ABCDEFGHIJ1234567890"
        d = self.protocol.connect(clientId, keepalive=0, version=v31)
        self.failureResultOf(d).trap(ValueError)
        self.assertEqual(self.protocol.state, self.protocol.IDLE)

    def test_connect_client_id_v311(self):
        clientId="1234567890ABCDEFGHIJ1234567890"*3000
        d = self.protocol.connect(clientId, keepalive=0, version=v311)
        self.failureResultOf(d).trap(ValueError)
        self.assertEqual(self.protocol.state, self.protocol.IDLE)

    def test_connect_keepalive_negative(self):
        clientId="1234567890A"
        d = self.protocol.connect(clientId, keepalive=-1, version=v31)
        self.failureResultOf(d).trap(ValueError)
        self.assertEqual(self.protocol.state, self.protocol.IDLE)

    def test_connect_keepalive_large(self):
        clientId="1234567890A"
        d = self.protocol.connect(clientId, keepalive=65537, version=v31)
        self.failureResultOf(d).trap(ValueError)
        self.assertEqual(self.protocol.state, self.protocol.IDLE)

    def test_connect_will_qos_large(self):
        clientId="1234567890A"
        d = self.protocol.connect(clientId, keepalive=0, version=v31, willQoS=5)
        self.failureResultOf(d).trap(ValueError)
        self.assertEqual(self.protocol.state, self.protocol.IDLE)

    def test_connect_will_qos_negative(self):
        clientId="1234567890A"
        d = self.protocol.connect(clientId, keepalive=0, version=v31, willQoS=-1)
        self.failureResultOf(d).trap(ValueError)
        self.assertEqual(self.protocol.state, self.protocol.IDLE)

    def test_connect_no_username_with_password(self):
        clientId="1234567890A"
        d = self.protocol.connect(clientId, keepalive=0, version=v31, password="foo")
        self.failureResultOf(d).trap(ValueError)
        self.assertEqual(self.protocol.state, self.protocol.IDLE)
    
    def test_connect_will_topic_no_message(self):
        clientId="1234567890A"
        d = self.protocol.connect(clientId, keepalive=0, version=v31, willTopic="foo/bar")
        self.failureResultOf(d).trap(ValueError)
        self.assertEqual(self.protocol.state, self.protocol.IDLE)

    def test_connect_will_message_no_topic(self):
        clientId="1234567890A"
        d = self.protocol.connect(clientId, keepalive=0, version=v31, willMessage="Hello")
        self.failureResultOf(d).trap(ValueError)
        self.assertEqual(self.protocol.state, self.protocol.IDLE)
    
    def test_window_size_large(self):
        self.assertRaises(ValueError, self.protocol.setWindowSize, 32)

    def test_window_size_negative(self):
        self.assertRaises(ValueError, self.protocol.setWindowSize, -1)

    def test_timeout_large(self):
        self.assertRaises(ValueError, self.protocol.setTimeout, 65536)

    def test_timeout_negative(self):
        self.assertRaises(ValueError, self.protocol.setTimeout, -1)
   
       
 
        
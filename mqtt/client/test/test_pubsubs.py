# ----------------------------------------------------------------------
# Copyright (C) 2015 by Rafael Gonzalez 
# #
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#----------------------------------------------------------------------

from twisted.trial    import unittest
from twisted.test     import proto_helpers
from twisted.internet import task, defer, error


from mqtt                   import v31
from mqtt.error             import MQTTWindowError
from mqtt.pdu               import CONNACK, PUBACK, PUBREC, PUBREL, PUBCOMP
from mqtt.client.base       import MQTTBaseProtocol
from mqtt.client.factory    import MQTTFactory
from mqtt.client.subscriber import MQTTProtocol as MQTTSubscriberProtocol
from mqtt.client.publisher  import MQTTProtocol as MQTTPublisherProtocol
from mqtt.client.pubsubs    import MQTTProtocol as MQTTPubSubsProtocol




class TestMQTTPublisherDisconnect(unittest.TestCase):
    '''
    Testing various cases of disconnect callback
    '''

    def setUp(self):
        '''
        Set up a connencted state
        '''
        self.transport = proto_helpers.StringTransportWithDisconnection()
        self.clock     = task.Clock()
        MQTTBaseProtocol.callLater = self.clock.callLater
        self.factory   = MQTTFactory(MQTTFactory.PUBLISHER | MQTTFactory.SUBSCRIBER)
        self._rebuild()
        self.disconnected = 0

    def _connect(self, cleanStart=True):
        '''
        Go to connected state
        '''
        ack = CONNACK()
        ack.session = False
        ack.resultCode = 0
        ack.encode()
        self.protocol.connect("TwistedMQTT-pubsubs", keepalive=0, cleanStart=cleanStart, version=v31)
        self.transport.clear()
        self.protocol.dataReceived(ack.encoded)

    def _disconnected(self, reason):
        self.disconnected += 1

    def _serverDown(self):
        self.transport.loseConnection()
        self.transport.clear()
        del self.protocol

    def _rebuild(self):
        self.protocol  = self.factory.buildProtocol(0)
        self.transport.protocol = self.protocol
        MQTTBaseProtocol.callLater = self.clock.callLater
        self.protocol.makeConnection(self.transport)

    def test_disconnect_1(self):
        '''Just connect and lose the transport'''
        self._connect()
        self.protocol.onDisconnection = self._disconnected
        self.transport.loseConnection()
        self.assertEqual(self.disconnected, 1)
        

    def test_disconnect_2(self):
        '''connect and disconnect'''
        self._connect()
        self.protocol.onDisconnection = self._disconnected
        self.protocol.disconnect()
        self.assertEqual(self.disconnected, 1)
        

    def test_disconnect_3(self):
        '''connect, generate a deferred and lose the transport'''
        self._connect()
        self.protocol.onDisconnection = self._disconnected
        d = self.protocol.publish(topic="foo/bar/baz1", qos=1, message="hello world 1")
        self.transport.clear()
        self.transport.loseConnection()
        self.assertEqual(self.disconnected, 1)
        self.failureResultOf(d).trap(error.ConnectionDone)
       

    def test_disconnect_4(self):
        '''connect, generate a deferred and disconnect'''
        self._connect()
        self.protocol.onDisconnection = self._disconnected
        d = self.protocol.publish(topic="foo/bar/baz1", qos=1, message="hello world 1")
        self.transport.clear()
        self.protocol.disconnect()
        self.assertEqual(self.disconnected, 1)
        self.failureResultOf(d).trap(error.ConnectionDone)
       

    def test_disconnect_5(self):
        '''connect with persistent session, generate a deferred and disconnect'''
        self._connect(cleanStart=False)
        self.protocol.onDisconnection = self._disconnected
        d = self.protocol.publish(topic="foo/bar/baz1", qos=1, message="hello world 1")
        self.transport.clear()
        self.protocol.disconnect()
        self.assertEqual(self.disconnected, 1)
        self.assertNoResult(d)
       

    def test_disconnect_6(self):
        '''connect with persistent session, generate a deferred , rebuilds protocol'''
        self._connect(cleanStart=False)
        self.protocol.onDisconnection = self._disconnected
        d = self.protocol.publish(topic="foo/bar/baz1", qos=1, message="hello world 1")
        self._serverDown()
        self._rebuild()
        self.assertEqual(self.disconnected, 1)
        self.assertNoResult(d)
       


class TestMQTTSubscriberDisconnect(unittest.TestCase):
    '''
    Testing various cases of disconnect callback
    '''

    def setUp(self):
        '''
        Set up a connencted state
        '''
        self.transport = proto_helpers.StringTransportWithDisconnection()
        self.clock     = task.Clock()
        MQTTBaseProtocol.callLater = self.clock.callLater
        self.factory   = MQTTFactory(MQTTFactory.PUBLISHER | MQTTFactory.SUBSCRIBER)
        self._rebuild()
        self.disconnected = 0

    def _connect(self, cleanStart=True):
        '''
        Go to connected state
        '''
        ack = CONNACK()
        ack.session = False
        ack.resultCode = 0
        ack.encode()
        self.protocol.connect("TwistedMQTT-sub", keepalive=0, cleanStart=cleanStart, version=v31)
        self.transport.clear()
        self.protocol.dataReceived(ack.encoded)

    def _disconnected(self, reason):
        self.disconnected += 1

    def _rebuild(self):
        self.protocol  = self.factory.buildProtocol(0)
        self.transport.protocol = self.protocol
        MQTTBaseProtocol.callLater = self.clock.callLater
        self.protocol.makeConnection(self.transport)

    def _serverDown(self):
        self.transport.loseConnection()
        self.transport.clear()
        del self.protocol

    def test_disconnect_1(self):
        '''Just connect and lose the transport'''
        self._connect()
        self.protocol.onDisconnection = self._disconnected
        self.transport.loseConnection()
        self.assertEqual(self.disconnected, 1)
       

    def test_disconnect_2(self):
        '''connect and disconnect'''
        self._connect()
        self.protocol.onDisconnection = self._disconnected
        self.protocol.disconnect()
        self.assertEqual(self.disconnected, 1)
       

    def test_disconnect_3(self):
        '''connect, generate a deferred and lose the transport'''
        self._connect()
        self.protocol.onDisconnection = self._disconnected
        d = self.protocol.subscribe("foo/bar/baz1", 2 )
        self.transport.clear()
        self.transport.loseConnection()
        self.assertEqual(self.disconnected, 1)
        self.failureResultOf(d).trap(error.ConnectionDone)

    def test_disconnect_4(self):
        '''connect, generate a deferred and disconnect'''
        self._connect()
        self.protocol.onDisconnection = self._disconnected
        d = self.protocol.subscribe("foo/bar/baz1", 2 )
        self.transport.clear()
        self.protocol.disconnect()
        self.assertEqual(self.disconnected, 1)
        self.failureResultOf(d).trap(error.ConnectionDone)

    def test_disconnect_5(self):
        '''connect with persistent session, 
        enerate a deferred that will not errback 
        and then disconnect'''
        self._connect(cleanStart=False)
        self.protocol.onDisconnection = self._disconnected
        d = self.protocol.subscribe("foo/bar/baz1", 2 )
        self.transport.clear()
        self.protocol.disconnect()
        self.assertEqual(self.disconnected, 1)
        self.assertNoResult(d)

    def test_disconnect_6(self):
        '''connect with persistent session, 
        generate a deferred that will not errback yet, 
        then rebuilds protocol'''
        self._connect(cleanStart=False)
        self.protocol.onDisconnection = self._disconnected
        d = self.protocol.subscribe("foo/bar/baz1", 2 )
        self._serverDown()
        self._rebuild()
        self.assertEqual(self.disconnected, 1)
        self.assertNoResult(d)



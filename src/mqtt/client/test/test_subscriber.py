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
from twisted.internet import task, defer, error

from twisted.internet.address import IPv4Address


from mqtt                   import v31
from mqtt.error             import MQTTWindowError
from mqtt.pdu               import CONNACK, SUBSCRIBE, SUBACK, UNSUBACK, PUBLISH, PUBREL
from mqtt.client.factory    import MQTTFactory
from mqtt.client.base       import MQTTBaseProtocol
from mqtt.client.subscriber import MQTTProtocol as MQTTSubscriberProtocol
from mqtt.client.publisher  import MQTTProtocol as MQTTPublisherProtocol
from mqtt.client.pubsubs    import MQTTProtocol as MQTTPubSubsProtocol




class TestMQTTSubscriber1(unittest.TestCase):


    def setUp(self):
        '''
        Set up a conencted state
        '''
        self.transport = proto_helpers.StringTransportWithDisconnection()
        self.clock     = task.Clock()
        MQTTBaseProtocol.callLater = self.clock.callLater
        self.factory   = MQTTFactory(MQTTFactory.SUBSCRIBER)
        self.addr = IPv4Address('TCP','localhost',1880)
        self._rebuild()
        self._connect()

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


    def _serverDown(self):
        self.transport.loseConnection()
        self.transport.clear()
        del self.protocol

    def _rebuild(self):
        self.protocol  = self.factory.buildProtocol(self.addr)
        self.transport.protocol = self.protocol
        MQTTBaseProtocol.callLater = self.clock.callLater
        self.protocol.makeConnection(self.transport)


    def _subscribe(self, n, qos, topic):
        self.protocol.setWindowSize(n)
        dl = []
        for i in range(0,n):
            t = "{0}{1}".format(topic, i)
            dl.append(self.protocol.subscribe(t, qos))
        self.transport.clear()
        for d in dl:
            self.assertNoResult(d)
        return dl

    def _unsubscribe(self, n, topic):
        self.protocol.setWindowSize(n)
        dl = []
        for i in range(0,n):
            t = "{0}{1}".format(topic, i)
            dl.append(self.protocol.unsubscribe(t))
        self.transport.clear()
        for d in dl:
            self.assertNoResult(d)
        return dl

    def test_subscribe_single(self):
        d = self.protocol.subscribe("foo/bar/baz1", 2 )
        self.transport.clear()
        ack = SUBACK()
        ack.msgId = d.msgId
        ack.granted = [(2, False)]
        self.protocol.dataReceived(ack.encode())
        self.assertEqual([(2, False)], self.successResultOf(d))

    def test_subscribe_single_large_qos(self):
        d = self.protocol.subscribe("foo/bar/baz1", 3)
        self.transport.clear()
        self.failureResultOf(d).trap(ValueError)

    def test_subscribe_single_negative_qos(self):
        d = self.protocol.subscribe("foo/bar/baz1", -1)
        self.transport.clear()
        self.failureResultOf(d).trap(ValueError)

    def test_subscribe_tuple(self):
        d = self.protocol.subscribe( ("foo/bar/baz1", 2) )
        self.transport.clear()
        ack = SUBACK()
        ack.msgId = d.msgId
        ack.granted = [(2, False)]
        self.protocol.dataReceived(ack.encode())
        self.assertEqual([(2, False)], self.successResultOf(d))

    def test_subscribe_list(self):
        d = self.protocol.subscribe( [ ("foo/bar/baz1", 2), ("foo/bar/baz2", 1), ("foo/bar/baz3", 0) ] )
        d.addCallback(self.assertEqual, [(2, False), (1, False), (0, False)] )
        self.transport.clear()
        ack = SUBACK()
        ack.msgId = d.msgId
        ack.granted = [(2, False), (1, False), (0, False)]
        self.protocol.dataReceived(ack.encode())
        self.assertEqual( [(2, False), (1, False), (0, False)], self.successResultOf(d))

    def test_subscribe_several_fail(self):
        dl = self._subscribe(n=3, qos=2, topic="foo/bar/baz")
        self.assertEqual(len(self.protocol.factory.windowSubscribe[self.addr]), 3)
        self._serverDown()
        for d in dl:
            self.failureResultOf(d).trap(error.ConnectionDone)
        

    def test_subscribe_several_window_fail(self):
        self.protocol.setWindowSize(3)
        dl = self._subscribe(n=3, qos=2, topic="foo/bar/baz")
        self.assertEqual(len(self.protocol.factory.windowSubscribe[self.addr]), 3)
        d4 = self.protocol.subscribe("foo/bar/baz3", 2 )
        self.assertEqual(len(self.protocol.factory.windowSubscribe[self.addr]), 3)
        self.failureResultOf(d4).trap(MQTTWindowError)
        self._serverDown()
        for d in dl:
            self.failureResultOf(d).trap(error.ConnectionDone)
        

    def test_unsubscribe_single(self):
        d = self.protocol.unsubscribe("foo/bar/baz1")
        self.transport.clear()
        ack = UNSUBACK()
        ack.msgId = d.msgId
        self.protocol.dataReceived(ack.encode())
        self.assertEqual(ack.msgId, self.successResultOf(d))


    def test_unsubscribe_list(self):
        d = self.protocol.unsubscribe( [ "foo/bar/baz1", "foo/bar/baz2", "foo/bar/baz3"] )
        self.transport.clear()
        ack = UNSUBACK()
        ack.msgId = d.msgId
        self.protocol.dataReceived(ack.encode())
        self.assertEqual(ack.msgId, self.successResultOf(d))

    def test_unsubscribe_several_fail(self):
        dl = self._unsubscribe(n=3, topic="foo/bar/baz")
        self.assertEqual(len(self.protocol.factory.windowUnsubscribe[self.addr]), 3)
        self._serverDown()
        for d in dl:
            self.failureResultOf(d).trap(error.ConnectionDone)

    def test_unsubscribe_several_window_fail(self):
        dl = self._unsubscribe(n=3, topic="foo/bar/baz")
        self.assertEqual(len(self.protocol.factory.windowUnsubscribe[self.addr]), 3)
        d4 = self.protocol.unsubscribe("foo/bar/baz4")
        self.assertEqual(len(self.protocol.factory.windowUnsubscribe[self.addr]), 3)
        self.failureResultOf(d4).trap(MQTTWindowError)
        self._serverDown()
        for d in dl:
            self.failureResultOf(d).trap(error.ConnectionDone)

    def test_publish_recv_qos0(self):
        def onPublish(topic, payload, qos, dup, retain, msgId):
            self.topic   = topic
            self.payload = payload.decode('utf-8')
            self.qos     = qos
            self.retain  = retain
            self.msgId   = msgId 
        self.protocol.onPublish = onPublish
        pub =PUBLISH()
        pub.qos     = 0
        pub.dup     = False
        pub.retain  = False
        pub.topic   = "foo/bar/baz0"
        pub.msgId   = None
        pub.payload = "Hello world 0"
        self.protocol.dataReceived(pub.encode())
        self.assertEqual(self.topic,   pub.topic)
        self.assertEqual(self.payload, pub.payload)
        self.assertEqual(self.qos,     pub.qos)
        self.assertEqual(self.retain,  pub.retain)
        self.assertEqual(self.msgId,   pub.msgId )

    def test_publish_recv_qos1(self):
        def onPublish(topic, payload, qos, dup, retain, msgId):
            self.topic   = topic
            self.payload = payload.decode('utf-8')
            self.qos     = qos
            self.retain  = retain
            self.msgId   = msgId 
            self.dup     = dup
        self.protocol.onPublish = onPublish
        pub =PUBLISH()
        pub.qos     = 1
        pub.dup     = False
        pub.retain  = False
        pub.topic   = "foo/bar/baz1"
        pub.msgId   = 1
        pub.payload = "Hello world 1"
        self.protocol.dataReceived(pub.encode())
        self.transport.clear()
        self.assertEqual(self.topic,   pub.topic)
        self.assertEqual(self.payload, pub.payload)
        self.assertEqual(self.qos,     pub.qos)
        self.assertEqual(self.retain,  pub.retain)
        self.assertEqual(self.msgId,   pub.msgId )
        self.assertEqual(self.dup,     pub.dup )

    def test_publish_recv_qos2(self):
        self.called = False
        def onPublish(topic, payload, qos, dup, retain, msgId):
            self.called = True
            self.topic   = topic
            self.payload = payload.decode('utf-8')
            self.qos     = qos
            self.retain  = retain
            self.msgId   = msgId 
            self.dup     = dup
        self.protocol.onPublish = onPublish
        pub =PUBLISH()
        pub.qos     = 2
        pub.dup     = False
        pub.retain  = False
        pub.topic   = "foo/bar/baz2"
        pub.msgId   = 1
        pub.payload = "Hello world 2"
        self.protocol.dataReceived(pub.encode())
        self.transport.clear()
        self.assertEqual(self.called, False)
        rel = PUBREL()
        rel.msgId = pub.msgId
        self.protocol.dataReceived(rel.encode())
        self.assertEqual(self.topic,   pub.topic)
        self.assertEqual(self.payload, pub.payload)
        self.assertEqual(self.qos,     pub.qos)
        self.assertEqual(self.retain,  pub.retain)
        self.assertEqual(self.msgId,   pub.msgId )
        self.assertEqual(self.dup,     pub.dup )


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
        self.factory   = MQTTFactory(MQTTFactory.SUBSCRIBER)
        self._rebuild()
        self.disconnected = False

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
        self.disconnected = True

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
        self.assertEqual(self.disconnected, True)

    def test_disconnect_2(self):
        '''connect and disconnect'''
        self._connect()
        self.protocol.onDisconnection = self._disconnected
        self.protocol.disconnect()
        self.assertEqual(self.disconnected, True)

    def test_disconnect_3(self):
        '''connect, generate a deferred and lose the transport'''
        self._connect()
        self.protocol.onDisconnection = self._disconnected
        d = self.protocol.subscribe("foo/bar/baz1", 2 )
        self.transport.clear()
        self.transport.loseConnection()
        self.assertEqual(self.disconnected, True)
        self.failureResultOf(d).trap(error.ConnectionDone)

    def test_disconnect_4(self):
        '''connect, generate a deferred and disconnect'''
        self._connect()
        self.protocol.onDisconnection = self._disconnected
        d = self.protocol.subscribe("foo/bar/baz1", 2 )
        self.transport.clear()
        self.protocol.disconnect()
        self.assertEqual(self.disconnected, True)
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
        self.assertEqual(self.disconnected, True)
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
        self.assertEqual(self.disconnected, True)
        self.assertNoResult(d)


class TestMQTTSubscriber2(unittest.TestCase):


    def setUp(self):
        '''
        Set up a conencted state
        '''
        self.transport = proto_helpers.StringTransportWithDisconnection()
        self.clock     = task.Clock()
        MQTTBaseProtocol.callLater = self.clock.callLater
        self.factory   = MQTTFactory(MQTTFactory.SUBSCRIBER)
        self._rebuild()
       
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


    def _serverDown(self):
        self.transport.loseConnection()
        self.transport.clear()
        del self.protocol

    def _rebuild(self):
        self.protocol  = self.factory.buildProtocol(0)
        self.transport.protocol = self.protocol
        MQTTBaseProtocol.callLater = self.clock.callLater
        self.protocol.makeConnection(self.transport)


    def _subscribe(self, n, qos, topic):
        self.protocol.setWindowSize(n)
        dl = []
        for i in range(0,n):
            t = "{0}{1}".format(topic, i)
            dl.append(self.protocol.subscribe(t, qos))
        self.transport.clear()
        for d in dl:
            self.assertNoResult(d)
        return dl

    def _unsubscribe(self, n, topic):
        self.protocol.setWindowSize(n)
        dl = []
        for i in range(0,n):
            t = "{0}{1}".format(topic, i)
            dl.append(self.protocol.unsubscribe(t))
        self.transport.clear()
        for d in dl:
            self.assertNoResult(d)
        return dl

    def test_subscribe_setPubishHandler1(self):
        def onPublish(topic, payload, qos, dup, retain, msgId):
            self.called  = True
        self.protocol.onPublish = onPublish
        self._connect()
        d = self.protocol.subscribe("foo/bar/baz1", 2 )
        self.transport.clear()
        ack = SUBACK()
        ack.msgId = d.msgId
        ack.granted = [(2, False)]
        self.protocol.dataReceived(ack.encode())
        self.assertEqual([(2, False)], self.successResultOf(d))

    def test_subscribe_setPubishHandler2(self):
        def onPublish(topic, payload, qos, dup, retain, msgId):
            self.called  = True
        self._connect()
        self.protocol.onPublish = onPublish
        d = self.protocol.subscribe("foo/bar/baz1", 2 )
        self.transport.clear()
        ack = SUBACK()
        ack.msgId = d.msgId
        ack.granted = [(2, False)]
        self.protocol.dataReceived(ack.encode())
        self.assertEqual([(2, False)], self.successResultOf(d))
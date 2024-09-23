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
from twisted.python   import log


from mqtt                   import v31
from mqtt.error             import MQTTWindowError
from mqtt.pdu               import CONNACK, PUBACK, PUBREC, PUBREL, PUBCOMP
from mqtt.client.base       import MQTTBaseProtocol, MQTTStateError
from mqtt.client.factory    import MQTTFactory
from mqtt.client.subscriber import MQTTProtocol as MQTTSubscriberProtocol
from mqtt.client.publisher  import MQTTProtocol as MQTTPublisherProtocol
from mqtt.client.pubsubs    import MQTTProtocol as MQTTPubSubsProtocol

from twisted.internet.address import IPv4Address



class TestMQTTPublisher1(unittest.TestCase):


    def setUp(self):
        '''
        Set up a conencted state
        '''
        self.transport = proto_helpers.StringTransportWithDisconnection()
        self.clock     = task.Clock()
        MQTTBaseProtocol.callLater = self.clock.callLater
        self.factory   = MQTTFactory(MQTTFactory.PUBLISHER)
        self._rebuild()
        # Just to generate connection contexts
        

    def _connect(self, cleanStart=True):
        '''
        Go to connected state
        '''
        ack = CONNACK()
        ack.session = False
        ack.resultCode = 0
        ack.encode()
        self.protocol.connect("TwistedMQTT-pub", keepalive=0, cleanStart=cleanStart, version=v31)
        self.transport.clear()
        self.protocol.dataReceived(ack.encoded)


    def _serverDown(self):
        self.transport.loseConnection()
        self.transport.clear()
        del self.protocol

    def _rebuild(self):
        self.addr = IPv4Address('TCP','localhost',1880)
        self.protocol  = self.factory.buildProtocol(self.addr)
        self.transport.protocol = self.protocol
        MQTTBaseProtocol.callLater = self.clock.callLater
        self.protocol.makeConnection(self.transport)


    def _publish(self, n, qos, topic, msg, window=None):
        if window is None:
            self.protocol.setWindowSize(n)
        else:
            self.protocol.setWindowSize(window)
        dl = []
        for i in range(0,n):
            dl.append(self.protocol.publish(topic=topic, qos=qos, message=msg))
        self.transport.clear()
        for d in dl:
            if qos == 0:
                self.assertEqual(None, self.successResultOf(d))
            else:
                self.assertNoResult(d)
        return dl
    
    def _puback(self, dl):
        ackl = []
        for i in range(0, len(dl)):
            ack= PUBACK()
            ack.msgId = dl[i].msgId
            ackl.append(ack)
        encoded = bytearray()
        for ack in ackl:
            encoded.extend(ack.encode())
        self.protocol.dataReceived(encoded)
        self.transport.clear()
        for i in range(0, len(dl)):
            self.assertEqual(dl[i].msgId, self.successResultOf(dl[i]))

    def _pubrec(self, dl):
        recl = []
        for i in range(0, len(dl)):
            rec= PUBREC()
            rec.msgId = dl[i].msgId
            recl.append(rec)
        encoded = bytearray()
        for rec in recl:
            encoded.extend(rec.encode())
        self.protocol.dataReceived(encoded)
        self.transport.clear()
        for i in range(0, len(dl)):
            self.assertNoResult(dl[i])


    def _pubcomp(self, dl):
        compl = []
        for i in range(0, len(dl)):
            comp= PUBCOMP()
            comp.msgId = dl[i].msgId
            compl.append(comp)
        encoded = bytearray()
        for comp in compl:
            encoded.extend(comp.encode())
        self.protocol.dataReceived(encoded)
        self.transport.clear()
        for i in range(0, len(dl)):
            self.assertEqual(dl[i].msgId, self.successResultOf(dl[i]))



    def test_publish_single_qos0(self):
        self._connect()
        d = self.protocol.publish(topic="foo/bar/baz1", qos=0, message="hello world 0")
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  0)
        self.assertEqual(None, self.successResultOf(d))

    def test_publish_single_qos1(self):
        self._connect()
        d = self.protocol.publish(topic="foo/bar/baz1", qos=1, message="hello world 1")
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  1)
        self.transport.clear()
        ack = PUBACK()
        ack.msgId = d.msgId
        self.protocol.dataReceived(ack.encode())
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  0)
        self.assertEqual(ack.msgId, self.successResultOf(d))

    def test_publish_single_qos2(self):
        self._connect()
        d = self.protocol.publish(topic="foo/bar/baz1", qos=2, message="hello world 2")
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  1)
        self.assertEqual(len(self.protocol.factory.windowPubRelease[self.addr]), 0)
        self.transport.clear()
        ack = PUBREC()
        ack.msgId = d.msgId
        self.protocol.dataReceived(ack.encode())
        self.transport.clear()
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  0)
        self.assertEqual(len(self.protocol.factory.windowPubRelease[self.addr]), 1)
        ack = PUBCOMP()
        ack.msgId = d.msgId
        self.protocol.dataReceived(ack.encode())
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  0)
        self.assertEqual(len(self.protocol.factory.windowPubRelease[self.addr]), 0)
        self.assertEqual(ack.msgId, self.successResultOf(d))

    def test_publish_several_qos0(self):
        self._connect()
        dl = self._publish(n=3, qos=0, topic="foo/bar/baz", msg="Hello World")
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  0)
        

    def test_publish_several_qos1(self):
        self._connect()
        dl = self._publish(n=3, qos=1, topic="foo/bar/baz", msg="Hello World")
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  len(dl))
        self._puback(dl)
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  0)
        

    def test_publish_several_qos2(self):
        self._connect()
        dl = self._publish(n=3, qos=2, topic="foo/bar/baz", msg="Hello World")
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  len(dl))
        self.assertEqual(len(self.protocol.factory.windowPubRelease[self.addr]), 0)
        self._pubrec(dl)
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  0)
        self.assertEqual(len(self.protocol.factory.windowPubRelease[self.addr]), len(dl))
        self._pubcomp(dl)
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  0)
        self.assertEqual(len(self.protocol.factory.windowPubRelease[self.addr]), 0)


    def test_publish_many_qos1(self):
        '''
        Test enqueuing when not all ACKs arrives
        '''
        self._connect()
        window = 3
        n = 7
        dl = self._publish(n=n, window=window, qos=1, topic="foo/bar/baz", msg="Hello World")
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  window)
        self.assertEqual(len(self.protocol.factory.queuePublishTx[self.addr]), n-window)
        self._puback(dl[0:window])
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  window)
        self.assertEqual(len(self.protocol.factory.queuePublishTx[self.addr]), 1)
        self._puback(dl[window:2*window])
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  1)
        self.assertEqual(len(self.protocol.factory.queuePublishTx[self.addr]), 0)
        self._puback(dl[2*window:])
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  0)
        self.assertEqual(len(self.protocol.factory.queuePublishTx[self.addr]), 0)

    def test_publish_many_qos2(self):
        '''
        Test enqueuing when not all ACKs arrives
        '''
        self._connect()
        window = 3
        n = 7
        dl = self._publish(n=n, window=window, qos=2, topic="foo/bar/baz", msg="Hello World")
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  window)
        self.assertEqual(len(self.protocol.factory.queuePublishTx[self.addr]), n-window)
        self._pubrec(dl[0:window])
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  0)
        self.assertEqual(len(self.protocol.factory.windowPubRelease[self.addr]), window)
        self._pubcomp(dl[0:window])
        self.assertEqual(len(self.protocol.factory.queuePublishTx[self.addr]), n-2*window)
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  window)
        self.assertEqual(len(self.protocol.factory.windowPubRelease[self.addr]), 0)



    def test_lost_session(self):
        self._connect()
        dl = self._publish(n=3, qos=2, topic="foo/bar/baz", msg="Hello World")
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  len(dl))
        self.assertEqual(len(self.protocol.factory.windowPubRelease[self.addr]), 0)
        self._serverDown()
        self.assertEqual(len(self.factory.windowPublish[self.addr]),  0)
        self.assertEqual(len(self.factory.windowPubRelease[self.addr]), 0)
        for d in dl:
            self.failureResultOf(d).trap(error.ConnectionDone)
       

    def test_persistent_session_qos1(self):
        self._connect(cleanStart=False)
        dl = self._publish(n=3, qos=1, topic="foo/bar/baz", msg="Hello World")
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  len(dl))
        self._serverDown()
        self.assertEqual(len(self.factory.windowPublish[self.addr]),  len(dl))
        for d in dl:
            self.assertNoResult(d)
        self._rebuild()
        self._connect(cleanStart=False)
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  len(dl))
        self._puback(dl)
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  0)


    def test_persistent_session_qos2(self):
        self._connect(cleanStart=False)
        dl = self._publish(n=3, qos=2, topic="foo/bar/baz", msg="Hello World")
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  len(dl))
        self.assertEqual(len(self.protocol.factory.windowPubRelease[self.addr]), 0)
        self._serverDown()
        for d in dl:
            self.assertNoResult(d)
        self._rebuild()
        self._connect(cleanStart=False)
        self.assertEqual(len(self.factory.windowPublish[self.addr]),  len(dl))
        self.assertEqual(len(self.protocol.factory.windowPubRelease[self.addr]), 0)
        self._pubrec(dl)
        self.assertEqual(len(self.factory.windowPublish[self.addr]), 0 )
        self.assertEqual(len(self.protocol.factory.windowPubRelease[self.addr]), len(dl))
        self._pubcomp(dl)
        self.assertEqual(len(self.factory.windowPublish[self.addr]),  0)
        self.assertEqual(len(self.protocol.factory.windowPubRelease[self.addr]), 0)



    def test_persistent_release_qos2(self):
        self._connect(cleanStart=False)
        dl = self._publish(n=3, qos=2, topic="foo/bar/baz", msg="Hello World")
        #- generate two ACK and simulate a server disconnect with a new client protocol
        # being built on the client 
        self._pubrec(dl[:-1])   # Only the first two

        self._serverDown()
        self.assertNoResult(dl[0])
        self.assertNoResult(dl[1])
        self.assertNoResult(dl[2])
        self._rebuild()
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]),  1)
        self.assertEqual(len(self.protocol.factory.windowPubRelease[self.addr]),  2)
        # Reconnect with the new client protcol object
        self._connect(cleanStart=False)
        self._pubrec(dl[-1:])   # send the last one
        self.assertEqual(len(self.protocol.factory.windowPublish[self.addr]), 0)
        self.assertEqual(len(self.protocol.factory.windowPubRelease[self.addr]), 3)
        self._pubcomp(dl[0:1])   # send the first comp
        self.assertEqual(len(self.factory.windowPublish[self.addr]),  0)
        self.assertEqual(len(self.protocol.factory.windowPubRelease[self.addr]), 2)
        self._pubcomp(dl[1:2])   # send the second comp
        self.assertEqual(len(self.factory.windowPublish[self.addr]),  0)
        self.assertEqual(len(self.protocol.factory.windowPubRelease[self.addr]), 1)
        self._pubcomp(dl[-1:])   # send the last comp
        self.assertEqual(len(self.factory.windowPublish[self.addr]),  0)
        self.assertEqual(len(self.protocol.factory.windowPubRelease[self.addr]), 0)


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
        self.factory   = MQTTFactory(MQTTFactory.PUBLISHER)
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
        self.protocol.connect("TwistedMQTT-pub", keepalive=0, cleanStart=cleanStart, version=v31)
        self.transport.clear()
        self.protocol.dataReceived(ack.encoded)

    def _disconnected(self, reason):
        self.disconnected = True

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
        d = self.protocol.publish(topic="foo/bar/baz1", qos=1, message="hello world 1")
        self.transport.clear()
        self.transport.loseConnection()
        self.assertEqual(self.disconnected, True)
        self.failureResultOf(d).trap(error.ConnectionDone)

    def test_disconnect_4(self):
        '''connect, generate a deferred and disconnect'''
        self._connect()
        self.protocol.onDisconnection = self._disconnected
        d = self.protocol.publish(topic="foo/bar/baz1", qos=1, message="hello world 1")
        self.transport.clear()
        self.protocol.disconnect()
        self.assertEqual(self.disconnected, True)
        self.failureResultOf(d).trap(error.ConnectionDone)

    def test_disconnect_5(self):
        '''connect with persistent session, generate a deferred and disconnect'''
        self._connect(cleanStart=False)
        self.protocol.onDisconnection = self._disconnected
        d = self.protocol.publish(topic="foo/bar/baz1", qos=1, message="hello world 1")
        self.transport.clear()
        self.protocol.disconnect()
        self.assertEqual(self.disconnected, True)
        self.assertNoResult(d)

    def test_disconnect_6(self):
        '''connect with persistent session, generate a deferred , rebuilds protocol'''
        self._connect(cleanStart=False)
        self.protocol.onDisconnection = self._disconnected
        d = self.protocol.publish(topic="foo/bar/baz1", qos=1, message="hello world 1")
        self._serverDown()
        self._rebuild()
        self.assertEqual(self.disconnected, True)
        self.assertNoResult(d)


class TestMQTTPublisherForbiddenOps(unittest.TestCase):
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
        self.factory   = MQTTFactory(MQTTFactory.PUBLISHER)
        self._rebuild()
        self.disconnected = False
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
        self.protocol.connect("TwistedMQTT-pub", keepalive=0, cleanStart=cleanStart, version=v31)
        self.transport.clear()
        self.protocol.dataReceived(ack.encoded)


    def _rebuild(self):
        self.protocol  = self.factory.buildProtocol(0)
        self.transport.protocol = self.protocol
        MQTTBaseProtocol.callLater = self.clock.callLater
        self.protocol.makeConnection(self.transport)

    def test_forbidden_subscribe(self):
        '''Just connect and lose the transport'''
        d = self.protocol.subscribe("foo/bar/baz1", 2 )
        self.failureResultOf(d).trap(MQTTStateError)
      
    def test_forbidden_unsubscribe(self):
        '''Just connect and lose the transport'''
        d = self.protocol.unsubscribe("foo/bar/baz1")
        self.failureResultOf(d).trap(MQTTStateError)

    def test_forbidden_publish_callback(self):
        '''Just connect and lose the transport'''
        def onPublish(topic, payload, qos, dup, retain, msgId):
            pass
        self.assertRaises(MQTTStateError, self.protocol.onPublish, onPublish)



class TestMQTTPublisherIntervals(unittest.TestCase):


    def setUp(self):
        '''
        Set up a conencted state
        '''
        self.transport = proto_helpers.StringTransportWithDisconnection()
        self.clock     = task.Clock()
        MQTTBaseProtocol.callLater = self.clock.callLater
        self.factory   = MQTTFactory(MQTTFactory.PUBLISHER)
        self.addr = IPv4Address('TCP','localhost',1880)
        self._rebuild()
        # Just to generate connection contexts
        

    def _connect(self, cleanStart=True):
        '''
        Go to connected state
        '''
        ack = CONNACK()
        ack.session = False
        ack.resultCode = 0
        ack.encode()
        self.protocol.connect("TwistedMQTT-pub", keepalive=0, cleanStart=cleanStart, version=v31)
        self.transport.clear()
        self.protocol.dataReceived(ack.encoded)

    def _rebuild(self):
        self.protocol  = self.factory.buildProtocol(self.addr)
        self.transport.protocol = self.protocol
        MQTTBaseProtocol.callLater = self.clock.callLater
        self.protocol.makeConnection(self.transport)


    def _publish(self, n, qos, topic, msg, window=None):
        if window is None:
            self.protocol.setWindowSize(n)
        else:
            self.protocol.setWindowSize(window)
        dl = []
        for i in range(0,n):
            dl.append(self.protocol.publish(topic=topic, qos=qos, message=msg))
        self.transport.clear()
        for d in dl:
            if qos == 0:
                self.assertEqual(None, self.successResultOf(d))
            else:
                self.assertNoResult(d)
        return dl
    
    def _puback(self, dl):
        ackl = []
        for i in range(0, len(dl)):
            ack= PUBACK()
            ack.msgId = dl[i].msgId
            ackl.append(ack)
        encoded = bytearray()
        for ack in ackl:
            encoded.extend(ack.encode())
        self.protocol.dataReceived(encoded)
        self.transport.clear()
        for i in range(0, len(dl)):
            self.assertEqual(dl[i].msgId, self.successResultOf(dl[i]))

    def test_publish_very_large_qos1(self):
        message = '0123456789ABCDEF'*1000000 # Large PDU
        self._connect()

        # Test at 1MByte/sec
        self.protocol.setBandwith(1000000.0)
        d = self.protocol.publish(topic="foo/bar/baz1", qos=1, message=message)
        self.assertEqual(self.protocol.factory.windowPublish[self.addr][1].dup, False)
        self.transport.clear()
        self.clock.advance(10)
        self.assertEqual(self.protocol.factory.windowPublish[self.addr][1].dup, False)
        ack = PUBACK()
        ack.msgId = d.msgId
        self.protocol.dataReceived(ack.encode())
        self.transport.clear()
        self.assertEqual(ack.msgId, self.successResultOf(d))

        # A large PDU with a large bandwith estimation may retransmit
        self.protocol.setBandwith(10000000.0)
        d = self.protocol.publish(topic="foo/bar/baz1", qos=1, message=message)
        self.assertEqual(self.protocol.factory.windowPublish[self.addr][2].dup, False)
        self.transport.clear()
        self.clock.advance(10)
        self.assertEqual(self.protocol.factory.windowPublish[self.addr][2].dup, True)
        ack = PUBACK()
        ack.msgId = d.msgId
        self.protocol.dataReceived(ack.encode())
        self.transport.clear()
        self.assertEqual(ack.msgId, self.successResultOf(d))

    


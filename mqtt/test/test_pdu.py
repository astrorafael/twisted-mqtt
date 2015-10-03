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

from mqtt import v31, v311
from mqtt.pdu import (
    CONNECT,
    CONNACK,
    DISCONNECT,
    PINGREQ,
    PINGRES,
    SUBSCRIBE,
    SUBACK,
    UNSUBSCRIBE,
    UNSUBACK,
    PUBLISH,
    PUBACK,
    PUBREC,
    PUBREL,
    PUBCOMP,
    )

class PDUTestCase(unittest.TestCase):
        

    def test_CONNECT_encdec(self):
        request = CONNECT()
        response = CONNECT()
        request.clientId    = "client-foo"
        request.version     = v31
        request.keepalive   = 0
        request.willTopic   = None
        request.willMessage = None
        request.willQoS     = None
        request.willRetain  = None
        request.username    = None
        request.password    = None
        request.cleanStart  = True
        response.decode(request.encode())
        self.assertEqual(request.encoded[0],  response.encoded[0])
        self.assertEqual(request.version,     response.version)
        self.assertEqual(request.clientId,    response.clientId)
        self.assertEqual(request.keepalive,   response.keepalive)
        self.assertEqual(request.willTopic,   response.willTopic)
        self.assertEqual(request.willMessage, response.willMessage)
        self.assertEqual(request.willQoS,     response.willQoS)
        self.assertEqual(request.willRetain,  response.willRetain)
        self.assertEqual(request.username,    response.username)
        self.assertEqual(request.password,    response.password)
        self.assertEqual(request.cleanStart,  response.cleanStart)
        

        
    def test_CONNECT_encdec_keepalive(self):
        request = CONNECT()
        response = CONNECT()
        request.version     = v31
        request.clientId    = "client-foo"
        request.keepalive   = 12
        request.willTopic   = None
        request.willMessage = None
        request.willQoS     = None
        request.willRetain  = None
        request.username    = None
        request.password    = None
        request.cleanStart  = True
        response.decode(request.encode())
        self.assertEqual(request.encoded[0],  response.encoded[0])
        self.assertEqual(request.version,     response.version)
        self.assertEqual(request.clientId,    response.clientId)
        self.assertEqual(request.keepalive,   response.keepalive)
        self.assertEqual(request.willTopic,   response.willTopic)
        self.assertEqual(request.willMessage, response.willMessage)
        self.assertEqual(request.willQoS,     response.willQoS)
        self.assertEqual(request.willRetain,  response.willRetain)
        self.assertEqual(request.username,    response.username)
        self.assertEqual(request.password,    response.password)
        self.assertEqual(request.cleanStart,  response.cleanStart)
        self.assertEqual(request.version,     response.version)

    def test_CONNECT_encdec_willTopic(self):
        request = CONNECT()
        response = CONNECT()
        request.clientId    = "client-foo"
        request.keepalive   = 1
        request.willTopic   = "foo-topic"
        request.willMessage = ""
        request.willQoS     = 1
        request.willRetain  = False
        request.username    = None
        request.password    = None
        request.cleanStart  = True
        request.version     = v31
        response.decode(request.encode())
        self.assertEqual(request.encoded[0],  response.encoded[0])
        self.assertEqual(request.version,     response.version)
        self.assertEqual(request.clientId,    response.clientId)
        self.assertEqual(request.keepalive,   response.keepalive)
        self.assertEqual(request.willTopic,   response.willTopic)
        self.assertEqual(request.willMessage, response.willMessage)
        self.assertEqual(request.willQoS,     response.willQoS)
        self.assertEqual(request.willRetain,  response.willRetain)
        self.assertEqual(request.username,    response.username)
        self.assertEqual(request.password,    response.password)
        self.assertEqual(request.cleanStart,  response.cleanStart)

    def test_CONNECT_encdec_willMessage(self):
        request = CONNECT()
        response = CONNECT()
        request.clientId    = "client-foo"
        request.keepalive   = 1
        request.willTopic   = "foo-topic"
        request.willMessage = "Hello World"
        request.willQoS     = 2
        request.willRetain  = False
        request.username    = None
        request.password    = None
        request.cleanStart  = True
        request.version     = v31
        response.decode(request.encode())
        self.assertEqual(request.encoded[0],  response.encoded[0])
        self.assertEqual(request.version,     response.version)
        self.assertEqual(request.clientId,    response.clientId)
        self.assertEqual(request.keepalive,   response.keepalive)
        self.assertEqual(request.willTopic,   response.willTopic)
        self.assertEqual(request.willMessage, response.willMessage)
        self.assertEqual(request.willQoS,     response.willQoS)
        self.assertEqual(request.willRetain,  response.willRetain)
        self.assertEqual(request.username,    response.username)
        self.assertEqual(request.password,    response.password)
        self.assertEqual(request.cleanStart,  response.cleanStart)

    def test_CONNECT_encdec_willRetain(self):
        request = CONNECT()
        response = CONNECT()
        request.clientId    = "client-foo"
        request.keepalive   = 1
        request.willTopic   = "foo-topic"
        request.willMessage = "Hello World"
        request.willQoS     = 2
        request.willRetain  = True
        request.username    = None
        request.password    = None
        request.cleanStart  = True
        request.version     = v31
        response.decode(request.encode())
        self.assertEqual(request.encoded[0],  response.encoded[0])
        self.assertEqual(request.version,     response.version)
        self.assertEqual(request.clientId,    response.clientId)
        self.assertEqual(request.keepalive,   response.keepalive)
        self.assertEqual(request.willTopic,   response.willTopic)
        self.assertEqual(request.willMessage, response.willMessage)
        self.assertEqual(request.willQoS,     response.willQoS)
        self.assertEqual(request.willRetain,  response.willRetain)
        self.assertEqual(request.username,    response.username)
        self.assertEqual(request.password,    response.password)
        self.assertEqual(request.cleanStart,  response.cleanStart)
        

    def test_CONNECT_encdec_userpass(self):
        request = CONNECT()
        response = CONNECT()
        request.clientId    = "client-foo"
        request.keepalive   = 12000
        request.willTopic   = "foo-topic"
        request.willMessage = ""
        request.willQoS     = 0
        request.willRetain  = False
        request.username    = "foouser"
        request.password    = "foopasswd"
        request.cleanStart  = True
        request.version     = v31
        response.decode(request.encode())
        self.assertEqual(request.encoded[0],  response.encoded[0])
        self.assertEqual(request.version,     response.version)
        self.assertEqual(request.clientId,    response.clientId)
        self.assertEqual(request.keepalive,   response.keepalive)
        self.assertEqual(request.willTopic,   response.willTopic)
        self.assertEqual(request.willMessage, response.willMessage)
        self.assertEqual(request.willQoS,     response.willQoS)
        self.assertEqual(request.willRetain,  response.willRetain)
        self.assertEqual(request.username,    response.username)
        self.assertEqual(request.password,    response.password.decode(encoding='ascii', errors='ignore'))
        self.assertEqual(request.cleanStart,  response.cleanStart)
       
    def test_CONNECT_encdec_session(self):
        request = CONNECT()
        response = CONNECT()
        request.clientId    = "client-foo"
        request.keepalive   = 1200
        request.willTopic   = "foo-topic"
        request.willMessage = ""
        request.willQoS     = 1
        request.willRetain  = False
        request.username    = None
        request.password    = None
        request.cleanStart  = False
        request.version     = v31
        response.decode(request.encode())
        self.assertEqual(request.encoded[0],  response.encoded[0])
        self.assertEqual(request.version,     response.version)
        self.assertEqual(request.clientId,    response.clientId)
        self.assertEqual(request.keepalive,   response.keepalive)
        self.assertEqual(request.willTopic,   response.willTopic)
        self.assertEqual(request.willMessage, response.willMessage)
        self.assertEqual(request.willQoS,     response.willQoS)
        self.assertEqual(request.willRetain,  response.willRetain)
        self.assertEqual(request.username,    response.username)
        self.assertEqual(request.password,    response.password)
        self.assertEqual(request.cleanStart,  response.cleanStart)
        

    def test_CONNECT_encdec_version(self):
        request = CONNECT()
        response = CONNECT()
        request.clientId    = "client-foo"
        request.keepalive   = 120
        request.willTopic   = "foo-topic"
        request.willMessage = ""
        request.willQoS     = 0
        request.willRetain  = False
        request.username    = None
        request.password    = None
        request.cleanStart  = True
        request.version     = v311  
        response.decode(request.encode())
        self.assertEqual(request.encoded[0],  response.encoded[0])
        self.assertEqual(request.version,     response.version)
        self.assertEqual(request.clientId,    response.clientId)
        self.assertEqual(request.keepalive,   response.keepalive)
        self.assertEqual(request.willTopic,   response.willTopic)
        self.assertEqual(request.willMessage, response.willMessage)
        self.assertEqual(request.willQoS,     response.willQoS)
        self.assertEqual(request.willRetain,  response.willRetain)
        self.assertEqual(request.username,    response.username)
        self.assertEqual(request.password,    response.password)
        self.assertEqual(request.cleanStart,  response.cleanStart)
       


    def test_PINGREQ_encdec(self):
        request = PINGREQ()
        response = PINGREQ()
        
        response.decode(request.encode())
        self.assertEqual(request.encoded[0],  response.encoded[0])

    def test_PINGRES_encdec(self):
        request = PINGRES()
        response = PINGRES()
        
        response.decode(request.encode())
        self.assertEqual(request.encoded[0], response.encoded[0])

    def test_DISCONNECT_encdec(self):
        request = DISCONNECT()
        response = DISCONNECT()
        
        response.decode(request.encode())
        self.assertEqual(request.encoded[0],  response.encoded[0])

    def test_CONNACK_encdec(self):
        request = CONNACK()
        response = CONNACK()
        request.session    = True
        request.resultCode = 2
        
        response.decode(request.encode())
        self.assertEqual(request.encoded[0],  response.encoded[0])
        self.assertEqual(request.session,     response.session)
        self.assertEqual(request.resultCode,  response.resultCode)

    def test_SUBSCRIBE_encdec(self):
        request = SUBSCRIBE()
        response = SUBSCRIBE()
        request.topics = [('foo', 1), ('bar',0), ('baz',2)]
        request.msgId  = 5
        
        response.decode(request.encode())
        self.assertEqual(request.msgId,  response.msgId)
        self.assertEqual(request.topics, response.topics)
       
    def test_SUBACK_encdec(self):
        request  = SUBACK()
        response = SUBACK()
        request.msgId = 5
        request.granted = [(0, False), (0, True), (1,False), (1,True), (2,False), (2,True)]
        
        response.decode(request.encode())
        self.assertEqual(request.msgId,  response.msgId)
        self.assertEqual(request.granted, response.granted)

    def test_UNSUBSCRIBE_encdec(self):
        request  = UNSUBSCRIBE()
        response = UNSUBSCRIBE()
        request.topics = ['foo', 'bar', 'baz']
        request.msgId = 6
        
        response.decode(request.encode())
        self.assertEqual(request.msgId,  response.msgId)
        self.assertEqual(request.topics, response.topics)

    def test_UNSUBACK_encdec(self):
        request  = UNSUBACK()
        response = UNSUBACK()
        request.msgId = 5
        
        response.decode(request.encode())
        self.assertEqual(request.msgId, response.msgId)

    def test_PUBACK_encdec(self):
        request  = PUBACK()
        response = PUBACK()
        request.msgId = 65535
        
        response.decode(request.encode())
        self.assertEqual(request.msgId, response.msgId)

    def test_PUBREC_encdec(self):
        request  = PUBREC()
        response = PUBREC()
        request.msgId = 30001
        
        response.decode(request.encode())
        self.assertEqual(request.msgId, response.msgId)

    def test_PUBREL_encdec(self):
        request  = PUBREL()
        response = PUBREL()
        request.msgId = 30002
        
        response.decode(request.encode())
        self.assertEqual(request.msgId, response.msgId)

    def test_PUBCOMP_encdec(self):
        request  = PUBCOMP()
        response = PUBCOMP()
        request.msgId = 30002
        
        response.decode(request.encode())
        self.assertEqual(request.msgId, response.msgId)

    def test_PUBLISH_encdec(self):
        request  = PUBLISH()
        response = PUBLISH()
        request.msgId   = None
        request.qos     = 0
        request.dup     = False
        request.retain  = False
        request.topic   = "foo"
        request.payload = "foo"
        
        response.decode(request.encode())
        self.assertEqual(request.msgId,   response.msgId)
        self.assertEqual(request.qos,     response.qos)
        self.assertEqual(request.dup,     response.dup)
        self.assertEqual(request.retain,  response.retain)
        self.assertEqual(request.topic,   response.topic)
        self.assertEqual(request.payload, response.payload.decode(encoding='utf-8'))

    def test_PUBLISH_encdec_qos(self):
        request  = PUBLISH()
        response = PUBLISH()
        request.msgId   = 30001
        request.qos     = 1
        request.dup     = False
        request.retain  = False
        request.topic   = "foo"
        request.payload = "foo"
        
        response.decode(request.encode())
        self.assertEqual(request.msgId,   response.msgId)
        self.assertEqual(request.qos,     response.qos)
        self.assertEqual(request.dup,     response.dup)
        self.assertEqual(request.retain,  response.retain)
        self.assertEqual(request.topic,   response.topic)
        self.assertEqual(request.payload, response.payload.decode(encoding='utf-8'))

    def test_PUBLISH_encdec_dup(self):
        request  = PUBLISH()
        response = PUBLISH()
        request.msgId   = 30001
        request.qos     = 1
        request.dup     = True
        request.retain  = False
        request.topic   = "foo"
        request.payload = "foo"
        
        response.decode(request.encode())
        self.assertEqual(request.msgId,   response.msgId)
        self.assertEqual(request.qos,     response.qos)
        self.assertEqual(request.dup,     response.dup)
        self.assertEqual(request.retain,  response.retain)
        self.assertEqual(request.topic,   response.topic)
        self.assertEqual(request.payload, response.payload.decode(encoding='utf-8'))

    def test_PUBLISH_encdec_retain(self):
        request  = PUBLISH()
        response = PUBLISH()
        request.msgId   = 30001
        request.qos     = 1
        request.dup     = False
        request.retain  = True
        request.topic   = "foo"
        request.payload = "foo"
        
        response.decode(request.encode())
        self.assertEqual(request.msgId,   response.msgId)
        self.assertEqual(request.qos,     response.qos)
        self.assertEqual(request.dup,     response.dup)
        self.assertEqual(request.retain,  response.retain)
        self.assertEqual(request.topic,   response.topic)
        self.assertEqual(request.payload, response.payload.decode(encoding='utf-8'))

    def test_PUBLISH_encdec_payload_str(self):
        request  = PUBLISH()
        response = PUBLISH()
        request.msgId   = 30001
        request.qos     = 1
        request.dup     = False
        request.retain  = True
        request.topic   = "foo"
        request.payload = ""
        
        response.decode(request.encode())
        self.assertEqual(request.msgId,   response.msgId)
        self.assertEqual(request.qos,     response.qos)
        self.assertEqual(request.dup,     response.dup)
        self.assertEqual(request.retain,  response.retain)
        self.assertEqual(request.topic,   response.topic)
        self.assertEqual(request.payload, response.payload.decode(encoding='utf-8'))

       
    def test_PUBLISH_encdec_payload_bytearray(self):
        request  = PUBLISH()
        response = PUBLISH()
        request.msgId   = 30001
        request.qos     = 1
        request.dup     = False
        request.retain  = True
        request.topic   = "foo"
        request.payload = bytearray(5)
        
        response.decode(request.encode())
        self.assertEqual(request.msgId,   response.msgId)
        self.assertEqual(request.qos,     response.qos)
        self.assertEqual(request.dup,     response.dup)
        self.assertEqual(request.retain,  response.retain)
        self.assertEqual(request.topic,   response.topic)
        self.assertEqual(request.payload, response.payload)


class PDUTestCase2(unittest.TestCase):

    def test_PUBREC_enc_fail1(self):
        request  = PUBACK()
        response = PUBACK()
        request.msgId = -1
        self.assertRaises(ValueError, request.encode)


    def test_PUBREC_enc_fail2(self):
        request  = PUBACK()
        response = PUBACK()
        request.msgId = 2000000
        self.assertRaises(ValueError, request.encode)

    def test_PUBLISH_encdec_payload_int(self):
        request  = PUBLISH()
        request.msgId   = 30001
        request.qos     = 1
        request.dup     = False
        request.retain  = True
        request.topic   = "foo"
        request.payload = 65537
        self.assertRaises(TypeError, request.encode)

    def test_PUBLISH_encdec_payload_float(self):
        request  = PUBLISH()
        response = PUBLISH()
        request.msgId   = 30001
        request.qos     = 1
        request.dup     = False
        request.retain  = True
        request.topic   = "foo"
        request.payload = 12.25
        self.assertRaises(TypeError, request.encode)
    
        

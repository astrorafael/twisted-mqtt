# -*- test-case-name: mqtt.test.test_pdu -*-
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

from twisted.logger import Logger

# -----------
# Own modules
# -----------

from .     import PY2, v31, v311
from .error import StringValueError, PayloadValueError, PayloadTypeError


log = Logger(namespace='mqtt')

# ---------------------------------------
# MQTT Encoding/Decoding Helper functions
# ---------------------------------------

def encodeString(string):
    '''
    Encode an UTF-8 string into MQTT format. 
    Returns a bytearray
    '''
    encoded = bytearray(2)
    encoded.extend(bytearray(string, encoding='utf-8'))
    l = len(encoded)-2
    if(l > 65535):
        raise StringValueError(l)
    encoded[0] = l >> 8
    encoded[1] = l & 0xFF
    return encoded

def decodeString(encoded):
    '''
    Decodes an UTF-8 string from an encoded MQTT bytearray.
    Returns the decoded string and renaining bytearray to be parsed
    '''
    length = encoded[0]*256 + encoded[1]
    return (encoded[2:2+length].decode('utf-8'), encoded[2+length:])


def encode16Int(value):
    '''
    Encodes a 16 bit unsigned integer into MQTT format.
    Returns a bytearray
    '''
    value      = int(value)
    encoded    = bytearray(2)
    encoded[0] = value >> 8
    encoded[1] = value & 0xFF
    return encoded

def decode16Int(encoded):
    '''
    Decodes a 16 bit unsigned integer from MQTT bytearray.
    '''
    return encoded[0]*256 + encoded[1]


def encodeLength(value):
    '''
    Encodes value into a multibyte sequence defined by MQTT protocol.
    Used to encode packet length fields.
    '''
    encoded = bytearray()
    while True:
        digit = value % 128
        value //= 128
        if value > 0:
            digit |= 128
        encoded.append(digit)
        if value <= 0:
            break
    return encoded


def decodeLength(encoded):
    '''
    Decodes a variable length value defined in the MQTT protocol.
    This value typically represents remaining field lengths
    '''
    value      = 0
    multiplier = 1
    for i in encoded:
        value += (i & 0x7F) * multiplier
        multiplier *= 0x80
        if (i & 0x80) != 0x80:
            break
    return value


# -------------------------------
# MQTT Protocol Data Units (PDUs)
# -------------------------------

class DISCONNECT(object):

    def __init__(self):
        self.encoded = None 

    def encode(self):
        '''
        Encode and store a DISCONNECT control packet.
        '''
        header    = bytearray(2)
        header[0] = 0xE0
        self.encoded = header
        return str(header) if PY2 else bytes(header)

    def decode(self, packet):
        '''
        Decode a DISCONNECT control packet. 
        '''
        self.encoded = packet
        

# ------------------------------------------------------------------------------

class PINGREQ(object):

    def __init__(self):
        self.encoded = None 

    def encode(self):
        '''
        Encode and store a PINGREQ control message.
        '''
        header    = bytearray(2)
        header[0] = 0xC0
        self.encoded = header
        return str(header) if PY2 else bytes(header)

    def decode(self, packet):
        '''
        Decode a PINGREQ control packet. 
        '''
        self.encoded = packet

# ------------------------------------------------------------------------------

# Server class Only
class PINGRES(object):

    def __init__(self):
        self.encoded = None 

    def encode(self):
        '''
        Encode and store a PINGRES control message.
        '''
        header    = bytearray(2)
        header[0] = 0xD0
        self.encoded = header
        return str(header) if PY2 else bytes(header)

    def decode(self, packet):
        '''
        Decode a CONNACK control packet. 
        '''
        self.encoded = packet

# ------------------------------------------------------------------------------

class CONNECT(object):

    def __init__(self):
        self.encoded    = None 
        self.clientId    = None
        self.keepalive   = None
        self.willTopic   = None
        self.willMessage = None
        self.willQoS     = None
        self.willRetain  = None
        self.username    = None
        self.password    = None
        self.cleanStart  = None
        self.version     = None

    def encode(self):
        '''
        Encode and store a CONNECT control packet. 
        @raise e: C{ValueError} if any encoded topic string exceeds 65535 bytes.
        @raise e: C{ValueError} if encoded username string exceeds 65535 bytes.
        '''
        header    = bytearray(1)
        varHeader = bytearray()
        payload   = bytearray()
        header[0] = 0x10            # packet code
        # ---- Variable header encoding section -----
        
        varHeader.extend(encodeString(self.version['tag'])) 
        varHeader.append(self.version['level']) # protocol Level
        flags =  (self.cleanStart << 1)
        if  self.willTopic is not None and self.willMessage is not None:
            flags |= 0x04 | (self.willRetain << 5) | (self.willQoS << 3)
        if self.username is not None:
            flags |= 0x80
        if self.password is not None:
            flags |= 0x40
        varHeader.append(flags)
        varHeader.extend(encode16Int(self.keepalive))
        # ------ Payload encoding section ----
        payload.extend(encodeString(self.clientId))
        if self.willTopic is not None and self.willMessage is not None:
            payload.extend(encodeString(self.willTopic))
            payload.extend(encodeString(self.willMessage))
        if self.username is not None:
             payload.extend(encodeString(self.username))
        if self.password is not None:
            payload.extend(encode16Int(len(self.password)))
            payload.extend(bytearray(self.password, encoding='ascii', errors='ignore'))
        # ---- Build the packet once all lengths are known ----
        header.extend(encodeLength(len(varHeader) + len(payload)))
        header.extend(varHeader)
        header.extend(payload)
        self.encoded = header
        return str(header) if PY2 else bytes(header)

    def decode(self, packet):
        '''
        Decode a CONNECT control packet. 
        '''
        self.encoded = packet
        # Strip the fixed header plus variable length field
        lenLen = 1
        while packet[lenLen] & 0x80:
            lenLen += 1
        packet_remaining = packet[lenLen+1:]
        # Variable Header
        version_str, packet_remaining = decodeString(packet_remaining)
        version_id = int(packet_remaining[0])
        if version_id == v31['level']:
            self.version = v31
        else:
            self.version = v311
        flags = packet_remaining[1]
        self.cleanStart = (flags & 0x02) != 0
        willFlag   = (flags & 0x04) != 0
        willQoS    = (flags >> 3) & 0x03
        willRetain = (flags & 0x20) != 0
        userFlag   = (flags & 0x80)  != 0
        passFlag   = (flags & 0x40)  != 0
        packet_remaining = packet_remaining[2:]
        self.keepalive = decode16Int(packet_remaining)
        # Payload
        packet_remaining = packet_remaining[2:]
        self.clientId, packet_remaining = decodeString(packet_remaining)
        if willFlag:
            self.willRetain = willRetain
            self.willQoS    = willQoS
            self.willTopic,  packet_remaining  = decodeString(packet_remaining)
            self.willMessage, packet_remaining = decodeString(packet_remaining)
        if userFlag:
            self.username, packet_remaining = decodeString(packet_remaining)
        if passFlag:
            l = decode16Int(packet_remaining)
            self.password = packet_remaining[2:2+l]



# ------------------------------------------------------------------------------

class CONNACK(object):

    def __init__(self):
        self.encoded   = None
        self.session    = None
        self.resultCode = None 

    def encode(self):
        '''
        Encode and store a CONNACK control packet. 
        '''
     
        header       = bytearray(1)
        varHeader    = bytearray(2)
        header[0]    = 0x20 
        varHeader[0] = self.session
        varHeader[1] = self.resultCode
        header.extend(encodeLength(len(varHeader)))
        header.extend(varHeader)
        self.encoded = header
        return str(header) if PY2 else bytes(header)

    def decode(self, packet):
        '''
        Decode a CONNACK control packet. 
        '''
        self.encoded = packet
        # Strip the fixed header plus variable length field
        lenLen = 1
        while packet[lenLen] & 0x80:
            lenLen += 1
        packet_remaining = packet[lenLen+1:]
        self.session = (packet_remaining[0] & 0x01) == 0x01 
        self.resultCode  = int(packet_remaining[1])
      
# ------------------------------------------------------------------------------

class SUBSCRIBE(object):

    def __init__(self):
        self.encoded = None
        self.topics   = None
        self.msgId    = None 

    def encode(self):
        '''
        Encode and store a SUBSCRIBE control packet. 
        @raise e: C{ValueError} if any encoded topic string exceeds 65535 bytes.
        '''
        header    = bytearray(1)
        payload   = bytearray()
        varHeader = encode16Int(self.msgId)
        header[0] = 0x82        # packet with QoS=1
        for topic in self.topics:
            payload.extend(encodeString(topic[0])) # topic name
            payload.append(topic[1])               # topic QoS
        header.extend(encodeLength(len(varHeader) + len(payload)))
        header.extend(varHeader)
        header.extend(payload)
        self.encoded = header
        return str(header) if PY2 else bytes(header)

    def decode(self, packet):
        '''
        Decode a SUBSCRIBE control packet. 
        '''
        self.encoded = packet
        lenLen = 1
        while packet[lenLen] & 0x80:
            lenLen += 1
        packet_remaining = packet[lenLen+1:]
        self.msgId   = decode16Int(packet_remaining[0:2])
        self.topics = []
        packet_remaining = packet_remaining[2:]
        while len(packet_remaining):
            topic, packet_remaining = decodeString(packet_remaining)
            qos =  int (packet_remaining[0]) & 0x03
            self.topics.append((topic,qos))
            packet_remaining = packet_remaining[1:]
        


# ------------------------------------------------------------------------------
# Server Class

class SUBACK(object):

    def __init__(self):
        self.encoded = None
        self.msgId   = None
        self.granted = None

    def encode(self):
        '''
        Encode and store a SUBACK control packet.
        '''
        header    = bytearray(1)
        payload   = bytearray()
        varHeader = encode16Int(self.msgId)
        header[0] = 0x90
        for code in self.granted:
            payload.append(code[0] | (0x80 if code[1] == True else 0x00))
        header.extend(encodeLength(len(varHeader) + len(payload)))
        header.extend(varHeader)
        header.extend(payload)
        self.encoded = header
        return str(header) if PY2 else bytes(header)


    def decode(self, packet):
        '''
        Decode a SUBACK control packet. 
        '''
        self.encoded = packet
        lenLen = 1
        while packet[lenLen] & 0x80:
            lenLen += 1
        packet_remaining = packet[lenLen+1:]
        self.msgId   = decode16Int(packet_remaining)
        # Make a sequence of tuples of (GrantedQoS, Failure Flag)
        self.granted = [ (byte & 0x7F, byte & 0x80 == 0x80) 
                    for byte in packet_remaining[2:] ]




# ------------------------------------------------------------------------------

class UNSUBSCRIBE(object):

    def __init__(self):
        self.encoded = None
        self.msgId   = None
        self.topics  = None

    def encode(self):
        '''
        Encode and store an UNSUBCRIBE control packet
        @raise e: C{ValueError} if any encoded topic string exceeds 65535 bytes
        '''
        header    = bytearray(1)
        payload   = bytearray()
        varHeader = encode16Int(self.msgId)
        header[0] = 0xA2    # packet with QoS=1
        for topic in self.topics:
            payload.extend(encodeString(topic)) # topic name
        header.extend(encodeLength(len(varHeader) + len(payload)))
        header.extend(varHeader)
        header.extend(payload)
        self.encoded = header
        return str(header) if PY2 else bytes(header)

    def decode(self, packet):
        '''
        Decode a UNSUBACK control packet. 
        '''
        self.encoded = packet
        lenLen = 1
        while packet[lenLen] & 0x80:
            lenLen += 1
        packet_remaining = packet[lenLen+1:]
        self.msgId   = decode16Int(packet_remaining[0:2])
        self.topics = []
        packet_remaining = packet_remaining[2:]
        while len(packet_remaining):
            l = decode16Int(packet_remaining[0:2])
            topic = packet_remaining[2:2+l].decode(encoding='utf-8')
            self.topics.append(topic)
            packet_remaining = packet_remaining[2+l:]

# ------------------------------------------------------------------------------

# Server PDU
class UNSUBACK(object):

    def __init__(self):
        self.encoded = None
        self.msgId   = None

    def encode(self):
        '''
        Encode and store an UNSUBACK control packet
        '''
        header    = bytearray(1)
        varHeader = encode16Int(self.msgId)
        header[0] = 0xB0 
        header.extend(encodeLength(len(varHeader)))
        header.extend(varHeader)
        self.encoded = header
        return str(header) if PY2 else bytes(header)

    def decode(self, packet):
        '''
        Decode a UNSUBACK control packet. 
        '''
        self.encoded = packet
        lenLen = 1
        while packet[lenLen] & 0x80:
            lenLen += 1
        packet_remaining = packet[lenLen+1:]
        self.msgId   = decode16Int(packet_remaining)


# ------------------------------------------------------------------------------

class PUBLISH(object):

    def __init__(self):
        self.encoded = None
        self.qos     = None
        self.dup     = None
        self.retain  = None
        self.topic   = None
        self.msgId   = None
        self.payload = None

    def encode(self):
        '''
        Encode and store a PUBLISH control packet.
        @raise e: C{ValueError} if encoded topic string exceeds 65535 bytes.
        @raise e: C{ValueError} if encoded packet size exceeds 268435455 bytes.
        @raise e: C{TypeError} if C{data} is not a string, bytearray, int, boolean or float.
        '''
        header    = bytearray(1)
        varHeader = bytearray()
        payload   = bytearray()

        if self.qos:
            header[0] = 0x30 | self.retain | (self.qos << 1) | (self.dup << 3)
            varHeader.extend(encodeString(self.topic)) # topic name
            varHeader.extend(encode16Int(self.msgId))  # msgId should not be None
        else:
            header[0] = 0x30 | self.retain
            varHeader.extend(encodeString(self.topic)) # topic name
        if isinstance(self.payload, bytearray):
            payload.extend(self.payload)
        elif isinstance(self.payload, str):
            payload.extend(bytearray(self.payload, encoding='utf-8'))
        else:
            raise PayloadTypeError(type(self.payload))
        totalLen = len(varHeader) + len(payload)
        if totalLen > 268435455:
            raise PayloadValueError(totalLen)
        header.extend(encodeLength(totalLen))
        header.extend(varHeader)
        header.extend(payload)
        self.encoded = header
        return str(header) if PY2 else bytes(header)

    def decode(self, packet):
        '''
        Decode a PUBLISH control packet. 
        '''
        self.encoded = packet
        lenLen = 1
        while packet[lenLen] & 0x80:
            lenLen += 1
        packet_remaining = packet[lenLen+1:]
        self.dup    = (packet[0] & 0x08) == 0x08
        self.qos    = (packet[0] & 0x06) >> 1
        self.retain = (packet[0] & 0x01) == 0x01
        self.topic, _  = decodeString(packet_remaining)
        topicLen       = decode16Int(packet_remaining)
        if self.qos:
            self.msgId = decode16Int( packet_remaining[topicLen+2:topicLen+4] )
            self.payload =  packet_remaining[topicLen+4:]
        else:
            self.msgId = None
            self.payload = packet_remaining[topicLen+2:] # payload is a bytearray
        

# ------------------------------------------------------------------------------

class PUBACK(object):

    def __init__(self):
        self.encoded = None
        self.msgId   = None

    def encode(self):
        '''
        Encode and store a PUBACK control packet
        '''
        header    = bytearray(1)
        varHeader = encode16Int(self.msgId)
        header[0] = 0x40 
        header.extend(encodeLength(len(varHeader)))
        header.extend(varHeader)
        self.encoded = header
        return str(header) if PY2 else bytes(header)

    def decode(self, packet):
        '''
        Decode a PUBACK control packet. 
        '''
        self.encoded = packet
        lenLen = 1
        while packet[lenLen] & 0x80:
            lenLen += 1
        packet_remaining = packet[lenLen+1:]
        self.msgId = decode16Int(packet_remaining)


# ------------------------------------------------------------------------------

class PUBREC(object):
   
    def __init__(self):
        self.encoded = None
        self.msgId   = None

    def encode(self):
        '''
        Encode and store a PUBREC control packet
        '''
        header    = bytearray(1)
        varHeader = encode16Int(self.msgId)
        header[0] = 0x50 
        header.extend(encodeLength(len(varHeader)))
        header.extend(varHeader)
        self.encoded = header
        return str(header) if PY2 else bytes(header)

    def decode(self, packet):
        '''
        Decode a PUBREC control packet. 
        '''
        self.encoded = packet
        lenLen = 1
        while packet[lenLen] & 0x80:
            lenLen += 1
        packet_remaining = packet[lenLen+1:]
        self.msgId = decode16Int(packet_remaining)


# ------------------------------------------------------------------------------

class PUBREL(object):
   
    def __init__(self):
        self.encoded = None
        self.msgId   = None
        self.dup     = None

    def encode(self):
        '''
        Encode and store a PUBREL control packet
        '''
        header    = bytearray(1)
        varHeader = encode16Int(self.msgId)
        header[0] = 0x62    # packet with QoS=1
        header.extend(encodeLength(len(varHeader)))
        header.extend(varHeader)
        self.encoded = header
        return str(header) if PY2 else bytes(header)

    def decode(self, packet):
        '''
        Decode a PUBREL control packet. 
        '''
        self.encoded = packet
        lenLen = 1
        while packet[lenLen] & 0x80:
            lenLen += 1
        packet_remaining = packet[lenLen+1:]
        self.msgId  = decode16Int(packet_remaining)
        self.dup = (packet[0] & 0x08) == 0x08


# ------------------------------------------------------------------------------

class PUBCOMP(object):
   
    def __init__(self):
        self.encoded = None
        self.msgId    = None
        
    def encode(self):
        '''
        Encode and store a PUBCOMP control packet
        '''
        header    = bytearray(1)
        varHeader = encode16Int(self.msgId)
        header[0] = 0x72 
        header.extend(encodeLength(len(varHeader)))
        header.extend(varHeader)
        self.encoded = header
        return str(header) if PY2 else bytes(header)

    def decode(self, packet):
        '''
        Decode a PUBCOMP control packet. 
        '''
        self.encoded = packet
        lenLen = 1
        while packet[lenLen] & 0x80:
            lenLen += 1
        packet_remaining = packet[lenLen+1:]
        self.msgId   = decode16Int(packet_remaining)

# ------------------------------------------------------------------------------

__all__ = [
    'decodeLength',
    'CONNECT',
    'CONNACK',
    'DISCONNECT',
    'PINGREQ',
    'PINGRES',
    'SUBSCRIBE',
    'SUBACK',
    'UNSUBSCRIBE',
    'UNSUBACK',
    'PUBLISH',
    'PUBACK',
    'PUBREC',
    'PUBREL',
    'PUBCOMP',
]

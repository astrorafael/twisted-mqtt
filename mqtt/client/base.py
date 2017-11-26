# -*- test-case-name: mqtt.client.test.test_base -*-
# ----------------------------------------------------------------------
# Original Copyright (C) 2012 by Adam Rudd
# Modifications and redesign by Rafael Gonzalez 
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

# +-----------------------------------------+
# | PACKET TYPES INVOLVED IN CLIENTS BY QoS |
# +-------------+-------------+-------------+
# |   QoS = 2   |   QoS = 1   |   QoS = 0   |
# +-------------+-------------+-------------+
# | CONNECT     | CONNECT     | CONNECT     | (out)(all)
# | CONNACK     | CONNACK     | CONNACK     | (in) (all)
# | DISCONNECT  | DISCONNECT  | DISCONNECT  | (out)(all)
# | PINGREQ     | PINGREQ     | PINGREQ     | (out)(all)
# | PINGRES     | PINGRES     | PINGRES     | (in) (all)
# +-------------+-------------+-------------+
# | SUBSCRIBE   | SUBSCRIBE   | SUBSCRIBE   | (out)(subscriber)
# | SUBACK      | SUBACK      | SUBACK      | (in) (subscriber)
# | UNSUBSCRIBE | UNSUBSCRIBE | UNSUBSCRIBE | (out)(subscriber)
# | UNSUBACK    | UNSUBACK    | UNSUBACK    | (in) (subscriber)
# +-------------+-------------+-------------+
# | PUBLISH     | PUBLISH     | PUBLISH     | (in/out)(subscriber/pubisher)
# | PUBREC      | PUBACK      |             | (out/in)(subscriber/publisher)
# | PUBREL      |             |             | (in/out)(subscriber/publisher)
# | PUBCOMP     |             |             | (out/in)(subscriber/publisher)
# +-------------+-------------+-------------+

# ----------------
# Standard modules
# ----------------

from random import randint

# ----------------
# Twisted  modules
# ----------------

from zope.interface import implementer
from twisted.internet.protocol import Protocol
from twisted.internet import reactor, defer, task
from twisted.logger   import Logger
from twisted.python   import failure

# -----------
# Own modules
# -----------

from ..          import v31, v311
from ..pdu       import decodeLength, DISCONNECT, PINGREQ, CONNECT, CONNACK
from ..pdu       import SUBACK, UNSUBACK, PUBLISH, PUBREL, PUBACK, PUBREC, PUBCOMP
from ..error     import ( MQTTStateError, MQTTWindowError, MQTTTimeoutError, TimeoutValueError, 
        QoSValueError, KeepaliveValueError, ClientIdValueError, ProtocolValueError, MissingTopicError,
        MissingPayloadError, MissingUserError, WindowValueError)
from .interfaces import IMQTTClientControl
from .interval   import Interval


MQTT_CONNECT_CODES = [
    "Connection Accepted",
    "Connection Refused, unacceptable protocol version",
    "Connection Refused, identifier rejected",
    "Connection Refused, Server unavailable",
    "Connection Refused, bad user name or password",
    "Connection Refused, not authorized",
]

log = Logger(namespace='mqtt')


# ---------------------------------------
# Base State Class
# ---------------------------------------

class BaseState(object):

    def __init__(self, protocol):
        self.protocol = protocol


    def connect(self, request):
        '''
        Send a CONNECT control packet.
        '''
        state = self.__class__.__name__
        return defer.fail(MQTTStateError("Unexpected connect() operation", state))


    def disconnect(self, request):
        '''
        Send a DISCONNECT control packet.
        '''
        state = self.__class__.__name__
        raise MQTTStateError("Unexpected disconnect() operation", state)


    def subscribe(self, request):
        state = self.__class__.__name__
        return defer.fail(MQTTStateError("Unexpected subscribe() operation", state))


    def unsubscribe(self, request):
        state = self.__class__.__name__
        return defer.fail(MQTTStateError("Unexpected unsubscribe() operation,", state))


    def publish(self, request):
        state = self.__class__.__name__
        return defer.fail(MQTTStateError("Unexpected publish() operation", state))


    # -------------------------------
    # Handle traffic form the network
    # -------------------------------

    # These default implementations should never be executed
    # in a well-behaved server

    def handleCONNACK(self, response):
        '''
        Handles CONNACK packet from the server
        '''
        state = self.__class__.__name__
        log.error("Unexpected {packet:7} packet received in {log_source}", packet="CONNACK")
        
    
    def handlePINGRESP(self):
        '''
        Handles PINGRESP packet from the server
        '''
        state = self.__class__.__name__
        log.error("Unexpected {packet:7} packet received in {log_source}", packet="PINGRESP")


    def handleSUBACK(self, response):
        '''
        Handles SUBACK packet from the server
        '''
        state = self.__class__.__name__
        log.error("Unexpected {packet:7} packet received in {log_source}", packet="SUBACK")


    def handleUNSUBACK(self, response):
        '''
        Decodes specific UNSUBACK data from Variable Header & Payload
        '''
        state = self.__class__.__name__
        log.error("Unexpected {packet:7} packet received in {log_source}", packet="UNSUBACK")


    def handlePUBLISH(self, response):
        '''
        Handles PUBLISH packet from the server
        '''
        state = self.__class__.__name__
        log.error("Unexpected {packet:7} packet received in {log_source}", packet="PUBLISH")


    def handlePUBACK(self, response):
        '''
        Handles PUBACK packet from the server
        '''
        state = self.__class__.__name__
        log.error("Unexpected {packet:7} packet received in {log_source}", packet="PUBACK")


    def handlePUBREC(self, response):
        '''
        Handles PUBREC packet from the server
        '''
        state = self.__class__.__name__
        log.error("Unexpected {packet:7} packet received in {log_source}", packet="PUBREC")

    def handlePUBREL(self, response):
        '''
        Handles PUBREL packet from the server
        '''
        state = self.__class__.__name__
        log.error("Unexpected {packet:7} packet received in {log_source}", packet="PUBREL")

    def handlePUBCOMP(self, response):
        '''
        Handles PUBCOMP packet from the server
        '''
        state = self.__class__.__name__
        log.error("Unexpected {packet:7} packet received in {log_source}", packet="PUBCOMP")


# ---------------------------------------
# Idle State Class
# ---------------------------------------

class IdleState(BaseState):

    def connect(self, request):
        return self.protocol.doConnect(request)

# ---------------------------------------
# Connecting State Class
# ---------------------------------------

class ConnectingState(BaseState):

    def handleCONNACK(self, response):
        self.protocol.handleCONNACK(response)

# ---------------------------------------
# Connected State Class
# ---------------------------------------

class ConnectedState(BaseState):


    def disconnect(self, request):
        '''
        Send a DISCONNECT packet.
        '''
        self.protocol.doDisconnect(request)


    def ping(self):
        '''
        Send a PINGREQ control packet.
        '''
        self.protocol.doPingRequest()


    def handlePINGRESP(self):
        '''
        Handles PINGRESP packet from the server
        '''
        self.protocol.handlePINGRESP()






# ------------------------
# MQTT Base Protocol Class
# ------------------------

@implementer(IMQTTClientControl)
class MQTTBaseProtocol(Protocol):
    '''
    Base Class, not meant to be directly instantiated.
    Handles all MQTT connection stuff
    '''
    
    # So that we can patch it in tests with Clock.callLater ...
    callLater = reactor.callLater

    packetTypes = {0x00: "null",    0x01: "CONNECT",     0x02: "CONNACK",
                   0x03: "PUBLISH", 0x04: "PUBACK",      0x05: "PUBREC",
                   0x06: "PUBREL",  0x07: "PUBCOMP",     0x08: "SUBSCRIBE",
                   0x09: "SUBACK",  0x0A: "UNSUBSCRIBE", 0x0B: "UNSUBACK",
                   0x0C: "PINGREQ", 0x0D: "PINGRESP",    0x0E: "DISCONNECT"}


    MAX_WINDOW          = 16   # Max value of in-flight PUBLISH/SUBSCRIBE/UNSUBSCRIBE
    TIMEOUT_INITIAL     = 4    # Initial tiemout for retransmissions
    TIMEOUT_MAX_INITIAL = 1024 # Maximun value for initial timeout

    def __init__(self, factory):
        self.IDLE        = IdleState(self)
        self.CONNECTING  = ConnectingState(self)
        self.CONNECTED   = ConnectedState(self)
        self.state       = self.IDLE
        self.factory     = factory
        self._initialT   = self.TIMEOUT_INITIAL # Initial timeout for retransmissions
        self._version    = v311 # default protocol version
        self._buffer     = bytearray()
        self._keepalive  = 0    # keepalive (in ms) disabled by default
        self._window     = 1    # Guarantees in-order delivery by default
        self._cleanStart = True # No session by default
        self._pingReq       = PINGREQ() 
        self._pingReq.timer = None
        self._pingReq.alarm = None
        self._pingReq.pdu   = self._pingReq.encode()    # reuses the same PDU over and over again
        self.onDisconnection = None # callback to be invoked

 # ------------------------------------------------------------------------

    def _accumulatePacket(self, data):
        self._buffer.extend(data)

        length = None

        while len(self._buffer):
            if length is None:
                # Start on a new packet

                # Haven't got enough data to start a new packet,
                # wait for some more
                if len(self._buffer) < 2:
                    break

                lenLen = 1
                # Calculate the length of the length field
                while lenLen < len(self._buffer):
                    if not self._buffer[lenLen] & 0x80:
                        break
                    lenLen += 1

                # We still haven't got all of the remaining length field
                if lenLen < len(self._buffer) and self._buffer[lenLen] & 0x80:
                    return

                length = decodeLength(self._buffer[1:])

            if len(self._buffer) >= length + lenLen + 1:
                chunk = self._buffer[:length + lenLen + 1]
                self._processPacket(chunk)
                self._buffer = self._buffer[length + lenLen + 1:]
                length = None

            else:
                break

 # ------------------------------------------------------------------------

    def _processPacket(self, packet):
        '''Generic MQTT packet decoder'''
        try:
            packet_type      = (packet[0] & 0xF0) >> 4
            packet_flags     = (packet[0] & 0x0F)
            packet_type_name = self.packetTypes[packet_type]
        except KeyError as e:
            # Invalid packet type, throw away this packet
            log.error("Invalid packet type %x" % packet_type)
            self.transport.abortConnection()
            return


        # Get the appropriate decoder function
        packetDecoder = getattr(self, "_handle%s" % packet_type_name, None)

        if packetDecoder:
            packetDecoder(packet)
        else:
            # No decoder
            log.error("Invalid packet decoder for %s" % packet_type_name)
            self.transport.abortConnection()
            return

    # -----------------------------
    # SPECIFIC MQTT PACKET DECODERS
    # -----------------------------

    def _handleCONNACK(self, packet):
        '''
        Decodes specific CONNACK data from Variable Header & Payload
        '''
        response = CONNACK()
        try:
            response.decode(packet)
        except Exception as e:
            log.debug("Exception {excp!r}.", excp=e)
            log.error("MQTT CONNACK PDU corrupt. Closing connection !")
            self.transport.abortConnection()
        else:
            self.state.handleCONNACK(response)

    # ------------------------------------------------------------------------

    def _handlePINGRESP(self, packet):
        '''
        Decodes specific PNGRESP data from Variable Header & Payload
        '''
        self.state.handlePINGRESP()           

    # ------------------------------------------------------------------------

    def _handleSUBACK(self, packet):
        '''
        Decodes specific SUBACK data from Variable Header & Payload
        '''
        response = SUBACK()
        try:
            response.decode(packet)
        except Exception as e:
            log.debug("Exception {excp!r}.", excp=e)
            log.error("MQTT SUBACK PDU corrupt. Closing connection !")
            self.transport.abortConnection()
        else:
            self.state.handleSUBACK(response)

    # ------------------------------------------------------------------------

    def _handleUNSUBACK(self, packet):
        '''
        Decodes specific UNSUBACK data from Variable Header & Payload
        '''
        response = UNSUBACK()
        try:
            response.decode(packet)
        except Exception as e:
            log.debug("Exception {excp!r}.", excp=e)
            log.error("MQTT UNSUBACK PDU corrupt. Closing connection !")
            self.transport.abortConnection()
        else:
            self.state.handleUNSUBACK(response)

    # ------------------------------------------------------------------------

    def _handlePUBLISH(self, packet):
        '''
        Decodes specific PUBLISH data from Flags, Variable Header & Payload
        '''
        response = PUBLISH()
        try:
            response.decode(packet)
        except Exception as e:
            log.debug("Exception {excp!r}.", excp=e)
            log.error("MQTT PUBLISH PDU corrupt. Closing connection !")
            self.transport.abortConnection()
        else:
            self.state.handlePUBLISH(response)

    # ------------------------------------------------------------------------

    def _handlePUBACK(self, packet):
        '''
        Decodes specific PUBACK data from Variable Header & Payload
        '''
        response = PUBACK()
        try:
            response.decode(packet)
        except Exception as e:
            log.debug("Exception {excp!r}.", excp=e)
            log.error("MQTT PUBACK PDU corrupt. Closing connection !")
            self.transport.abortConnection()
        else:
            self.state.handlePUBACK(response)

    # ------------------------------------------------------------------------

    def _handlePUBREL(self, packet):
        '''
        Decodes specific PUBREL data from Variable Header & Payload
        '''
        response = PUBREL()
        try:
            response.decode(packet)
        except Exception as e:
            log.debug("Exception {excp!r}.", excp=e)
            log.error("MQTT PUBREL PDU corrupt. Closing connection !")
            self.transport.abortConnection()
        else:
            self.state.handlePUBREL(response)

    # ------------------------------------------------------------------------

    def _handlePUBREC(self, packet):
        '''
        Decodes specific PUBREC data from Variable Header & Payload
        '''
        response = PUBREC()
        try:
            response.decode(packet)
        except Exception as e:
            log.debug("Exception {excp!r}.", excp=e)
            log.error("MQTT PUBREL PDU corrupt. Closing connection !")
            self.transport.abortConnection()
        else:
            self.state.handlePUBREC(response)

    # ------------------------------------------------------------------------

    def _handlePUBCOMP(self, packet):
        '''
        Decodes specific PUBCOMP data from Variable Header & Payload
        '''
        response = PUBCOMP()
        try:
            response.decode(packet)
        except Exception as e:
            log.debug("Exception {excp!r}.", excp=e)
            log.error("MQTT PUBCOMP PDU corrupt. Closing connection !")
            self.transport.abortConnection()
        self.state.handlePUBCOMP(response)

    # ------------------------------------------------------------------------

    # --------------------------
    # Twisted Protocol Interface
    # --------------------------

    def dataReceived(self, data):
        self._accumulatePacket(data)
    

    def connectionLost(self, reason):
        log.debug("--- Connection to MQTT Broker lost")
        if self._pingReq.timer:
            self._pingReq.timer.stop()
            self._pingReq.timer = None
        if self._pingReq.alarm:
            self._pingReq.alarm.cancel()
            self._pingReq.alarm = None
        self.doConnectionLost(reason)
        self.state = self.IDLE
        # The disconnect callback is invoked in another reactor loop cycle
        # Otherwise, the reconnection attempt happens before connection cleanup
        # which obviopusly it si not what we want.
        if self.onDisconnection:
            self.callLater(0.1, self.onDisconnection, reason)
        

    # ---------------------------------
    # IMQTTClientControl Implementation
    # ---------------------------------

    def connect(self, clientId, keepalive=0, willTopic=None,
                willMessage=None, willQoS=0, willRetain=False,
                username=None,password=None,cleanStart=True, version=v311):
        '''
        API Entry Point       
        '''
        request = CONNECT()
        request.clientId    = clientId
        request.keepalive   = keepalive
        request.willTopic   = willTopic
        request.willMessage = willMessage
        request.willQoS     = willQoS
        request.willRetain  = willRetain
        request.username    = username
        request.password    = password
        request.cleanStart  = cleanStart
        request.version     = version
        return self.state.connect(request)

    # ------------------------------------------------------------------------

    def disconnect(self):
        '''
        API Entry Point
        '''
        request = DISCONNECT()
        self.state.disconnect(request)

     # ------------------------------------------------------------------------

    def setTimeout(self, timeout):
        '''
        API Entry Point
        '''
        if not ( 1 <= timeout <= self.TIMEOUT_MAX_INITIAL ):
             raise TimeoutValueError(timeout)
        self._initialT = timeout

    # --------------------------------------------------------------------------

    def setWindowSize(self, n):
        '''
        API Entry Point
        '''
        if not (0 < n <= self.MAX_WINDOW):
            raise WindowValueError(n)
        self._window = min(n, self.MAX_WINDOW)

    # ------------------------------------------------------------------------

    def ping(self):
        '''
        Send a PINGREQ control packet
        The PINGREQ Packet is sent from a Client to the Server. 
        It can be used to:
        1. indicate to the Server that the Client is alive in the absence of 
        any other Control Packets being sent from the Client to the Server.
        2. Request that the Server responds to confirm that it is alive.
        3. Exercise the network to indicate that the Network Connection 
        is active.

         It is the responsibility of the Client to ensure that the interval 
        between Control Packets being sent does not exceed the Keep Alive value.
        In the absence of sending any other Control Packets, the Client MUST 
        send a PINGREQ Packet [MQTT-3.1.2-23].
        '''
        self.state.ping()

    # ------------------------------------------
    # Southbound interface: Network entry points
    # ------------------------------------------

    def handleCONNACK(self, response):
        '''
        Handles CONNACK packet from the server.

        The 8 bit unsigned value that represents the revision level of the 
        protocol used by the Client. The value of the Protocol Level field for
        the version 3.1.1 of the protocol is 4 (0x04). The Server MUST respond 
        to the CONNECT Packet with a CONNACK return code 0x01 (unacceptable 
        protocol level) and then disconnect the Client if the Protocol Level 
        is not supported by the Server [MQTT-3.1.2-2].

        The Keep Alive is a time interval measured in seconds. It is the 
        maximum time interval that is permitted to elapse between 
        the point at which the Client finishes transmitting one Control Packet 
        and the point it starts sending the next. A Keep Alive value of zero 
        (0) has the effect of turning off the keep alive mechanism.
        '''
        # Changes state and execute deferreds
        log.debug("<== {packet:7} (code={code} session={flags})", packet="CONNACK", code=response.resultCode, flags=response.session)
        request = self.connReq
        request.alarm.cancel()
        if response.resultCode == 0:
            self.state = self.CONNECTED
            self.mqttConnectionMade()   # before the callbacks are executed ...
            if request.keepalive != 0:
                self._pingReq.keepalive = request.keepalive
                self._pingReq.timer     = task.LoopingCall(self.ping)
                self._pingReq.timer.start(request.keepalive)
            request.deferred.callback(response.session)
        else:
            self.state = self.IDLE
            msg = MQTT_CONNECT_CODES[response.resultCode]
            request.deferred.errback(MQTTStateError(response.resultCode, msg))
        self.connReq = None     # to be garbage-collected
      
    # ------------------------------------------------------------------------
    
    def handlePINGRESP(self):
        '''
        Handles PINGRESP packet from the server
        '''
        log.debug("<== {packet:7}", packet="PINGRESP")
        self._pingReq.alarm.cancel()
        self._pingReq.alarm = None


    # ---------------------------
    # Protocol API for subclasses
    # ---------------------------

    def mqttConnectionMade(self):
        '''
        Called when a CONNACK has been received.
        Overriden in subscriber/publisher to do additional session sync
        '''
        pass

    # ---------------------------
    # State Machine API callbacks
    # ---------------------------

    def doDisconnect(self, request):
        '''
        Performs the actual work of disconnecting
        '''
        log.debug("==> {packet:7}",packet="DISCONNECT")
        self.transport.write(request.encode())
        self.transport.loseConnection()

    # ------------------------------------------------------------------------

    def doConnect(self, request):
        '''
        Performs the actual work of connecting
        '''
        def connectError():
            request.deferred.errback(MQTTTimeoutError("CONNACK"))
            request.deferred = None
            self.transport.abortConnection()            

        try:
            self._checkConnect(request)
            pdu = request.encode()
        except ValueError as e:
            return defer.fail(e)
        log.debug("==> {packet:7} (id={id} keepalive={keepalive} clean={clean})", packet="CONNECT", id=request.clientId, keepalive=request.keepalive, clean=request.cleanStart)
        self._cleanStart = request.cleanStart
        self._version    = request.version
        self.transport.write(pdu)
        # Changes state and returns deferred
        self.state = self.CONNECTING
        request.alarm = self.callLater(request.keepalive or 10, connectError)
        request.deferred = defer.Deferred()
        self.connReq = request  # keep track of this request until CONNACK or timeout
        return request.deferred

    # ------------------------------------------------------------------------

    def doPingRequest(self):
        '''
        Performs the actual work of sending PINGREQ packets
        '''
        def doPingError():
            log.warn("--- {packet:7} Timeout", packet="PINGREQ")
            self.transport.abortConnection()
        log.debug("==> {packet:7}", packet="PINGREQ")
        self.transport.write(self._pingReq.pdu)
        self._pingReq.alarm = self.callLater(self._pingReq.keepalive, doPingError)

    # ------------------------------------------------------------------------

    def doConnectionLost(self, reason):
        '''
        To be subclassed
        '''
        pass

    # --------------
    # Helper methods
    # --------------

    def _checkConnect(self, request):
        '''
        Assert connect parameters
        '''

        if not ( 0<= request.willQoS < 3):
            raise QoSValueError("last will", request.willQoS)
        if not ( 0 <= request.keepalive <= 65535):
            raise KeepaliveValueError(request.keepalive)
        if (request.version == v31) and len(request.clientId) > 23:
            raise ClientIdValueError("Client ID exceed 23 characters", request.clientId)
        if not (request.version == v31 or request.version == v311):
            raise ProtocolValueError("Incorrect protocol version", request.version)
        if request.willMessage is not None and request.willTopic is None:
            raise MissingTopicError("Last Will Topic")
        if request.willMessage is None and request.willTopic is not None:
            raise MissingPayloadError("Last Will Message")
        if request.username is None and request.password is not None:
            raise MissingUserError()

    # ------------------------------------------------------------------------


__all__ = ["MQTTBaseProtocol"]

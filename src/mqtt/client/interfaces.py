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
# Twisted  modules
# ----------------

import mqtt
from zope.interface import Interface, Attribute

# ============================================================================ #
#                MQTT Client Connection Control Interface                      #
# ============================================================================ #


class IMQTTClientControl(Interface):

    '''
    This interface defines operations to start,maintain and finish
    and MQTT connection, above the TCP layer
    '''

    
    def connect(clientId, keepalive=0, willTopic=None,
                willMessage=None, willQoS=0, willRetain=False, 
                username=None, password=None, cleanStart=True, version=mqtt.v311):
        '''
        Abstract
        ========

        Send a CONNECT control packet.

        Description
        ===========

        After a Network Connection is established by a Client to a Server, 
        the first Packet sent from the Client to the Server MUST be a CONNECT 
        Packet [MQTT-3.1.0-1].

        A Client can only send the CONNECT Packet once over a 
        Network Connection. The Server MUST process a second CONNECT Packet 
        sent from a Client as a protocol violation and disconnect the Client.

        If the Client does not receive a CONNACK Packet from the Server within
        a reasonable amount of time, he Client SHOULD close the Network 
        Connection. A "reasonable" amount of time depends on the type of 
        application and the communications infrastructure.

        Signature
        =========

        @param clientId: client ID for the connection (UTF-8 string)
        @param keepalive: connection keepalive period in seconds.
        @param willTopic:   last will topic  (UTF-8 string)
        @param willMessage: last will message  (UTF-8 string)
        @param willQoS:     last will qos message
        @param willRetain:  lass will retain flag.
        @param cleanStart:  session clean flag.
        @return: a Deferred whose callback will be called with a tuple
            C{returnCode, sessionFlag)} when the connection completes. 
            The Deferred errback with a C{MQTTError} exception will be called 
            if no connection ack is received from the server within a keepalive
            period. If no keepalive is used, a max of 10 seconds is used.
        '''

    def disconnect():
        '''
        Abstract
        ========

        Send a DISCONNECT packet and disconenct the transport.

        Description
        ===========

        The DISCONNECT Packet is the final Control Packet sent from 
        the Client to the Server. It indicates that the Client is 
        disconnecting cleanly. This operation is synchronous since we 
        do not expect a response from the server. A disconnect confirmation
        can be obtained through the *disconnect indication callback* below.

        Signature
        =========

        @return: Nothing.
        '''

    onDisconnection = Attribute("""
        @type onDisconnection: C{function or bounded method}
        @ivar onDisconnection: handler that will be invoked  if the Protocol loses the connection and no pending deferred remains 
        to invoke its errbacks. This is the only way for clients to be notified of such situation.
    """)

    onMqttConnectionMade = Attribute("""
        @type onMqttConnectionMade: C{function or bounded method}
        @ivar onMqttConnectionMade: handler that will be invoked before the deferreds for special cases
        (to be yet confirmed) before the connection deferred is fired.
    """)



    def setTimeout(timeout):
        '''
        Abstract
        ========

        Sets the initial timeout value for retries.

        Description
        ===========

        Set the initial timeout value for retries in PUBLISH, SUBSCRIBE, UNSUBCRIBE,
        & PUBREL control value. Retries for SUBSCRIBE, UNSUBCRIBE,
        & PUBREL will be done with exponentially backoff timeout value up to a limit. 
        Retries for PUBLISH will take into account estimated banwidth (see IPublisher)

        Signature
        =========

        @param timeout: timeout value in seconds.
        @raise ValueError: if not within [1..TIMEOUT_MAX_INITIAL]
        '''

    def setWindowSize(n):
        '''
        Abstract
        =======

        Set Acknowledge window size. 

        Description
        ===========

        Specifies the maximum number of simultaneous C{subscribe()} and
        C{unssubscribe()} requests that can be issued before waiting for
        acknowledge packets. 'n' can be limited to an internal maximun size
        (implementation defined).

        To guarantee an in-order delivery of messages for messages with QoS > 0, 
        only one ACK should be pending (n=1). 
        By default, the ack window size is n=1 unless changed by this function.

        Signature
        =========

        @param n: window size
        @raise ValueError: if not within [1..MQTTBaseProtocol.MAX_WINDOW]

        '''

# ============================================================================ #
#                      MQTT Client Subscriber Interface                        #
# ============================================================================ #

class IMQTTSubscriber(Interface):
    '''
    This interface defines the operations necessary for  a 
    pure subscriber MQTT client.
    '''

    def subscribe(topicList):
        '''
        Abstract
        ========

        Send a SUBSCRIBE control packet.
        
        Description
        ===========

        The SUBSCRIBE Packet is sent from the Client to the Server to create 
        one or more Subscriptions. Each Subscription registers a Client's 
        interest in one or more Topics.

        Signature
        =========

        @param topicList: list of tuples C{(topic, QoS)}. Each topic is
            an UTF-8 string. 0 <= QoS <= 3
        @return: a Deferred, with an extra C{msgId} attribute which you can 
            use to keep track of requests. 
            The callbacks will be invoked with a list of granted tuples (granted qos, failure flag)
            where False in the failure flag means operation Ok)
        '''

    def unsubscribe(topic):
        '''
        Abstract
        ========

        Send an UNSUBSCRIBE control packet

        Description
        ===========

        An UNSUBSCRIBE Packet is sent by the Client to the Server, 
        to unsubscribe from topics.

        Signature
        =========
        @param topic: is either a single string or a list of strings 
            [topic1, topic2, topic3,]
        @return: a Deferred, with an extra C{msgId} attribute which you can 
            use to keep track of requests. 
            The callbacks will be invoked with the msgId as parameter.
        '''


    onPublish = Attribute("""
        @type onPublish: C{function or bounded method}
        @ivar onPublish: handler that will be invoked whenever a PUBLISH message arrive.
        with parameters (topic, payload, qos, dup, retain, msgId).
    """)

    


# ============================================================================ #
#                     MQTT Client Publisher Interface                          #
# ============================================================================ #

class IMQTTPublisher(Interface):
    '''
    This interface defines the operations necessary for  a 
    pure publisher MQTT client.
    '''

    def setBandwith(bandwith, factor = 2):
        '''
        Abstract
        ========

        Set the estimate available bandwith.

         Description
        ===========

        Set the estimate available bandwith to produce timeouts proportional 
        to the payload size, according to the formula:
        T = initial + (K * payload_size)/bandwith
             where K = K*factor in each iteration
        This is useful to avoid timeouts and retransmissions in very 
        large payloads using QoS=1 and 2. 
        '''
        
    def publish(topic, message, qos=0, retain=False):
        '''

        Abstract
        ========

        Send PUBLISH control packet

        Description
        ===========
        
        Publish a message with a give QoS [0..2], returning a deferred.
        The cleanStart flag in the C{connect} API has an impact on when the
        errback is called. When cleanStart = False, 
         1) a disconenction will not cause the errback to be fired.
         2) a disconnection will not purge pending publish messages in the internal queues.

        Signature
        =========

        @param topic: an UTF-8 string describing the topic on which to publish.
        @param message: a bytearray() with the application message
        @param qos: Desired Qos to publish the message to the server [0..3].
        @param retain: Retain Flag.
        @return: a Deferred, with an extra C{msgId} attribute which you can 
            use to keep track of requests. 
            The callback is called upon successful confirm and will include
            the msgId as parameter.
        '''

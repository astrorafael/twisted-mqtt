
twsited-mqtt
============

MQTT Client protocol for Twisted.

Description
-----------

**twsited-mqtt** is a library using the Twisted framework and implementing
the MQTT protocol (v3.1 & v3.1.1) in these flavours:

* pure subscriber
* pure publisher
* or a mixing of both

Instalation
-----------

Just type:

  `sudo pip install twisted-mqtt`


Credits
-------

I started writting this software after finding [Adam Rudd's MQTT.py code](https://github.com/adamvr/MQTT-For-Twisted-Python). 
Some parts of this library still has hos code. However, I soon began taking my
own direction both in design and scope.

Function/methods docstrings contain quotes of the OASIS [mqtt-v3.1.1](http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html) standard.

MQTT Version 3.1.1. Edited by Andrew Banks and Rahul Gupta. 29 October 2014. OASIS Standard. 
http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html. 
Latest version: http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html.

Usage
-----

The APIs are described in the [library defined interfaces](mqtt/client/interfaces.py)

This library builds `MQTTProtocol` objects and is designed to be *used rather than inherited*.


### Publisher Example ###

    from twisted.logger import Logger, LogLevel
    from twisted.internet import reactor, task
    from twisted.application.service import Service
    from twisted.internet.endpoints import TCP4ClientEndpoint
    
    from mqtt.client.factory import MQTTFactory
    from mqtt.logger import startLogging
    from mqtt import v31
    
    
    class MyService(Service):
    
        def gotProtocol(self, p):
            self.protocol = p
            d = p.connect("TwistedMQTT-pub", keepalive=0, version=v31)
            d.addCallbacks(self.prepareToPublish, self.printError)
            
        def prepareToPublish(self, *args):
            self.task = task.LoopingCall(self.publish)
            self.task.start(5.0)
    
        def publish(self):
            d = self.protocol.publish(topic="foo/bar/baz1", qos=0, message="hello world 0")
            d = self.protocol.publish(topic="foo/bar/baz2", qos=1, message="hello world 1")
            d = self.protocol.publish(topic="foo/bar/baz3", qos=2, message="hello world 2")
            d.addErrback(self.printError)
    
       def printError(self, *args):
            log.debug("args={args!s}", args=args)
            reactor.stop()
    
    
    if __name__ == '__main__':
        import sys
        log = Logger()
        startLogging(sys.stdout, LogLevel.debug)
    
        factory = MQTTFactory(profile=MQTTFactory.PUBLISHER)
        point   = TCP4ClientEndpoint(reactor, "test.mosquitto.org", 1883)
        serv    = MyService()
    
        d = point.connect(factory)
        d.addCallback(serv.gotProtocol)
    
        reactor.run()


### Subscriber Example ###

    from twisted.logger import Logger, LogLevel
    from twisted.internet import reactor
    from twisted.application.service import Service
    from twisted.internet.endpoints import TCP4ClientEndpoint
    
    from mqtt.client.factory import MQTTFactory
    from mqtt.logger import startLogging
    
    class MyService(Service):
    
        def gotProtocol(self, p):
            self.protocol = p
            d = p.connect("TwistedMQTT-subs", keepalive=0)
            d.addCallback(self.subscribe)
    
        def subscribe(self, *args):
            d = self.protocol.subscribe("foo/bar/baz1", 2 )
            d.addCallback(self.grantedQoS)
            d = self.protocol.subscribe("foo/bar/baz2", 2 )
            d.addCallback(self.grantedQoS)
            d = self.protocol.subscribe("foo/bar/baz3", 2 )
            d.addCallback(self.grantedQoS)
            self.protocol.setPublishHandler(self.onPublish)
    
        def onPublish(self, topic, payload, qos, dup, retain, msgId):
           log.debug("topic = {topic}, msg={payload} qos = {qos}, dup ={dup} retain={retain}, msgId={id}", topic=topic, payload=payload, 
                qos=qos, dup=dup, retain=retain, id=msgId)
    
        def grantedQoS(self, *args):
            log.debug("args={args!r}", args=args)
    
    
    if __name__ == '__main__':
        import sys
        log = Logger()
        startLogging(sys.stdout, LogLevel.debug)
    
        factory = MQTTFactory(profile=MQTTFactory.SUBSCRIBER)
        point   = TCP4ClientEndpoint(reactor, "test.mosquitto.org", 1883)
        serv    = MyService()
    
        d = point.connect(factory).addCallback(serv.gotProtocol)
        reactor.run()


### Publisher/Subscriber Example ###
    
    from twisted.logger import Logger, LogLevel
    from twisted.internet import reactor, task
    from twisted.application.service import Service
    from twisted.internet.endpoints import TCP4ClientEndpoint
    
    from mqtt.client.factory import MQTTFactory
    from mqtt.logger import startLogging
    
    log = Logger()
    
    
    class MyService(Service):
    
        def gotProtocol(self, p):
            self.protocol = p
            d = p.connect("TwistedMQTT-pubsubs", keepalive=0)
            d.addCallback(self.subscribe)
            d.addCallback(self.prepareToPublish)
    
        def subscribe(self, *args):
            d = self.protocol.subscribe("foo/bar/baz", 0 )
            self.protocol.setPublishHandler(self.onPublish)
    
        def onPublish(self, topic, payload, qos, dup, retain, msgId):
           log.debug("topic = {topic}, msg={payload} qos = {qos}, dup ={dup} retain={retain}, msgId={id}", topic=topic, payload=payload, 
                qos=qos, dup=dup, retain=retain, id=msgId)
    
        def prepareToPublish(self, *args):
            self.task = task.LoopingCall(self.publish)
            self.task.start(5.0)
    
        def publish(self):
            d = self.protocol.publish(topic="foo/bar/baz", message="hello friends")
            d.addErrback(self.printError)
    
        def printError(self, *args):
            log.debug("args={args!s}", args=args)
            reactor.stop()
    
    
    if __name__ == '__main__':
        import sys
        log = Logger()
        startLogging(sys.stdout, LogLevel.debug)
    
        factory = MQTTFactory(profile=MQTTFactory.PUBLISHER | MQTTFactory.SUBSCRIBER)
        point   = TCP4ClientEndpoint(reactor, "test.mosquitto.org", 1883)
        serv    = MyService()
    
        d = point.connect(factory).addCallback(serv.gotProtocol)
        reactor.run()
    
    
Design Notes
------------

There is a separate `MQTTProtocol` in each module implementing a different profile (subscriber, publiser, publisher/subscriber).
The `MQTTBaseProtocol` and the various `MQTTProtocol` classes implement a State Pattern to avoid the "if spaghetti code" in the 
connection states. A basic state machine is built into the `MQTTBaseProtocol` and the `ConnectedState` is patched according to
the profile.

The publisher/subscriber is a mixin class implemented by delegation. The composite manage connection state and forwards all
client requests and network events to the proper delegate. The trick is that the connection state must be shared
between all protocol instances, using class variables. 
Also, the transport is shared with the delegates so that they can write as if they were not in a container.

Limitations
-----------

The current implementation has the following limitations:

* This library does not claim to be full comformant to the standard. 

* There is a limited form of session persistance for the publisher. Pending acknowledges for PUBLISH
  and PUBREL are kept in RAM and outlive the connection and the protocol object while Twisted is running. 
  However, they are not stored in a persistent medium.

For the time being, I consider this library to be in *Alpha* state.

TODO
----

I wrote this library for my pet projects and learn Twsited. 
However, it goes a long way from an apparently looking good library
to an industrial-strength, polished product. I don't simply have the time, 
energy and knowledge to do so. 

Some areas in which this can be improved:

* Include a thorough test battery.
* Improve documentation.
* etc.


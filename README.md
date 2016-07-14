
twisted-mqtt
============

MQTT Client protocol for Twisted.

Description
-----------

**twisted-mqtt** is a library using the Twisted framework and implementing
the MQTT protocol (v3.1 & v3.1.1) in these flavours:

* pure subscriber
* pure publisher
* or a mixing of both. This is useful to subscribe and publish through the same broker using only one TCP connection.

Instalation
-----------

Just type:

  `sudo pip install twisted-mqtt`

or from GitHub:

	git clone https://github.com/astrorafael/twisted-mqtt.git
	cd twisted-mqtt
	sudo python setup.py install

Change Log
----------

* Version 0.2.1 was a major internal refactoring of the publish,  subscribe and pubsubs roles over 0.1.6.
* Version 0.2.3 is backwards compatible with 0.2.1, with three enhancements:
    - Persistent ***per-connection state*** (Pending Publish & Subscription ACKs). Verion 0.2.1 cannot be used with two simultaneous, different MQTT broker connections.
    - Internal queue to hold PUBLISH requests beyond the window size.
    - Adaptive timeouts depending on PUBLISH PDU size and a bandwith estimate. New protocol API function `setBandwith()`. This will avoid dupicate payloads using QoS 1 and 2.


Credits
-------

I started writting this software after finding [Adam Rudd's MQTT.py code](https://github.com/adamvr/MQTT-For-Twisted-Python). 
A small part his code is still there. However, I soon began taking my
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

```
import sys

from twisted.internet import reactor, task
from twisted.application.internet import ClientService
from twisted.internet.endpoints   import clientFromString
from twisted.logger   import (
    Logger, LogLevel, globalLogBeginner, textFileLogObserver, 
    FilteringLogObserver, LogLevelFilterPredicate)

from mqtt.client.factory import MQTTFactory
from mqtt import v31


# ----------------
# Global variables
# ----------------

# Global object to control globally namespace logging
logLevelFilterPredicate = LogLevelFilterPredicate(defaultLogLevel=LogLevel.info)

# -----------------
# Utility Functions
# -----------------

def startLogging(console=True, filepath=None):
    '''
    Starts the global Twisted logger subsystem with maybe
    stdout and/or a file specified in the config file
    '''
    global logLevelFilterPredicate
   
    observers = []
    if console:
        observers.append( FilteringLogObserver(observer=textFileLogObserver(sys.stdout),  
            predicates=[logLevelFilterPredicate] ))
    
    if filepath is not None and filepath != "":
        observers.append( FilteringLogObserver(observer=textFileLogObserver(open(filepath,'a')), 
            predicates=[logLevelFilterPredicate] ))
    globalLogBeginner.beginLoggingTo(observers)


def setLogLevel(namespace=None, levelStr='info'):
    '''
    Set a new log level for a given namespace
    LevelStr is: 'critical', 'error', 'warn', 'info', 'debug'
    '''
    level = LogLevel.levelWithName(levelStr)
    logLevelFilterPredicate.setLogLevelForNamespace(namespace=namespace, level=level)

class MyService(ClientService):

    def gotProtocol(self, p):
        self.protocol = p
        d = p.connect("TwistedMQTT-pub", keepalive=0, version=v31)
        d.addCallbacks(self.prepareToPublish, self.printError)
        
    def prepareToPublish(self, *args):
        # We are issuing 3 publish in a row
        # if order matters, then set window size to 1
        # Publish requests beyond window size are enqueued
        self.protocol.setWindowSize(3) 
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
    startLogging()
    setLogLevel(namespace='mqtt',     levelStr='debug')
    setLogLevel(namespace='__main__', levelStr='debug')

    factory    = MQTTFactory(profile=MQTTFactory.PUBLISHER)
    myEndpoint = clientFromString(reactor, "tcp:test.mosquitto.org:1883")
    serv       = MyService(myEndpoint, factory)
    serv.whenConnected().addCallback(serv.gotProtocol)
    serv.startService()
    reactor.run()

```

### Subscriber Example ###

```
import sys

from twisted.internet import reactor
from twisted.application.internet import ClientService
from twisted.internet.endpoints   import clientFromString
from twisted.logger   import (
    Logger, LogLevel, globalLogBeginner, textFileLogObserver, 
    FilteringLogObserver, LogLevelFilterPredicate)

from mqtt.client.factory import MQTTFactory

# ----------------
# Global variables
# ----------------

# Global object to control globally namespace logging
logLevelFilterPredicate = LogLevelFilterPredicate(defaultLogLevel=LogLevel.info)

# -----------------
# Utility Functions
# -----------------

def startLogging(console=True, filepath=None):
    '''
    Starts the global Twisted logger subsystem with maybe
    stdout and/or a file specified in the config file
    '''
    global logLevelFilterPredicate
   
    observers = []
    if console:
        observers.append( FilteringLogObserver(observer=textFileLogObserver(sys.stdout),  
            predicates=[logLevelFilterPredicate] ))
    
    if filepath is not None and filepath != "":
        observers.append( FilteringLogObserver(observer=textFileLogObserver(open(filepath,'a')), 
            predicates=[logLevelFilterPredicate] ))
    globalLogBeginner.beginLoggingTo(observers)


def setLogLevel(namespace=None, levelStr='info'):
    '''
    Set a new log level for a given namespace
    LevelStr is: 'critical', 'error', 'warn', 'info', 'debug'
    '''
    level = LogLevel.levelWithName(levelStr)
    logLevelFilterPredicate.setLogLevelForNamespace(namespace=namespace, level=level)


class MyService(ClientService):

    def gotProtocol(self, p):
        self.protocol = p
        d = p.connect("TwistedMQTT-subs", keepalive=0)
        d.addCallback(self.subscribe)
        # We are issuing 3 subscriptions in a row
        # Subscription requests beyond window size 
        # invoke errback with MQTTWindowError exception
        self.protocol.setWindowSize(3) 

    def subscribe(self, *args):
        d = self.protocol.subscribe("foo/bar/baz1", 2 )
        d.addCallback(self.grantedQoS)
        d = self.protocol.subscribe("foo/bar/baz2", 2 )
        d.addCallback(self.grantedQoS)
        d = self.protocol.subscribe("foo/bar/baz3", 2 )
        d.addCallback(self.grantedQoS)
        self.protocol.setPublishHandler(self.onPublish)

    def onPublish(self, topic, payload, qos, dup, retain, msgId):
       log.debug("msg={payload}", payload=payload)

    def grantedQoS(self, *args):
        log.debug("args={args!r}", args=args)


if __name__ == '__main__':
    import sys
    log = Logger()
    startLogging()
    setLogLevel(namespace='mqtt',     levelStr='debug')
    setLogLevel(namespace='__main__', levelStr='debug')


    factory    = MQTTFactory(profile=MQTTFactory.SUBSCRIBER)
    myEndpoint = clientFromString(reactor, "tcp:test.mosquitto.org:1883")
    serv       = MyService(myEndpoint, factory)
    serv.whenConnected().addCallback(serv.gotProtocol)
    serv.startService()
    reactor.run()
```


### Publisher/Subscriber Example ###
```
import sys

from twisted.internet import reactor, task
from twisted.application.internet import ClientService
from twisted.internet.endpoints   import clientFromString
from twisted.logger   import (
    Logger, LogLevel, globalLogBeginner, textFileLogObserver, 
    FilteringLogObserver, LogLevelFilterPredicate)

from mqtt.client.factory import MQTTFactory

# ----------------
# Global variables
# ----------------

# Global object to control globally namespace logging
logLevelFilterPredicate = LogLevelFilterPredicate(defaultLogLevel=LogLevel.info)

# -----------------
# Utility Functions
# -----------------

def startLogging(console=True, filepath=None):
    '''
    Starts the global Twisted logger subsystem with maybe
    stdout and/or a file specified in the config file
    '''
    global logLevelFilterPredicate
   
    observers = []
    if console:
        observers.append( FilteringLogObserver(observer=textFileLogObserver(sys.stdout),  
            predicates=[logLevelFilterPredicate] ))
    
    if filepath is not None and filepath != "":
        observers.append( FilteringLogObserver(observer=textFileLogObserver(open(filepath,'a')), 
            predicates=[logLevelFilterPredicate] ))
    globalLogBeginner.beginLoggingTo(observers)


def setLogLevel(namespace=None, levelStr='info'):
    '''
    Set a new log level for a given namespace
    LevelStr is: 'critical', 'error', 'warn', 'info', 'debug'
    '''
    level = LogLevel.levelWithName(levelStr)
    logLevelFilterPredicate.setLogLevelForNamespace(namespace=namespace, level=level)


class MyService(ClientService):

    def gotProtocol(self, p):
        self.protocol = p
        d = p.connect("TwistedMQTT-pubsubs", keepalive=0)
        d.addCallback(self.subscribe)
        d.addCallback(self.prepareToPublish)

    def subscribe(self, *args):
        d = self.protocol.subscribe("foo/bar/baz", 0 )
        self.protocol.setPublishHandler(self.onPublish)

    def onPublish(self, topic, payload, qos, dup, retain, msgId):
       log.debug("msg={payload}", payload=payload)

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
    startLogging()
    setLogLevel(namespace='mqtt',     levelStr='debug')
    setLogLevel(namespace='__main__', levelStr='debug')

    factory    = MQTTFactory(profile=MQTTFactory.PUBLISHER | MQTTFactory.SUBSCRIBER)
    myEndpoint = clientFromString(reactor, "tcp:test.mosquitto.org:1883")
    serv       = MyService(myEndpoint, factory)
    serv.whenConnected().addCallback(serv.gotProtocol)
    serv.startService()
    reactor.run()

```
	
	
Design Notes
------------

There is a separate `MQTTProtocol` in each module implementing a different profile (subscriber, publiser, publisher/subscriber).
The `MQTTBaseProtocol` and the various `MQTTProtocol` classes implement a State Pattern to avoid the "if spaghetti code" in the connection states. A basic state machine is built into the `MQTTBaseProtocol` and the `ConnectedState` is patched according to the profile.

Previous 0.1.x implementations used two separate (subclases, publisher) and  with separate logic for both roles. The publisher/subscriber was a mixin class implemented by delegation that managed the connection state and forwarded all client requests and network events to the proper delegate. 

However, this approach had some quirks and issues with sharing state. It has been re-written to a single publisher/subscriber class that manages everything. 

To maintain the former API, separate subclasses has been derived to implement a pure subscriber or publisher roles. The subclassing simply patches the state machine in order to honor only the methods for a given role.

Limitations
-----------

The current implementation has the following limitations:

* This library does not claim to be full comformant to the standard. 

* There is a limited form of session persistance for the publisher. Pending acknowledges for PUBLISH and PUBREL are kept in RAM and outlive the connection and the protocol object while Twisted is running. However, they are not stored in a persistent medium.

For the time being, I consider this library to be in *Alpha* state.

TODO
----

I wrote this library for my pet projects and learn Twisted. 
However, it goes a long way from an apparently looking good library
to an industrial-strength, polished product. I don't simply have the time, 
energy and knowledge to do so. 

Some areas in which this can be improved:

* Include a thorough test battery.
* Improve documentation.
* etc.


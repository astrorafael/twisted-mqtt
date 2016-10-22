
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

```python
import sys

from twisted.internet             import reactor, task
from twisted.internet.defer       import inlineCallbacks, DeferredList
from twisted.application.internet import ClientService, backoffPolicy
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

BROKER = "tcp:test.mosquitto.org:1883"

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


# -----------------------
# MQTT Publishing Service
# -----------------------

class MyService(ClientService):

    def __init(self, endpoint, factory):
        ClientService.__init__(self, endpoint, factory, retryPolicy=backoffPolicy())


    def startService(self):
        log.info("starting MQTT Client Publisher Service")
        # invoke whenConnected() inherited method
        self.whenConnected().addCallback(self.connectToBroker)
        ClientService.startService(self)


    @inlineCallbacks
    def connectToBroker(self, protocol):
        '''
        Connect to MQTT broker
        '''
        self.protocol                 = protocol
        self.protocol.onDisconnection = self.onDisconnection
        # We are issuing 3 publish in a row
        # if order matters, then set window size to 1
        # Publish requests beyond window size are enqueued
        self.protocol.setWindowSize(3) 
        self.task = task.LoopingCall(self.publish)
        self.task.start(5.0)
        try:
            yield self.protocol.connect("TwistedMQTT-pub", keepalive=60)
        except Exception as e:
            log.error("Connecting to {broker} raised {excp!s}", 
               broker=BROKER, excp=e)
        else:
            log.info("Connected and subscribed to {broker}", broker=BROKER)


    def onDisconnection(self, reason):
        '''
        get notfied of disconnections
        and get a deferred for a new protocol object (next retry)
        '''
        log.debug(" >< Connection was lost ! ><, reason={r}", r=reason)
        self.whenConnected().addCallback(self.connectToBroker)


    def publish(self):
        

        def _logFailure(failure):
            log.debug("reported {message}", message=failure.getErrorMessage())
            return failure

        def _logAll(*args):
            log.debug("all publihing complete args={args!r}",args=args)

        log.debug(" >< Starting one round of publishing >< ")
        d1 = self.protocol.publish(topic="foo/bar/baz1", qos=0, message="hello world 0")
        d1.addErrback(_logFailure)
        d2 = self.protocol.publish(topic="foo/bar/baz2", qos=1, message="hello world 1")
        d2.addErrback(_logFailure)
        d3 = self.protocol.publish(topic="foo/bar/baz3", qos=2, message="hello world 2")
        d3.addErrback(_logFailure)
        dlist = DeferredList([d1,d2,d3], consumeErrors=True)
        dlist.addCallback(_logAll)
        return dlist



if __name__ == '__main__':
    import sys
    log = Logger()
    startLogging()
    setLogLevel(namespace='mqtt',     levelStr='debug')
    setLogLevel(namespace='__main__', levelStr='debug')

    factory    = MQTTFactory(profile=MQTTFactory.PUBLISHER)
    myEndpoint = clientFromString(reactor, BROKER)
    serv       = MyService(myEndpoint, factory)
    serv.startService()
    reactor.run()
```

### Subscriber Example ###

```python
import sys

from twisted.internet.defer       import inlineCallbacks, DeferredList
from twisted.internet             import reactor
from twisted.internet.endpoints   import clientFromString
from twisted.application.internet import ClientService, backoffPolicy

from twisted.logger   import (
    Logger, LogLevel, globalLogBeginner, textFileLogObserver, 
    FilteringLogObserver, LogLevelFilterPredicate)

from mqtt.client.factory import MQTTFactory

# ----------------
# Global variables
# ----------------

# Global object to control globally namespace logging
logLevelFilterPredicate = LogLevelFilterPredicate(defaultLogLevel=LogLevel.info)

BROKER = "tcp:test.mosquitto.org:1883"

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

# -----------------------
# MQTT Subscriber Service
# ------------------------

class MyService(ClientService):


    def __init(self, endpoint, factory):
        ClientService.__init__(self, endpoint, factory, retryPolicy=backoffPolicy())


    def startService(self):
        log.info("starting MQTT Client Subscriber Service")
        # invoke whenConnected() inherited method
        self.whenConnected().addCallback(self.connectToBroker)
        ClientService.startService(self)


    @inlineCallbacks
    def connectToBroker(self, protocol):
        '''
        Connect to MQTT broker
        '''
        self.protocol                 = protocol
        self.protocol.onPublish       = self.onPublish
        self.protocol.onDisconnection = self.onDisconnection
        self.protocol.setWindowSize(3) 
        try:
            yield self.protocol.connect("TwistedMQTT-subs", keepalive=60)
            yield self.subscribe()
        except Exception as e:
            log.error("Connecting to {broker} raised {excp!s}", 
               broker=BROKER, excp=e)
        else:
            log.info("Connected and subscribed to {broker}", broker=BROKER)


    def subscribe(self):

        def _logFailure(failure):
            log.debug("reported {message}", message=failure.getErrorMessage())
            return failure

        def _logGrantedQoS(value):
            log.debug("response {value!r}", value=value)
            return True

        def _logAll(*args):
            log.debug("all subscriptions complete args={args!r}",args=args)

        d1 = self.protocol.subscribe("foo/bar/baz1", 2 )
        d1.addCallbacks(_logGrantedQoS, _logFailure)

        d2 = self.protocol.subscribe("foo/bar/baz2", 2 )
        d2.addCallbacks(_logGrantedQoS, _logFailure)

        d3 = self.protocol.subscribe("foo/bar/baz3", 2 )
        d3.addCallbacks(_logGrantedQoS, _logFailure)

        dlist = DeferredList([d1,d2,d3], consumeErrors=True)
        dlist.addCallback(_logAll)
        return dlist


    def onPublish(self, topic, payload, qos, dup, retain, msgId):
        '''
        Callback Receiving messages from publisher
        '''
        log.debug("msg={payload}", payload=payload)


    def onDisconnection(self, reason):
        '''
        get notfied of disconnections
        and get a deferred for a new protocol object (next retry)
        '''
        log.debug(" >< Connection was lost ! ><, reason={r}", r=reason)
        self.whenConnected().addCallback(self.connectToBroker)


if __name__ == '__main__':
    import sys
    log = Logger()
    startLogging()
    setLogLevel(namespace='mqtt',     levelStr='debug')
    setLogLevel(namespace='__main__', levelStr='debug')

    factory    = MQTTFactory(profile=MQTTFactory.SUBSCRIBER)
    myEndpoint = clientFromString(reactor, BROKER)
    serv       = MyService(myEndpoint, factory)
    serv.startService()
    reactor.run()
```


### Publisher/Subscriber Example ###
```python
import sys

from twisted.internet.defer       import inlineCallbacks, DeferredList
from twisted.internet             import reactor
from twisted.internet.endpoints   import clientFromString
from twisted.application.internet import ClientService, backoffPolicy

from twisted.logger   import (
    Logger, LogLevel, globalLogBeginner, textFileLogObserver, 
    FilteringLogObserver, LogLevelFilterPredicate)

from mqtt.client.factory import MQTTFactory

# ----------------
# Global variables
# ----------------

# Global object to control globally namespace logging
logLevelFilterPredicate = LogLevelFilterPredicate(defaultLogLevel=LogLevel.info)

BROKER = "tcp:test.mosquitto.org:1883"

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

# -----------------------
# MQTT Subscriber Service
# ------------------------

class MyService(ClientService):


    def __init(self, endpoint, factory):
        ClientService.__init__(self, endpoint, factory, retryPolicy=backoffPolicy())


    def startService(self):
        log.info("starting MQTT Client Subscriber Service")
        # invoke whenConnected() inherited method
        self.whenConnected().addCallback(self.connectToBroker)
        ClientService.startService(self)


    @inlineCallbacks
    def connectToBroker(self, protocol):
        '''
        Connect to MQTT broker
        '''
        self.protocol                 = protocol
        self.protocol.onPublish       = self.onPublish
        self.protocol.onDisconnection = self.onDisconnection
        self.protocol.setWindowSize(3)
        self.task = task.LoopingCall(self.publish)
        self.task.start(5.0) 
        try:
            yield self.protocol.connect("TwistedMQTT-pubsubs", keepalive=60)
            yield self.subscribe()
        except Exception as e:
            log.error("Connecting to {broker} raised {excp!s}", 
               broker=BROKER, excp=e)
        else:
            log.info("Connected and subscribed to {broker}", broker=BROKER)


    def publish(self):

        def _logFailure(failure):
            log.debug("publisher reported {message}", message=failure.getErrorMessage())
            return failure

        d1 = self.protocol.publish(topic="foo/bar/baz1", qos=1, message="hello world 1")
        d1.addErrback(_logFailure)       
        return d1


    def subscribe(self):

        def _logFailure(failure):
            log.debug("subscriber reported {message}", message=failure.getErrorMessage())
            return failure

        def _logGrantedQoS(value):
            log.debug("subscriber response {value!r}", value=value)
            return True

        d1 = self.protocol.subscribe("foo/bar/baz1", 2)
        d1.addCallbacks(_logGrantedQoS, _logFailure)      
        return d1


    def onPublish(self, topic, payload, qos, dup, retain, msgId):
        '''
        Callback Receiving messages from publisher
        '''
        log.debug("msg={payload}", payload=payload)


    def onDisconnection(self, reason):
        '''
        get notfied of disconnections
        and get a deferred for a new protocol object (next retry)
        '''
        log.debug(" >< Connection was lost ! ><, reason={r}", r=reason)
        self.whenConnected().addCallback(self.connectToBroker)


if __name__ == '__main__':
    import sys
    log = Logger()
    startLogging()
    setLogLevel(namespace='mqtt',     levelStr='debug')
    setLogLevel(namespace='__main__', levelStr='debug')
    factory    = MQTTFactory(profile=MQTTFactory.PUBLISHER | MQTTFactory.SUBSCRIBER)
    myEndpoint = clientFromString(reactor, BROKER)
    serv       = MyService(myEndpoint, factory)
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

* Bug fixing 
* Include a thorough test battery.
* Improve documentation.
* etc.


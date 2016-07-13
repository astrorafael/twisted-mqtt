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
    
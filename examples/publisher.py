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

class MQTTService(ClientService):

    def __init__(self, endpoint, factory):
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
        self.task.start(5.0, now=False)
        try:
            yield self.protocol.connect("TwistedMQTT-pub", keepalive=60)
        except Exception as e:
            log.error("Connecting to {broker} raised {excp!s}", 
               broker=BROKER, excp=e)
        else:
            log.info("Connected to {broker}", broker=BROKER)


    def onDisconnection(self, reason):
        '''
        get notfied of disconnections
        and get a deferred for a new protocol object (next retry)
        '''
        log.debug("<Connection was lost !> <reason={r}>", r=reason)
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
    serv       = MQTTService(myEndpoint, factory)
    serv.startService()
    reactor.run()

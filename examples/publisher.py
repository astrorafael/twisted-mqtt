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

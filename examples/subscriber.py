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

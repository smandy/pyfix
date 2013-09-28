import yaml

from pyfix.FIXProtocol import SessionManager, NormalMessageProcessing
from pyfix.FIXSpec import parse_specification
from pyfix.FIXConfig import makeConfig
from pyfix.util.randomOrders import flipOrder
from pyfix.FIXApplication import FIXApplication
from pyfix.FIXPerspective import FIXPerspective
from twisted.internet import reactor

fix = parse_specification(version="FIX.4.2")


class Receiver(FIXApplication):
    def __init__(self):
        FIXApplication.__init__(self, fix)
        self.dispatch_dict = {fix.OrderSingle: self.on_order}

    def on_order(self, protocol, order, seq, dup):
        assert order.__class__ == fix.OrderSingle
        #msg.dump()
        f = fix
        if self.state.__class__ == NormalMessageProcessing:
            reply = flipOrder(self.fix, order)
            assert self.protocol is not None
            assert self.session is not None
            strMsg = self.session.compile_message(reply)
            print ">>>MYEXEC %s %s" % (reply, strMsg)
            protocol.transport.write(strMsg)


config = yaml.load(open('./sinks.yaml', 'r'))

if __name__ == '__main__':
    receiverConfig = makeConfig(config)
    for x in receiverConfig:
        x.app = Receiver()

    sm = SessionManager(fix, receiverConfig)
    fixPerspective = FIXPerspective(sm, description="Multiplexer:Sinks")
    print "About to listen"
    sm.getConnected()
    reactor.run()

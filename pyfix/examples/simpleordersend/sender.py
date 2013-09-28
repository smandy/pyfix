import yaml
from twisted.internet import reactor

from pyfix.FIXProtocol import SessionManager, NormalMessageProcessing, LoggedOut
from pyfix.FIXSpec import parse_specification
from pyfix.FIXConfig import makeConfig
from pyfix.FIXApplication import FIXApplication

fix = parse_specification("FIX.4.2")

from pyfix.util import randomOrders


def beep(*args):
    print "Beep"


class Sender(FIXApplication):
    def __init__(self, fix):
        FIXApplication.__init__(self, fix)
        self.dispatch_dict = {
            fix.ExecutionReport: self.on_execution,
            fix.Heartbeat: beep
        }

        self.recovery_dict = {
            fix.ExecutionReport: self.recovered_execution,
            fix.Heartbeat: self.noop,
            fix.Logon: self.noop,
            fix.OrderSingle: self.on_recovered_new_order_single,
        }

    def set_state(self, old_state, new_state):
        self.state = new_state
        if new_state.__class__ == NormalMessageProcessing:
            assert self.protocol is not None
            reactor.callLater(2, self.send_order)
        elif new_state.__class__ == LoggedOut:
            print "SCram!"
            reactor.stop()

    def send_order(self):
        my_order = randomOrders.makeOrder(fix)
        message_string = self.session.compile_message(my_order)
        msg_seq_um = my_order.get_header_field_value(fix.MsgSeqNum)
        print "SENDING ORDER >> %s %s %s" % (msg_seq_um, my_order, message_string)
        self.protocol.transport.write(message_string)

    def on_execution(self, prot, msg, seq, possDup):
        print "Got an execution ! %s" % possDup
        print "State is %s" % self.state
        msg.dump()
        self.session.logoff(False)

    def recovered_execution(self, *args):
        print "Recoverred ! %s" % str(args)
        #msg.dump()

    def on_recovered_new_order_single(self, *args):
        print "Recoverred ! %s" % str(args)


config = yaml.load(open('../config/sender.yaml', 'r'))
senderConfig = makeConfig(config)
for x in senderConfig:
    x.app = Sender(fix)

if __name__ == '__main__':
    sessionManager = SessionManager(fix, senderConfig)
    for x in senderConfig:
        x.app.recover()

    sessionManager.getConnected()
    reactor.run()

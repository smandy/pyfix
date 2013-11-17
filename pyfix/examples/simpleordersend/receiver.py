import yaml

from pyfix.FIXProtocol import NormalMessageProcessing
from pyfix.FIXSpec import parse_specification
from pyfix.FIXConfig import makeConfig
from pyfix.SessionFactory import SessionManager

def boop(*args):
    print "Boop"

from pyfix.FIXApplication import FIXApplication

fix = parse_specification(version="FIX.4.2")

class Receiver(FIXApplication):
    def __init__(self, f):
        FIXApplication.__init__(self, f)
        self.dispatch_dict = {
            f.OrderSingle: self.on_order,
            f.Heartbeat: boop
        }

    def on_order(self, prot, msg, seq, dup):
        #msg.dump()
        f = self.fix
        if self.state.__class__ == NormalMessageProcessing:
            order_qty = msg.get_field_value(f.OrderQty)
            reply = f.ExecutionReport(fields=[
                f.OrderID('ORDERID'),
                f.ExecID('Exec21'),
                f.ExecTransType.NEW,
                f.ExecType.NEW,
                f.OrdStatus.FILLED,
                msg.get_field(f.Symbol),
                msg.get_field(f.Side),
                f.LeavesQty(0),
                f.CumQty(order_qty),
                f.LastShares(order_qty),
                f.LastPx(101.5),
                f.AvgPx(101.5)])

            assert self.protocol is not None
            assert self.session is not None
            message_string = self.session.compile_message(reply)
            print ">>>MYEXEC %s %s" % (reply, message_string)
            self.protocol.transport.write(message_string)
        else:
            dup = msg.get_header_field_value(f.PossDupFlag, default=False)

config = yaml.load(open('../config/receiver.yaml', 'r'))

if __name__ == '__main__':
    receiverConfig = makeConfig(config)
    for x in receiverConfig:
        x.app = Receiver(fix)

    sm = SessionManager(fix, receiverConfig)
    from twisted.internet import reactor

    print "About to listen"
    sm.getConnected()
    reactor.run()

import yaml

from pyfix.FIXProtocol import SessionManager, FIXApplication, NormalMessageProcessing
from pyfix.FIXSpec import parseSpecification
from pyfix.FIXConfig import makeConfig
from pyfix.FIXPerspective import FIXPerspective

from twisted.internet import reactor

from pyfix.util.randomOrders import makeOrder
import random

fix = parseSpecification("FIX.4.2")


class OrderSource(FIXApplication):
    def __init__(self, sender_comp_id):
        FIXApplication.__init__(sender_comp_id, fix)
        self.dispatchdict = {fix.ExecutionReport: self.on_execution}
        self.sender_comp_id = sender_comp_id

    def set_state(self, old_state, new_state):
        self.state = new_state
        if new_state.__class__ == NormalMessageProcessing:
            assert self.protocol is not None
            self.schedule_order_send()

    def schedule_order_send(self):
        # 5 second delay with 1 second stdev will separate out the heartbeat threads
        delay = max(0, random.normalvariate(2, 1))
        reactor.callLater(delay, self.send_order)

    def send_order(self):
        if self.state.__class__ == NormalMessageProcessing:
            f = fix
            my_order = makeOrder(fix, prefix=self.sender_comp_id)
            str_msg = self.session.compileMessage(my_order)
            msg_seq_num = my_order.getHeaderFieldValue(f.MsgSeqNum)
            print "%s>> %s %s %s" % (self.senderCompID, msg_seq_num, my_order, str_msg)
            self.protocol.transport.write(str_msg)
        self.schedule_order_send()

    def on_execution(self, ign1, msg, ign2, ign3):
        #print "Got an execign1tion !"
        ClOrdID = msg.getFieldValue(self.fix.ClOrdID)
        if not ClOrdID.startswith(self.sender_comp_id):
            print "ERROR !!! Unexpected execution"
            #msg.dump()

config = yaml.load(open('./sources.yaml', 'r'))
senderConfig = makeConfig(config)

for x in senderConfig:
    x.app = OrderSource(x.sender)

if __name__ == '__main__':
    sessionManager = SessionManager(fix, senderConfig)
    fixPerspective = FIXPerspective(sessionManager, description="Multiplexer:Sources")
    sessionManager.getConnected()
    reactor.run()

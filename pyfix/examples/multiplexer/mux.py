import yaml

from twisted.internet import reactor

from pyfix.FIXProtocol import SessionManager
from pyfix.FIXSpec import parseSpecification
from pyfix.FIXConfig import makeConfig
from pyfix.FIXApplication import FIXApplication
from pyfix.FIXPerspective import FIXPerspective

from pyfix.util.randomOrders import extensions

fix = parseSpecification("FIX.4.2")


class Multiplexer(object):
    def __init__(self, session_manager):
        self.session_manager = session_manager
        # We'll route each ric extension to a unique extension
        assert len(session_manager.initiatorsByTuple) == len(extensions), "%s vs %s" % (
            len(session_manager.initiatorsByTuple), len(extensions))
        self.sink_for_extension = {}
        self.source_by_name = {}

        for (session, extension) in zip(session_manager.initiatorsByTuple.values(), extensions):
            # Does it even need to know?! - do these guys even need to have their own identify ?
            # could use only one of each?
            sink_connection = SinkConnection(self)
            session.setApp(sink_connection)
            self.sink_for_extension[extension] = sink_connection

        for (s_t, session) in session_manager.acceptorsByTuple.items():
            sender, target = s_t
            app = SourceConnection(self)
            session.setApp(app)
            self.source_by_name[target] = app
        print "source by name ", self.source_by_name

    def on_order(self, source_connection, order):
        assert order.__class__ == fix.OrderSingle
        symbol = order.getFieldValue(fix.Symbol)
        extension = symbol.split('.')[-1]
        assert self.sink_for_extension.has_key(extension)
        sink = self.sink_for_extension[extension]

        # We need to re-sequence it - stick sequence numbers/target CompIDs etc on it.
        # Thankfully the 'guts' of the order should be okay so we can just use the fields
        # from the original order.
        if sink.protocol:
            re_wrap = fix.OrderSingle(fields=order.fields)
            msg = sink.session.compileMessage(re_wrap)
            sink.protocol.transport.write(msg)
        else:
            print "Can't route order - sink not connected"

    def on_execution(self, sink_connection, execution):
        assert execution.__class__ == fix.ExecutionReport
        #execution.dump()

        ClOrdID = execution.getFieldValue(fix.ClOrdID)
        source_system = ClOrdID[:7]
        source = self.source_by_name.get(source_system, None)
        if not source:
            print "Couldn't get source %s %s" % (source_system, self.source_by_name)
        else:
            reWrap = fix.ExecutionReport(fields=execution.fields)
            strMsg = source.session.compileMessage(reWrap)
            source.protocol.transport.write(strMsg)


class NoiseMux(Multiplexer):
    def __init__(self, session_manager, perspective):
        Multiplexer.__init__(self, session_manager)
        self.perspective = perspective

    def on_order(self, source, order):
        Multiplexer.on_order(self, source, order)
        self.perspective.on_order(source, order)

    def on_execution(self, source, execution):
        Multiplexer.on_execution(self, source, execution)
        self.perspective.on_execution(source, execution)

# The source/sink connections, although application objects
# should really be considered the 'periphery' of the system
# so have simple implementations. However in their bowels they
# have a full session object with its own persistence etc.
class SourceConnection(FIXApplication):
    def __init__(self, mux):
        FIXApplication.__init__(self, fix)
        self.mux = mux
        self.dispatchDict = {fix.OrderSingle: self.onOrder,
                             fix.Heartbeat: self.noop}
        self.recoveryDict = {fix.ExecutionReport: self.onRecoveredExecution,
                             fix.OrderSingle: self.onRecoveredOrder,
                             fix.ResendRequest: self.noop,
                             fix.Heartbeat: self.noop,
                             fix.Logon: self.noop}
        self.orders = 0
        self.execs = 0

    def onOrder(self, protocol, msg, seq, possdup):
        self.mux.on_order(self, msg)

    def onRecoveredExecution(self, msg):
        self.execs += 1

    def onRecoveredOrder(self, msg):
        self.orders += 1

    def onRecoveryDone(self):
        print "%s recovered %s orders, %s executions" % (self.session.target, self.orders, self.execs )


class SinkConnection(FIXApplication):
    def __init__(self, mux):
        FIXApplication.__init__(self, fix)
        self.dispatchDict = {fix.ExecutionReport: self.onExecution,
                             fix.Heartbeat: self.noop}

        self.recoveryDict = {fix.ExecutionReport: self.onRecoveredExecution,
                             fix.Heartbeat: self.noop,
                             fix.OrderSingle: self.onRecoveredOrder,
                             fix.ResendRequest: self.noop,
                             fix.Logon: self.noop}
        self.mux = mux
        self.execs = 0
        self.orders = 0

    def onRecoveryDone(self):
        "%s recovered %s executions, %s orders" % (self.session.target, self.execs, self.orders)

    def onRecoveredExecution(self, msg):
        self.execs += 1

    def onRecoveredOrder(self, msg):
        self.orders += 1

    def onExecution(self, protocol, msg, seq, possdup):
        self.mux.on_execution(self, msg)


if __name__ == '__main__':
    config = yaml.load(open('./mux.yaml', 'r'))
    muxConfig = makeConfig(config)
    sessionManager = SessionManager(fix, muxConfig)

    if 0:
        # Vanilla multiplexer
        multiplexer = Multiplexer(sessionManager)
    else:
        # 'Perspective' version can be monitored by examples/pyglex/muxGui
        fixPerspective = FIXPerspective(sessionManager, description="Multiplexer Example - MUX")
        multiplexer = NoiseMux(sessionManager, fixPerspective)

    for s in sessionManager.sessions:
        s.app.recover()

    sessionManager.getConnected()
    reactor.run()

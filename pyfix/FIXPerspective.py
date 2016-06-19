from twisted.spread import pb
from twisted.internet import reactor, task
from pyfix.alladin.Discovery import Discoverable

class FIXPerspective(pb.Root):
    def __init__(self, session_manager, description="FIX Perspective"):
        self.session_listeners = []
        self.session_manager = session_manager
        session_manager.perspective = self
        address = reactor.listenTCP(0, pb.PBServerFactory(self))
        # Advertise the perspective on the network
        port = address.getHost().port
        self.description = description
        data = {'description': self.description,
                'port': port}
        d = Discoverable(data, domain="pyfix_perspective")
        l = task.LoopingCall(self.update_listeners)
        reactor.callWhenRunning(l.start, 1)

    def remote_getSessionStatus(self):
        ret = []
        for session in self.session_manager.sessions:
            ret.append(
                (session.sender, session.target, session.isConnected(), session.inMsgSeqNum, session.outMsgSeqNum))
        return ret

    getSessionStatus = remote_getSessionStatus

    def remote_addSessionListener(self, listener):
        print "AddSessionListener %s" % listener
        listener.notifyOnDisconnect(lambda x: self.expunge(self.session_listeners, listener))
        self.session_listeners.append(listener)

    def on_execution(self, source, execution):
        to_iter = self.session_listeners[:]
        for x in to_iter:
            x.callRemote('onExecution', execution.to_fix()).addErrback(self.expunge, self.session_listeners, x)

    def on_order(self, source, order):
        to_iter = self.session_listeners[:]
        for x in to_iter:
            x.callRemote('onOrder', order.to_fix()).addErrback(self.expunge, self.session_listeners, x)

    def update_listeners(self):
        print "UpdateListeners ( of which there are %s)" % len(self.session_listeners)
        ss = self.getSessionStatus()
        to_iter = self.session_listeners[:]
        for x in to_iter:
            x.callRemote('onSessionState', ss).addErrback(self.expunge, self.session_listeners, x)

    @staticmethod
    def expunge(l, victim):
        print "Expunging %s" % victim
        while victim in l:
            l.remove(victim)

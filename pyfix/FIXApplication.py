from pyfix.FIXParser import SynchronousParser, ParseException
import cPickle


class RecoveryException(Exception):
    pass


class FIXApplication:
    def __init__(self, fix):
        self.state = None
        self.protocol = None
        self.session = None
        self.perspective = None
        self.fix = fix
        self.dispatch_dict = {fix.Heartbeat: self.noop,
                              fix.TestRequest: self.noop, }
        self.recovery_dict = {fix.Heartbeat: self.noop}
        self.in_recovery = False

    def noop(self, *args):
        pass

    def set_session(self, session):
        assert self.session is None
        self.session = session

    def set_protocol(self, protocol):
        print(f"onProtocol {protocol}")
        assert protocol.session == self.session, \
            f"{protocol.session} {self.session}"
        self.protocol = protocol

    def set_state(self, _, new_state):
        self.state = new_state

    def on_message(self, protocol, msg, seq, poss_dup):
        assert protocol == self.protocol, f"{protocol} {self.protocol}"
        msg_class = msg.__class__
        if self.dispatch_dict.has_key(msg_class):
            self.dispatch_dict[msg_class](protocol, msg, seq, poss_dup)
        else:
            print("Warning unmapped message {msg_class}")

    def recovered_message(self, msg):
        klazz = msg.__class__
        if self.recovery_dict.has_key(klazz):
            self.recovery_dict[klazz](msg)
        else:
            print("Unmapped recovery message {klazz}")

    def on_recovery_done(self):
        pass

    def recover(self):
        assert self.session is not None
        self.in_recovery = True
        sp = SynchronousParser(self.fix)
        c = self.session.persister.ledger.cursor()
        while True:
            d = c.next()
            if not d:
                break
            try:
                msg, _, _ = sp.parse(d[1])
                self.recovered_message(msg)
            except ParseException:
                msg = cPickle.loads(d[1])
                self.recovered_message(msg)
        c.close()
        self.on_recovery_done()
        self.in_recovery = False

import datetime
from pyfix.FIXApplication import FIXApplication
from pyfix.FIXParser import SynchronousParser
from pyfix.persistence.BerkeleyPersister import BerkeleyPersister


class Session(object):
    def __init__(self, session_manager, fix, config):
        self.session_manager = session_manager
        self.protocol = None
        self.fix = fix
        self.sender = config.sender
        self.target = config.target
        self.sender_compid = fix.SenderCompID(self.sender)
        self.target_compid = fix.TargetCompID(self.target)
        self.begin_string = fix.BeginString(fix.version)
        self.out_msg_seq_num = 1
        self.in_msg_seq_num = 1
        self.set_persister(BerkeleyPersister(config.persistRoot, self.sender, self.target))
        self.heartbeat_interval = config.heartbeatInterval
        # Why do we need an sp?
        self.sp = SynchronousParser(self.fix)
        self.last_by_type = {}
        self.state = None
        if config.app:
            self.set_app(config.app)
        else:
            self.set_app(FIXApplication(fix))

        self.on_integrity_exception = None
        self.last_integrity_exception = None
        self.want_to_be_logged_in = True

    def set_app(self, app):
        self.app = app
        self.app.set_session(self)

    def set_state(self, old_state, new_state):
        self.app.set_state(old_state, new_state)

    def bind_protocol(self, protocol):
        assert self.protocol is None
        assert protocol.session is None
        protocol.session = self
        self.protocol = protocol
        self.app.set_protocol(protocol)

    def release_protocol(self):
        assert self.protocol.session == self
        assert self.protocol is not None
        self.protocol.session = None
        self.protocol = None

    def str_connected(self):
        return {True: " Connected  ",
                False: "Disconnected"}[self.isConnected()]

    def __repr__(self):
        return "Session(%s-%s %s [%s,%s] )" % (self.sender,
                                               self.target,
                                               self.str_connected(),
                                               self.in_msg_seq_num,
                                               self.out_msg_seq_num)

    def dump_in(self, x):
        self.dump_msg(self.in_db, x)

    def dump_out(self, x):
        self.dump_msg(self.out_db, x)

    def logoff(self, want_to_be_logged_on=False):
        assert self.isConnected()
        self.want_to_be_logged_in = want_to_be_logged_on
        # TODO - investigate - I put this in for a reason!
        self.protocol._logoff()

    def logon(self): # This translates to "want to be logged on" for an acceptor!
        assert not self.isConnected()
        self.want_to_be_logged_in = True
        if self.factory:
            assert self.factory.__class__ == InitiatorFactory, "Logic error only initiators keep track of factory"
            self.factory.logon()

    def dump_msg(self, db, x):
        raw_msg = db[x]
        msg, x, y = self.sp.feed(raw_msg)
        msg.dump()
        print x, y

    def parse(self, msg):
        return self.sp.feed(msg)[0]

    def isConnected(self):
        return self.protocol is not None

    def set_persister(self, persister):
        self.persister = persister
        self.in_db, self.out_db = persister.getTodayPersister()
        #self.persister.report( self.inDb)
        #self.persister.report( self.outDb)
        p = SynchronousParser(self.fix)
        import time

        for db in (self.in_db, self.out_db):
            start = time.time()
            i = 0.0
            c = db.cursor()
            while True:
                v = c.next()
                if not v:
                    break
                msg, _, _ = p.feed(v[1])
                i += 1
            endTime = time.time()
            dur = endTime - start

            print "%s parsed %s messages in %s secs (%s/sec)" % (db, i, dur, i / dur )

        self.in_msg_seq_num = self.persister.getNextSeq(self.in_db)
        self.out_msg_seq_num = self.persister.getNextSeq(self.out_db)
        print "Setting sequence numbers %s %s" % ( self.in_msg_seq_num, self.out_msg_seq_num)

    def persist_and_advance(self,
                            message_string,
                            check_in_sequence=True):
        msg, _, _ = self.sp.feed(message_string)
        msg_seq = msg.get_header_field_value(self.fix.MsgSeqNum)
        if check_in_sequence:
            seq = self.persister.getNextSeq(self.in_db)
            seq2 = self.persister.getNextSeq(self.out_db)
            assert msg_seq >= seq, "Received %s vs %s %s" % (msg_seq, seq, seq2)

        self.persister.persistInMsg(msg_seq, message_string)
        self.in_msg_seq_num = msg_seq + 1

    def compile_message(self,
                        msg,
                        poss_dup=False,
                        force_sequence_number=None,
                        orig_sending_time=None,
                        persist=True,
                        disable_validation=False):

        sending_time = self.fix.SendingTime(datetime.datetime.now())
        body_length = self.fix.BodyLength(0)
        check_sum = self.fix.CheckSum(0)

        if force_sequence_number:
            seq = force_sequence_number
        else:
            seq = self.out_msg_seq_num

        header = [self.begin_string,
                  body_length,
                  msg.msgTypeField,
                  self.sender_compid,
                  self.target_compid,
                  self.fix.MsgSeqNum(seq),
                  sending_time
        ]

        if poss_dup:
            header = header[:-1] + [self.fix.PossDupFlag('Y')] + header[-1:]

        if orig_sending_time:
            header = header[:-1] + [self.fix.OrigSendingTime(orig_sending_time)] + header[-1:]

        footer = [check_sum]
        msg.header_fields = header
        msg.footer_fields = footer

        # this will check what we've done so far
        #msg.checkStructure()
        #msg.validate()
        msg.calc_body_length(mutate=True)
        msg.calc_check_sum(mutate=True)
        #msg.checkBodyLength()
        #bl2 = msg.calcBodyLength( )
        #cs2 = msg.calcCheckSum()

        if not disable_validation:
            msg.validate()
            #assert bl==bl2, "Body Length failed before/after consistency check"
        #assert cs==cs2, "Checksum failed before/after consistency check"

        ret = msg.to_fix()
        if not poss_dup:
            if persist:
                self.persister.persistOutMsg(self.out_msg_seq_num, ret)
                #self.outDb[self.outMsgSeqNum] = ret
            #self.outDb.sync()
            self.out_msg_seq_num += 1
        return ret

from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from datetime import datetime
from types import IntType, ListType
import random
from collections import deque
from twisted.internet.error import AlreadyCancelled

from FIXParser import FIXParser, SynchronousParser
from FIXSpec import BusinessReject, MessageIntegrityException


def log(x):
    pass


class OutOfSequenceException(Exception):
    pass


class IllegalStateTransition(Exception):
    pass


class FIXState:
    def __init__(self, protocol):
        # self.factory  = protocol.factory
        self.protocol = protocol
        self.fix = protocol.fix

    def isInSequence(self, msgSeqNum):
        assert isinstance(msgSeqNum, IntType), "Need a sequence number"
        assert self.protocol.session is not None, "Session not connected"
        return msgSeqNum == self.protocol.session.in_msg_seq_num


class AwaitingLogout(FIXState):
    def on_msg(self, msg, _1, _2):
        """
        :param msg:
        :param ign:
        :param ign1:
        """
        if msg.__class__ == self.fix.Logout:
            print("Graceful logout")
            reactor.callLater(0, self.protocol.clean_up_and_die)
        else:
            # XXX What to do here - ignore I guess
            print(f"Expected logout but got {msg}")


class AwaitingLogon(FIXState):
    def logon_processing(self, _):
        assert False, "Override me!"

    def on_msg(self, msg, in_msg_seq_num, poss_dup_flag):
        assert msg.__class__ == self.fix.Logon
        assert not poss_dup_flag

        self.logon_processing(msg)

        if self.isInSequence(in_msg_seq_num):
            print("In Sequence Logon")
            self.protocol.session.persist_and_advance(
                msg.to_fix(), check_in_sequence=True)
            self.protocol.set_state(self.protocol.normal_message_processing)
        else:
            print("Out of sequence logon")
            # self.protocol.factory.inMsgSeqNum = msgSeqNum+1
            self.protocol.set_state(GapProcessing(
                self.protocol, msg, in_msg_seq_num))
        self.protocol.send_heartbeat()


class InitiatorAwaitingLogon(AwaitingLogon):
    def logon_processing(self, _):
        self.protocol.heartbeat_interval = \
            self.protocol.session.heartbeat_interval


class AcceptorAwaitingLogon(AwaitingLogon):
    def logon_processing(self, msg):
        f = self.fix

        # The Acceptor factory has a map of compids.
        # if we find one we wire it up
        session = self.protocol.factory.get_session_for_message(msg)
        print("Found session {session}")
        if session:
            # self.protocol.session = session
            session.bind_protocol(self.protocol)
            # # XXX Chekc the spec. Do we need to have same heartbeat as our cpty?
            # does the initiator get to mandate it ?
            interval = msg.get_field_value(f.HeartBtInt)
            self.protocol.heartbeat_interval = interval
            reply = f.Logon(fields=[f.EncryptMethod.NONEOTHER,
                                    f.HeartBtInt(interval)])
            message_string = self.protocol.session.compile_message(reply)
            out_seq_num = reply.get_header_field_value(f.MsgSeqNum)
            print(f">>> {out_seq_num} {reply} {message_string}")
            self.protocol.transport.write(message_string)
        else:
            print("Getting rid of connection - don't know the session")
            reply = f.Logout(fields=[f.Text("Unknown Session")])
            message_string = self.flip_message(reply)
            # print ">>> %s %s %s" % (outMsgSeqNum, reply , strMsg)
            self.protocol.transport.write(message_string)
            self.protocol.state = self.protocol.loggedOutState

    # On logout we don't have the benefit of an identified session
    # so echo what was sent back to use. Don't know the session so
    # we'll just set the sequence number to be one.
    def flip_message(self,
                     msg):
        f = self.fix
        sending_time = f.SendingTime(datetime.now())
        body_length = f.BodyLength(0)
        check_sum = f.CheckSum(0)
        sender = f.SenderCompID(msg.get_header_field_value(f.TargetCompID))
        target = f.TargetCompID(msg.get_header_field_value(f.SenderCompID))
        begin_string = msg.get_header_field(f.BeginString)

        header = [begin_string,
                  body_length,
                  msg.msgTypeField,
                  sender,
                  target,
                  f.MsgSeqNum(1),
                  sending_time]
        footer = [check_sum]
        msg.header_fields = header
        msg.footer_fields = footer
        # this will check what we've done so far
        msg.check_structure()
        msg.validate()
        bl = msg.calc_body_length(mutate=True)
        cs = msg.calc_check_sum(mutate=True)
        msg.check_body_length()
        bl2 = msg.calc_body_length()
        cs2 = msg.calc_check_sum()
        assert bl == bl2, "Body Length failed before/after consistency check"
        assert cs == cs2, "Checksum failed before/after consistency check"
        ret = msg.to_fix()
        return ret


class LoggedOut(FIXState):
    def on_msg(self, *args):
        print(f"Ignorning msg {args}")


class NormalMessageProcessing(FIXState):
    def __init__(self, p):
        FIXState.__init__(self, p)
        f = p.fix
        self.in_sequence_dict = {
            f.Logout: p.on_logout,
            f.Logon: self.failure,
            f.TestRequest: p.on_test_request,
            f.SequenceReset: SplitGapFill(
                self.on_sequence_reset_reset, self.failure),
            f.Heartbeat: p.on_heartbeat,
            f.ResendRequest: p.on_resend_request
        }

        self.out_of_sequence_dict = {
            f.SequenceReset: SplitGapFill(
                self.on_sequence_reset_reset, self.failure),
            f.ResendRequest: p.on_resend_request
        }

        self.out_of_sequence_dict_post = {
            f.Logout: p.on_logout,
            # f.ResendRequest : p.onResendRequest
        }

    def failure(self, msg, msgSeqNum, possDupFlag):
        raise IllegalStateTransition(
            f"Message {msg.__class__} is illegal in {self} state")

    def on_sequence_reset_reset(self, msg, _msgSeqNum, _possDupFlag):
        new_seq_no = msg.get_field_value(msg.fix.NewSeqNo)
        assert new_seq_no >= self.protocol.session.inMsgSeqNum
        self.protocol.session.in_msg_seq_num = new_seq_no

    def on_msg(self, *args):
        msg, msg_seq_num, pos_dup_flag = args
        # print self.protocol.session.sender,
        # " <<< ", msg, msgSeqNum, possDupFlag
        if pos_dup_flag:
            print("XXX Possdup message in normal message processing "
                  "- have I just gapfilled?")
            if self.protocol.session.inDb.has_key(msg_seq_num):
                print("OKAY - have seen already")
            else:
                print("Have possdup message I never saw first time round")
            return
            # assert self.protocol.session.inDb.has_key( msgSeqNum )
            # inSequence = msgSeqNum==self.protocol.session.inMsgSeqNum
            # FIX Spec - these should still be honoured first
            # if out of sequence !
        klazz = msg.__class__
        if self.isInSequence(msg_seq_num):
            s = self.protocol.session
            if self.in_sequence_dict.has_key(klazz):
                # print "Dispatching in sequence message"
                self.in_sequence_dict[klazz](*args)
                # Let the application have a bash at it

            perspective = self.protocol.session.session_manager.perspective
            if perspective:
                if msg.__class__ == self.fix.ExecutionReport:
                    perspective.on_execution(self.protocol, msg)
                elif msg.__class__ == self.fix.OrderSingle:
                    perspective.on_order(self.protocol, msg)

            self.protocol.session.app.on_message(self.protocol, *args)
            s.persist_and_advance(msg.to_fix(),
                                  check_in_sequence=True)
        else:
            if self.out_of_sequence_dict.has_key(klazz):
                self.out_of_sequence_dict[klazz](*args)
            print(f"Out of sequence message got {msg_seq_num}"
                  f"expecting {self.protocol.session.in_msg_seq_num}")

            gap_processor = GapProcessing(self.protocol, msg, msg_seq_num)
            self.protocol.set_state(gap_processor)

            if self.out_of_sequence_dict_post.has_key(klazz):
                self.out_of_sequence_dict_post[klazz](*args)


class GapProcessing(FIXState):
    def __init__(self, protocol, _msg, msg_seq_num):
        FIXState.__init__(self, protocol)
        self.gaps = {}
        self.gap_queue = {}
        self.last_sequence = msg_seq_num
        # TODO - these could actually be stored
        # off to another persister somewhere
        self.pending_application_messages = {}

        print(f"out of sequence message got {msg_seq_num} expecting "
              f"{self.protocol.session.in_msg_seq_num}")
        resend_request = self.fix.ResendRequest(
            fields=[self.fix.BeginSeqNo(self.protocol.session.in_msg_seq_num),
                    self.fix.EndSeqNo(0)])

        message_string = self.protocol.session.compile_message(resend_request)
        print("Sending resend request {message_string}")
        resend_request.dump(">>>")
        self.protocol.transport.write(message_string)
        for i in range(self.protocol.session.in_msg_seq_num, msg_seq_num + 1):
            self.gaps[i] = resend_request

        self.protocol.session.in_msg_seq_num = msg_seq_num + 1
        print(f"In Gap processing : Gaps are {self.gaps}")

    def failure(self, *_args):
        assert False, "Logic error, I shouldn't be called"

    def on_msg(self, *args):
        msg, msg_seq_num, pos_dup_flag = args
        print("Gapfill <<< {msg} {msg_seq_num}")
        if msg.__class__ == self.fix.SequenceReset:
            new_seq = msg.get_field_value(self.fix.NewSeqNo)
            if msg.get_optional_field_values(self.fix.GapFillFlag, 'N') == 'N':
                # SequenceReset-Reset
                assert False, "XXX Handle Sequence Reset-Reset"
            else:
                # SequenceReset-Gapfill
                foreign_sequence_number = msg.get_header_field_value(
                    self.fix.MsgSeqNum)
                print(f"Received Gap fill {foreign_sequence_number}-{new_seq}")
                # NEw Seq points *beyond* the gap. i.e. next expected number
                # so NB we rely here on fact that
                # range(a,b) goes from a -> b-1 :-)
                self.protocol.session.in_msg_seq_num = \
                    max(self.protocol.session.in_msg_seq_num, new_seq)

                for i in range(foreign_sequence_number, new_seq):
                    assert self.gaps.has_key(i) or i > self.last_sequence
                    if self.gaps.has_key(i):
                        del self.gaps[i]
        elif not pos_dup_flag:
            # Don't want to know - stick them in a queue
            if msg.__class__ == self.fix.ResendRequest:
                print(f"Processing resend request {msg}")
                self.protocol.on_resend_request(*args)
                if self.isInSequence(msg_seq_num):
                    # print "Persisting resend request"
                    self.protocol.session.persist_and_advance(
                        msg.to_fix(),
                        check_in_sequence=True)
                else:
                    print("Resend request was out of sequence "
                          f"{self.protocol.session.in_msg_seq_num} "
                          f"vs {msg_seq_num}")
            else:
                print(f"Queueing message {msg} {msg_seq_num}")
                self.pending_application_messages[msg_seq_num] = msg
        else:
            if self.gaps.has_key(msg_seq_num) or \
               msg_seq_num > self.last_sequence:
                if self.gaps.has_key(msg_seq_num):
                    del self.gaps[msg_seq_num]
                    # assert self.gaps.has_key(msgSeqNum), "Logic error - have msg outside expected gap %s" % msgSeqNum
                # del self.gaps[msgSeqNum]
                print(f"Adding {msg_seq_num} to gap queue")
                self.gap_queue[msg_seq_num] = msg
                # XXX HMM... inMsgSeqNum During recovery
                # self.protocol.factory.inMsgSeqNum = max(newSeq,
                # self.protocol.factory.inMsgSeqNum)

        if not self.gaps:
            # self.protocol.factory.inMsgSeqNum = self.lastSequence + 1
            print("Gap Queue empty! - About to feed "
                  "myself queueud up messages "
                  f"- have {len(self.gap_queue)} from {self.gap_queue.keys()} "
                  f"am expecting {self.protocol.session.in_msg_seq_num}")
            print(f"Persisting {len(self.gap_queue)}"
                  f" recovered messages {self.gap_queue}")
            items = self.gap_queue.items()
            items.sort(key=lambda x: x[0])
            for idx, msg in items:
                self.protocol.session.app.on_message(
                    self.protocol, msg, idx, pos_dup_flag)
                # self.protocol.onMsg( msg, idx, False)
                seq = msg.get_header_field_value(self.fix.MsgSeqNum)
                if seq < self.protocol.session.in_msg_seq_num:
                    continue
                self.protocol.session.persist_and_advance(
                    msg.to_fix(), check_in_sequence=False)
            self.gap_queue = {}
            print(f"Have {len(self.pending_application_messages)} "
                  "pending application messages "
                  f"{self.pending_application_messages.keys()}")
            self.protocol.set_state(self.protocol.normal_message_processing)
            # If we're here it means we have completed the gap fill
            # process and all missing messages have been accounted
            # for in the gap fill process, and the session.inMsgSeqNum
            # has been set correctly. Anything int the pending queue
            # is a non-gapfill applicaiton message that we'll already
            # have received during msg processing -> filter it out.
            # rejectedItems = [ x for x in
            # self.pendingApplicationMessages.items()
            # if not x[0]>=self.protocol.session.inMsgSeqNum ]
            # print "Rejected pending messsages %s" % rejectedItems
            filtered_items = [x for x in
                              self.pending_application_messages.items() if
                              x[0] >= self.protocol.session.in_msg_seq_num]
            # filteredItems = [ x for x in
            # self.pendingApplicationMessages.items() ]
            filtered_items.sort(key=lambda x: x[0])
            for seq, v in filtered_items:
                print(f"Replaying sequence number {seq} "
                      f"to {self.protocol.state}")
                # Possdup = false
                self.protocol.state.on_msg(v, seq, False)


class SplitGapFill:
    """These really should have been two messages IMHO
    have them fire different callbacks depending on
    whether they were gapfills or not"""

    def __init__(self, srr, srg):
        self.srr = srr
        self.srg = srg

    def __call__(self, msg, seqNum, possDup):
        msg.dump()
        is_gap_fill = msg.get_optional_field_values(msg.fix.GapFillFlag)
        if is_gap_fill:
            self.srg(msg, seqNum, possDup)
        else:
            self.srr(msg, seqNum, possDup)


class MessageQueue(deque):

    def __init__(self):
        deque.__init__(self)
        self.last = 0

    def append(self, x):
        seq = x.get_header_field_value(x.fix.MsgSeqNum)
        if len(self) == 0:
            deque.append(self, x)
        else:
            if self.last + 1 != seq:
                raise OutOfSequenceException(f"{seq} vs {self.last + 1}")
        self.last = seq

    @staticmethod
    def get_seq(msg):
        return msg.get_header_field_value(msg.fix.MsgSeqNum)


class FIXProtocol(Protocol):
    def __init__(self, fix, _state_listeners=None):
        print(f"Protocol {self.__class__} {fix.version} init")
        self.fix = fix
        self.heartbeat_checks = {}
        self.pending_test_requests = {}
        self.heart_beat_interval = None
        self.factory = None
        self.session = None
        self.handler = None

        # State Objects
        self.awaiting_logon = self.AwaitingLogonKlazz(self)
        self.awaiting_logout = AwaitingLogout(self)
        self.normal_message_processing = NormalMessageProcessing(self)
        self.logged_out_state = LoggedOut(self)

        # Keep track of the callables I have scheduled at any given time
        # if the protocol dies want to cancel these so we don't have 'ghost'
        # calls after we''re done
        self.send_heartbeat_call = None
        self.test_request_checks = {}
        self.heartbeat_checks = {}

        self.state = None
        self.set_state(self.awaiting_logon)
        self.parser = FIXParser(self.fix, self.on_msg)

    def set_state(self, s):
        print(f"State change {self.state.__class__.__name__}->{s.__class__.__name__}")
        old_state = self.state
        self.state = s
        if self.session:
            self.session.set_state(old_state, self.state)

    @staticmethod
    def get_seq(msg):
        return msg.getHeader

    def send_heartbeat(self):
        if self.state == self.normal_message_processing:
            msg = self.fix.Heartbeat()
            message_string = self.session.compile_message(msg)
            # print "Sending heartbeat ... %s" % strMsg
            msg_seq_num = msg.get_header_field_value(self.fix.MsgSeqNum)
            log(">>> %s %s %s" % (msg_seq_num, msg, message_string))
            self.transport.write(message_string)
            # print "Scheduling heartbeat in %s " % self.heartbeatInterval
        else:
            print(f"NOT SENDING HEARTBEAT - dodgy state {self.state}")
            # Depending on what you want to do this may or may not be useful
        # from observation when a large number of sessions connect at roughly
        # the same time the heartbeats can cause a 'wave'
        # of messages every heartbeat
        # interval ( or multiple thereof ). We'll help the reactor out a bit by
        # adding a small randomization ( 1 second standard deviation )
        # to the interval
        # this should be small enough to prevent any test request
        # cycles but large enough
        # to smooth out heartbeats between multiple sessions
        delay = random.normalvariate(self.heartbeat_interval, 1)
        # Or if you're OCD or into Wagner/Kraftwerk/Techno you're probably
        # not a fan of randomness and like regularly spaced metronomic 'doof's
        # - uncomment the line below delay = self.heartbeatInterval
        # delay = self.heartbeatInterval

        self.send_heartbeat_call = reactor.callLater(
            delay, self.send_heartbeat)
        # We'll rely on our heartbeat but
        myObj = datetime.now()
        self.heartbeat_checks[myObj] = reactor.callLater(
            self.heartbeat_interval * 1.5,
            self.check_heartbeat, myObj)

    def on_logout(self, msg, _in_msg_seq_num, _poss_dup_flag):
        print("onLogout {msg}")
        self.session.want_to_be_logged_on = False
        msg = self.fix.Logout(
            fields=[self.fix.Text("Accepted logoff request")])
        message_string = self.session.compile_message(msg, persist=False)
        print(">>> {message_string}")
        self.transport.write(message_string)
        self.transport.loseConnection()
        reactor.callLater(0, self.clean_up_and_die)

    def check_heartbeat(self, token):
        assert self.heartbeat_checks.has_key(token)
        del self.heartbeat_checks[token]
        print(f"Check Heartbeat {token}")
        if self.state == self.normal_message_processing:
            print("No heartbeat recieved for "
                  f"{token} {datetime.now() - token}")
            challenge = f"TEST {str(random.random())[2:15]}"
            test_request_id = self.fix.TestReqID(challenge)
            msg = self.fix.TestRequest(fields=[test_request_id])
            message_string = self.session.compile_message(msg)
            # print "Sending heartbeat ... %s" % strMsg
            msg_seq_num = msg.get_header_field_value(self.fix.MsgSeqNum)
            print(f">>> {msg_seq_num} {msg} {message_string}")
            self.transport.write(message_string)
            self.test_request_checks[challenge] = reactor.callLater(
                10,
                self.check_test_request_acknowledged, challenge)
        else:
            print("Skipping heartbeat checks - not "
                  "in normal message processing phase")

    def check_test_request_acknowledged(self, challenge):
        assert self.test_request_checks.has_key(challenge)
        print("He's out of there")
        msg = self.fix.Logout(
            fields=[self.fix.Text(f"No response to test request {challenge}")])
        message_string = self.session.compile_message(msg)
        msg_seq_num = msg.get_header_field_value(self.fix.MsgSeqNum)
        print(f">>> {msg_seq_num, msg} {message_string}")
        self.transport.write(message_string)
        # Bye bye
        self.transport.loseConnection()
        reactor.callLater(0, self.clean_up_and_die)

    def _logoff(self, reason=None, extreme_prejudice=False):
        """Don't call me - call the session objects logoff instead"""
        if not self.state == self.normal_message_processing:
            self.transport.loseConnection()
            self.clean_up_and_die()

        if reason:
            fields = [self.fix.Text(reason)]
        else:
            fields = []

        msg = self.fix.Logout(fields)
        message_string = self.session.compile_message(msg)
        self.transport.write(message_string)
        if extreme_prejudice:
            reactor.callLater(0, self.clean_up_and_die)
        else:
            self.set_state(self.awaiting_logout)

    def clean_up_and_die(self):
        # Get rid of the balls we've got already up in the air!
        # Note to self
        # I assume as long as code is logically
        # correct I don't have to worry about
        if self.state == self.logged_out_state:
            print("Already cleaned up - nothing to do")
        else:
            self.set_state(self.logged_out_state)
            calls = [self.send_heartbeat_call] + \
                self.test_request_checks.values() + \
                self.heartbeat_checks.values()
            for call in calls:
                if call:
                    try:
                        call.cancel()
                    except AlreadyCancelled:
                        pass

            # TODO - pycharm complaining these havent been used.
            # Doesnt look like they're required. Delete when happy
            # self.loggedIn = False
            # self.loggedOut = True
            # self.parser = None

            # quick sanity checks on disconnect
            if self.session:
                assert self.session.protocol is self
                self.session.release_protocol()
            print("Cleaned up")

    def on_heartbeat(self, msg, _seq, _dup):
        test_request_id = msg.get_field(self.fix.TestReqID)
        if test_request_id:
            challenge = test_request_id.value
            if self.test_request_checks.has_key(challenge):
                self.test_request_checks[challenge].cancel()
                del self.test_request_checks[challenge]
            else:
                pass
                # print "Got testRequestID I didn't send!!! %s" % testRequestID
        else:
            for posted, cb in self.heartbeat_checks.items()[:]:
                # print "Clearing check %s %s after %s seconds" %
                # ( callable, posted, (now-posted).seconds)
                cb.cancel()
                del self.heartbeat_checks[posted]

    def on_test_request(self, msg, _seq, _dup):
        # print "onTestRequest %s" % msg
        test_request_id = msg.get_field(self.fix.TestReqID)
        # assert self.loggedIn
        msg = self.fix.Heartbeat(fields=[test_request_id])
        message_string = self.session.compile_message(msg)
        # print "Test Request %s .. replying with %s" % (testRequestId, strMsg)
        self.transport.write(message_string)

    def connectionMade(self):
        print("Connection Made")
        self.parser = FIXParser(self.fix,
                                self.on_msg)

    def dataReceived(self, data):
        # print "============================================"
        # print "Got some data!!! %s" % data
        self.parser.feed(data)

    def on_resend_request(self, msg, _seq, _dup):
        begin = msg.get_field_value(self.fix.BeginSeqNo)
        tmp_end = msg.get_field_value(self.fix.EndSeqNo)
        resend_details = []
        gap = None
        db = self.session.out_db
        if tmp_end == 0:
            end_seq_no = self.session.out_msg_seq_num - 1
        else:
            end_seq_no = tmp_end

        print(f"onResendRequest {begin}-{tmp_end} "
              f"Playing back {begin}-{end_seq_no}")
        parser = SynchronousParser(self.fix)
        for i in range(begin, end_seq_no + 1):
            # print i , "... " ,
            haveMsg = False
            if db.has_key(i):
                message_string = db[i]
                msg, _, _ = parser.feed(message_string)
                # print "Recovered %s" % msg
                if msg.Section != 'Session':
                    # We have a message to resend
                    if gap:
                        resend_details.append(gap)
                    gap = None
                    resend_details.append(msg)
                    haveMsg = True
            if not haveMsg:
                if gap:
                    gap[1] = i
                else:
                    gap = [i, i]
        if gap:
            resend_details.append(gap)
        print("Resend Details {len(resend_details)}")
        if 1:
            for obj in resend_details:
                if isinstance(obj, ListType):
                    # Gap Fill
                    [send_sequence_number, last_sequence_number] = obj
                    # print "GapFill %s-%s" % (sendSequenceNumber,
                    # lastSequenceNumber)
                else:
                    orig_seq = obj.get_header_field_value(self.fix.MsgSeqNum)
                    # obj.dump( "GapFill>>>")
                    # print "gf2 =%s %s %s" % (obj, msg.getHeaderField(
                    # self.pyfix.MsgSeqNum ).value, origSeq )

        for obj in resend_details:
            i = 0
            if type(obj) == ListType:
                # Gap Fill
                [send_sequence_number, last_sequence_number] = obj
                gapFill = self.fix.SequenceReset(
                    fields=[self.fix.NewSeqNo(last_sequence_number + 1),
                            self.fix.GapFillFlag('Y')])
                message_string = self.session.compile_message(
                    gapFill,
                    poss_dup=True,
                    force_sequence_number=send_sequence_number)
                print(f"Sending sequence reset {send_sequence_number}->"
                      f"{last_sequence_number + 1} {message_string}")
                self.transport.write(message_string)
            else:
                # Hmm wonder if this will work.
                # Header of old msg is going to be blatted
                orig_seq = obj.get_header_field_value(self.fix.MsgSeqNum)
                print(f"{obj:10s} {orig_seq}")
                orig_sending_time = obj.get_header_field_value(
                    self.fix.SendingTime)
                message_string = self.session.compile_message(
                    obj,
                    poss_dup=True,
                    force_sequence_number=orig_seq,
                    orig_sending_time=orig_sending_time)
                # obj.dump("Recovered: " )
                # print "REC>>> %s %s %s" % (origSeq, obj, fixMsg)
                self.transport.write(message_string)
            i += 1
            if i % 100 == 0:
                print(f"Recovering {i} ...")

    def on_sequence_reset(self, msg, _seq, _dup):
        # print "onSequenceReset %s %s" % ( msg, msg.toFix() )
        is_gap_fill = msg.get_optional_field_values(self.fix.GapFillFlag)
        if is_gap_fill:
            self.onGapFill(msg)
        else:
            assert False, "Pure sequence reset not handled yet"

    def connectionLost(self, reason):
        if self.state != self.logged_out_state:
            print(f"PROTOCOL: Connection lost reason = {reason}")
            self.clean_up_and_die()
        else:
            print("Connection Closed")

    def on_msg(self, msg, data):
        message_class = msg.__class__
        message_seq_num = msg.get_header_field_value(self.fix.MsgSeqNum)
        poss_dup_flag = msg.get_header_field_value(self.fix.PossDupFlag)

        if self.session is not None:
            sender = self.session.sender
        else:
            sender = "UNKN"

        log(f"<<< {sender} {message_seq_num} {msg}->{self.state} {data}")
        try:
            msg.validate()
        except MessageIntegrityException as e:
            print(f"Integrity Exception {e.message}")
            e.msg.dump()
            self.session.last_integrity_exception = msg, e
            # No further processing required
            # on a message that fails integrity checks
            if self.session.onIntegrityException:
                self.session.onIntegrityException(e)
            return
        except BusinessReject as br:
            self.last_business_reject = msg, br
            fields = [self.fix.RefSeqNum(message_seq_num),
                      self.fix.Text(br.message)]
            if br.field is not None:
                fields.append(br.field)
            reject = self.fix.Reject(fields=fields)
            # br.field = SessionRejectReason
            print(f"Creating reject - fields are {fields}")
            reject_string = self.session.compile_message(reject)
            self.transport.write(reject_string)
            # Spec says messages which fail business validation
            # sholud be logged + sequence numbers
            # incremented
            self.session.persist_and_advance(
                msg.to_fix(), checkInSequence=True)
            return

        self.state.on_msg(msg, message_seq_num, poss_dup_flag)
        if self.session is not None:
            self.session.last_by_type[message_class] = msg


class InitiatorFIXProtocol(FIXProtocol):
    AwaitingLogonKlazz = InitiatorAwaitingLogon

    def connectionMade(self):
        assert self.session is not None
        FIXProtocol.connectionMade(self)
        msg = self.fix.Logon(
            fields=[self.fix.EncryptMethod.NONEOTHER,
                    self.fix.HeartBtInt(self.session.heartbeat_interval)])
        # THIS SHOULD BE SOME SORT OF METHOD
        message_string = self.session.compile_message(msg)
        msg_seq_num = msg.get_header_field_value(self.fix.MsgSeqNum)
        print(f">>> {msg_seq_num} {msg} {message_string}")
        self.transport.write(message_string)


class AcceptorFIXProtocol(FIXProtocol):
    AwaitingLogonKlazz = AcceptorAwaitingLogon

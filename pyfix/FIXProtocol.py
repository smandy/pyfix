from FIXParser import FIXParser, SynchronousParser
from FIXApplication import FIXApplication
from FIXSpec import BusinessReject, MessageIntegrityException
from twisted.internet.protocol import Protocol, ReconnectingClientFactory, Factory
from twisted.internet import reactor
from BerkeleyPersister import BerkeleyPersister

from datetime import datetime
from types import IntType, ListType
import random
from collections import deque, defaultdict

from twisted.internet.error import AlreadyCancelled


def log(x):
    pass


class OutOfSequenceException(Exception):
    pass


class IllegalStateTransition(Exception):
    pass


class FIXState:
    def __init__(self, protocol):
        #self.factory  = protocol.factory
        self.protocol = protocol
        self.fix = protocol.fix

    def isInSequence(self, msgSeqNum):
        assert type(msgSeqNum) == IntType, "Need a sequence number"
        assert self.protocol.session is not None, "Session not connected"
        return msgSeqNum == self.protocol.session.inMsgSeqNum


class AwaitingLogout(FIXState):
    def onMsg(self, msg, ign, ign1):
        """
:param msg:
        :param ign:
        :param ign1:
        """
        if msg.__class__ == self.fix.Logout:
            print "Graceful logout"
            reactor.callLater(0, self.protocol.cleanUpAndDie)
        else:
            # XXX What to do here - ignore I guess
            print "Expected logout but got %s" % msg


class AwaitingLogon(FIXState):
    def logonProcessing(self, _):
        assert False, "Override me!"

    def onMsg(self, msg, inMsgSeqNum, possDupFlag):
        assert msg.__class__ == self.fix.Logon
        assert not possDupFlag

        self.logonProcessing(msg)

        if self.isInSequence(inMsgSeqNum):
            print "In Sequence Logon"
            self.protocol.session.persistMsgAndAdvanceSequenceNumber(msg.toFix(), checkInSequence=True)
            self.protocol.set_state(self.protocol.normalMessageProcessing)
        else:
            print "Out of sequence logon"
            #self.protocol.factory.inMsgSeqNum = msgSeqNum+1
            self.protocol.set_state(GapProcessing(self.protocol, msg, inMsgSeqNum))
        self.protocol.sendHeartbeat()


class InitiatorAwaitingLogon(AwaitingLogon):
    def logonProcessing(self, _):
        self.protocol.heartbeatInterval = self.protocol.session.heartbeatInterval


class AcceptorAwaitingLogon(AwaitingLogon):
    def logonProcessing(self, msg):
        f = self.fix

        # The Acceptor factory has a map of compids.
        # if we find one we wire it up
        session = self.protocol.factory.getSessionForMessage(msg)
        print "Found session %s" % session
        if session:
            #self.protocol.session = session
            session.bindProtocol(self.protocol)
            ## XXX Chekc the spec. Do we need to have same heartbeat as our cpty?
            # does the initiator get to mandate it ?
            interval = msg.getFieldValue(f.HeartBtInt)
            self.protocol.heartbeatInterval = interval
            reply = f.Logon(fields=[f.EncryptMethod.NONEOTHER,
                                    f.HeartBtInt(interval)])
            strMsg = self.protocol.session.compileMessage(reply)
            outMsgSeqNum = reply.getHeaderFieldValue(f.MsgSeqNum)
            print ">>> %s %s %s" % (outMsgSeqNum, reply, strMsg)
            self.protocol.transport.write(strMsg)
        else:
            print "Getting rid of connection - don't know the session"
            reply = f.Logout(fields=[f.Text("Unknown Session")])
            strMsg = self.flipMessage(reply)
            #print ">>> %s %s %s" % (outMsgSeqNum, reply , strMsg)
            self.protocol.transport.write(strMsg)
            self.protocol.state = self.protocol.loggedOutState

    # On logout we don't have the benefit of an identified session
    # so echo what was sent back to use. Don't know the session so
    # we'll just set the sequence number to be one.
    def flipMessage(self,
                    msg):
        f = self.fix
        sendingTime = f.SendingTime(datetime.now())
        bodyLength = f.BodyLength(0)
        checkSum = f.CheckSum(0)
        sender = f.SenderCompID(msg.getHeaderFieldValue(f.TargetCompID))
        target = f.TargetCompID(msg.getHeaderFieldValue(f.SenderCompID))
        beginString = msg.getHeaderField(f.BeginString)

        header = [beginString,
                  bodyLength,
                  msg.msgTypeField,
                  sender,
                  target,
                  f.MsgSeqNum(1),
                  sendingTime
        ]
        footer = [checkSum]
        msg.headerFields = header
        msg.footerFields = footer
        # this will check what we've done so far
        msg.checkStructure()
        msg.validate()
        bl = msg.calcBodyLength(mutate=True)
        cs = msg.calcCheckSum(mutate=True)
        msg.checkBodyLength()
        bl2 = msg.calcBodyLength()
        cs2 = msg.calcCheckSum()
        assert bl == bl2, "Body Length failed before/after consistency check"
        assert cs == cs2, "Checksum failed before/after consistency check"
        ret = msg.toFix()
        return ret


class LoggedOut(FIXState):
    def onMsg(self, *args):
        print "Ignorning msg %s" % str(args)


class NormalMessageProcessing(FIXState):
    def __init__(self, p):
        FIXState.__init__(self, p)
        f = p.fix
        self.inSequenceMap = {
            f.Logout: p.onLogout,
            f.Logon: self.failure,
            f.TestRequest: p.onTestRequest,
            f.SequenceReset: SplitGapFill(self.onSequenceResetReset, self.failure),
            f.Heartbeat: p.onHeartbeat,
            f.ResendRequest: p.onResendRequest
        }

        self.outOfSequenceMapPre = {
            f.SequenceReset: SplitGapFill(self.onSequenceResetReset, self.failure),
            f.ResendRequest: p.onResendRequest
        }

        self.outOfSequenceMapPost = {
            f.Logout: p.onLogout,
            #f.ResendRequest : p.onResendRequest
        }

    def failure(self, msg, msgSeqNum, possDupFlag):
        raise IllegalStateTransition("Message %s is illegal in %s state" % (msg.__class__, self))

    def onSequenceResetReset(self, msg, msgSeqNum, possDupFlag):
        newSeqNo = msg.getFieldValue(msg.fix.NewSeqNo)
        assert newSeqNo >= self.protocol.session.inMsgSeqNum
        self.protocol.session.inMsgSeqNum = newSeqNo

    def onMsg(self, *args):
        msg, msgSeqNum, possDupFlag = args
        #print self.protocol.session.sender, " <<< ", msg, msgSeqNum, possDupFlag
        if possDupFlag:
            print "XXX Possdup message in normal message processing - have I just gapfilled? ",
            if self.protocol.session.inDb.has_key(msgSeqNum):
                print "OKAY - have seen already"
                #return
            else:
                print "Have possdup message I never saw first time round"
            return
            #assert self.protocol.session.inDb.has_key( msgSeqNum )
        #inSequence = msgSeqNum==self.protocol.session.inMsgSeqNum
        # FIX Spec - these should still be honoured first if out of sequence !
        klazz = msg.__class__
        if self.isInSequence(msgSeqNum):
            s = self.protocol.session
            if self.inSequenceMap.has_key(klazz):
                #print "Dispatching in sequence message"
                self.inSequenceMap[klazz](*args)
                # Let the application have a bash at it

            spssp = self.protocol.session.sessionManager.perspective
            if spssp:
                if msg.__class__ == self.fix.ExecutionReport:
                    spssp.on_execution(self.protocol, msg)
                elif msg.__class__ == self.fix.OrderSingle:
                    spssp.on_order(self.protocol, msg)

            self.protocol.session.app.onMessage(self.protocol, *args)
            s.persistMsgAndAdvanceSequenceNumber(msg.toFix(), checkInSequence=True)
        else:
            if self.outOfSequenceMapPre.has_key(klazz):
                self.outOfSequenceMapPre[klazz](*args)
            print "Out of sequence message got %s expecting %s" % (msgSeqNum, self.protocol.session.inMsgSeqNum)

            gapProcessor = GapProcessing(self.protocol, msg, msgSeqNum)
            self.protocol.set_state(gapProcessor)

            if self.outOfSequenceMapPost.has_key(klazz):
                self.outOfSequenceMapPost[klazz](*args)


class LoggedOut(FIXState):
    def onMsg(self, *args):
        print "Ignoring msg - logged out %s" % str(args)
        pass


class GapProcessing(FIXState):
    def __init__(self, protocol, msg, msgSeqNum):
        FIXState.__init__(self, protocol)
        self.gaps = {}
        self.gapQueue = {}
        self.lastSequence = msgSeqNum

        # TODO - these could actually be stored off to another persister somewhere
        self.pendingApplicationMessages = {}

        print "out of sequence message got %s expecting %s" % (msgSeqNum, self.protocol.session.inMsgSeqNum)
        resendRequest = self.fix.ResendRequest(fields=[self.fix.BeginSeqNo(self.protocol.session.inMsgSeqNum),
                                                       self.fix.EndSeqNo(0)])

        msgText = self.protocol.session.compileMessage(resendRequest)
        print "Sending resend request %s" % msgText
        resendRequest.dump(">>>")
        self.protocol.transport.write(msgText)
        for i in range(self.protocol.session.inMsgSeqNum, msgSeqNum + 1):
            self.gaps[i] = resendRequest

        self.protocol.session.inMsgSeqNum = msgSeqNum + 1
        print "In Gap processing : Gaps are %s" % str(self.gaps)

    def failure(self, *args):
        assert False, "Logic error, I shouldn't be called"

    def onMsg(self, *args):
        msg, msgSeqNum, possDupFlag = args
        print "Gapfill <<< %s %s" % (msg, msgSeqNum)
        #s =  "GAPFILL %s <<<" % self.gaps.keys()
        #msg.dump( s )
        if msg.__class__ == self.fix.SequenceReset:
            newSeq = msg.getFieldValue(self.fix.NewSeqNo)
            if msg.getOptionalFieldValue(self.fix.GapFillFlag, 'N') == 'N':
                # SequenceReset-Reset
                assert False, "XXX Handle Sequence Reset-Reset"
            else:
                # SequenceReset-Gapfill
                foreignSequenceNumber = msg.getHeaderFieldValue(self.fix.MsgSeqNum)
                print "Received Gap fill %s-%s" % (foreignSequenceNumber, newSeq)
                # NEw Seq points *beyond* the gap. i.e. next expected number
                # so NB we rely here on fact that range(a,b) goes from a -> b-1 :-)
                self.protocol.session.inMsgSeqNum = max(self.protocol.session.inMsgSeqNum, newSeq)

                for i in range(foreignSequenceNumber, newSeq):
                    assert self.gaps.has_key(i) or i > self.lastSequence
                    if self.gaps.has_key(i):
                        del self.gaps[i]
        elif not possDupFlag:
            # Don't want to know - stick them in a queue
            if msg.__class__ == self.fix.ResendRequest:
                print "Processing resend request %s" % msg
                self.protocol.onResendRequest(*args)
                if self.isInSequence(msgSeqNum):
                    #print "Persisting resend request"
                    self.protocol.session.persistMsgAndAdvanceSequenceNumber(msg.toFix(), checkInSequence=True)
                else:
                    print "Resend request was out of sequence %s vs %s" % (
                        self.protocol.session.inMsgSeqNum, msgSeqNum )
            else:
                print "Queueing message %s %s" % (msg, msgSeqNum)
                self.pendingApplicationMessages[msgSeqNum] = msg
        else:
            #assert self.gaps.has_key(msgSeqNum) or msgSeqNum>self.lastSequence, "%s %s %s" % (str(self.gaps), msgSeqNum, self.lastSequence)
            if ( self.gaps.has_key(msgSeqNum) or msgSeqNum > self.lastSequence ):
                if self.gaps.has_key(msgSeqNum):
                    del self.gaps[msgSeqNum]
                    #assert self.gaps.has_key(msgSeqNum), "Logic error - have msg outside expected gap %s" % msgSeqNum
                #del self.gaps[msgSeqNum]
                print "Adding %s to gap queue" % msgSeqNum
                self.gapQueue[msgSeqNum] = msg
                # XXX HMM... inMsgSeqNum During recovery
                #self.protocol.factory.inMsgSeqNum = max(newSeq, self.protocol.factory.inMsgSeqNum)

        if not self.gaps:
            #self.protocol.factory.inMsgSeqNum = self.lastSequence + 1
            print "Gap Queue empty! - About to feed myself queueud up messages - have %s from %s am expecting %s" % (
                len(self.gapQueue),
                self.gapQueue.keys(),
                self.protocol.session.inMsgSeqNum)
            print "Persisting %s recovered messages %s" % (len(self.gapQueue), str(self.gapQueue) )
            eyeThames = self.gapQueue.items()
            eyeThames.sort(lambda x, y: cmp(x[0], y[0]))
            for idx, msg in eyeThames:
                self.protocol.session.app.onMessage(self.protocol, msg, idx, possDupFlag)
                #self.protocol.onMsg( msg, idx, False)
                seq = msg.getHeaderFieldValue(self.fix.MsgSeqNum)
                if seq < self.protocol.session.inMsgSeqNum:
                    continue
                self.protocol.session.persistMsgAndAdvanceSequenceNumber(msg.toFix(), checkInSequence=False)
            self.gapQueue = {}

            print "Have %s pending application messages %s" % (
                len(self.pendingApplicationMessages), self.pendingApplicationMessages.keys() )
            self.protocol.set_state(self.protocol.normalMessageProcessing)
            # If we're here it means we have completed the gap fill process and all missing messages have been accounted
            # for in the gap fill process, and the session.inMsgSeqNum has been set correctly. Anything int the pending queue
            # is a non-gapfill applicaiton message that we'll already have received during msg processing -> filter it out.
            #rejectedItems = [ x for x in self.pendingApplicationMessages.items() if not x[0]>=self.protocol.session.inMsgSeqNum ]
            #print "Rejected pending messsages %s" % rejectedItems
            filteredItems = [x for x in self.pendingApplicationMessages.items() if
                             x[0] >= self.protocol.session.inMsgSeqNum]
            #filteredItems = [ x for x in self.pendingApplicationMessages.items() ]
            filteredItems.sort(lambda x, y: cmp(x[0], y[0]))
            for seq, v in filteredItems:
                print "Replaying sequence number %s to %s" % (seq, self.protocol.state)
                self.protocol.state.onMsg(v, seq, False) # Possdup = false

##         else:
##             print "Remaining gaps : "
##             #pp(self.gaps)

class SplitGapFill:
    """These really should have been two messages IMHO
    have them fire different callbacks depending on
    whether they were gapfills or not"""

    def __init__(self, srr, srg):
        self.srr = srr
        self.srg = srg

    def __call__(self, msg, seqNum, possDup):
        msg.dump()
        isGapFill = msg.getOptionalFieldValue(msg.fix.GapFillFlag)
        if isGapFill:
            self.srg(msg, seqNum, possDup)
        else:
            self.srr(msg, seqNum, possDup)


class MessageQueue(deque):
    def append(self, msg):
        seq = msg.getHeaderFieldValue(msg.fix.MsgSeqNum)
        if not len(self):
            deque.append(self, msg)
        else:
            if self.last + 1 != seq:
                raise OutOfSequenceException("%s vs %s" % ( seq, self.last + 1))
        self.last = seq

    def getSeq(self, msg):
        return msg.getHeaderFieldValue(msg.fix.MsgSeqNum)


class FIXProtocol(Protocol):
    def __init__(self, fix, stateListeners=None):
        print "Protocol %s %s init" % (self.__class__, fix.version)
        self.fix = fix

        self.heartBeatChecks = {}
        self.pendingTestRequests = {}
        self.heartbeatInterval = None
        #self.lastMessageByType = {}

        self.factory = None
        self.session = None

        self.handler = None

        # State Objects
        self.awaitingLogon = self.AwaitingLogonKlazz(self)
        self.awaitingLogout = AwaitingLogout(self)
        self.normalMessageProcessing = NormalMessageProcessing(self)
        self.loggedOutState = LoggedOut(self)

        # Keep track of the callables I have scheduled at any given time
        # if the protocol dies want to cancel these so we don't have 'ghost'
        # calls after we''re done
        self.sendHeartbeatCall = None
        self.testRequestChecks = {}
        self.heartbeatChecks = {}
        #self.pendingLogon = False
        #xoself.logonSequence = None

        self.state = None
        self.setState(self.awaitingLogon)

    def setState(self, s):
        #print "State change %s->%s" % (self.state.__class__.__name__, s.__class__.__name__)
        oldState = self.state
        self.state = s
        if self.session:
            self.session.set_state(oldState, self.state)

    def getSeq(self, msg):
        return msg.getHeader

    def sendHeartbeat(self):
        if self.state == self.normalMessageProcessing:
            msg = self.fix.Heartbeat()
            strMsg = self.session.compileMessage(msg)
            #print "Sending heartbeat ... %s" % strMsg
            msgSeqNum = msg.getHeaderFieldValue(self.fix.MsgSeqNum)

            log(">>> %s %s %s" % (msgSeqNum, msg, strMsg))
            self.transport.write(strMsg)
            #print "Scheduling heartbeat in %s " % self.heartbeatInterval
        else:
            print "NOT SENDING HEARTBEAT - dodgy state %s" % self.state
            # Depending on what you want to do this may or may not be useful
        # from observation when a large number of sessions connect at roughly
        # the same time the heartbeats can cause a 'wave' of messages every heartbeat
        # interval ( or multiple thereof ). We'll help the reactor out a bit by
        # adding a small randomization ( 1 second standard deviation ) to the interval
        # this shold be small enough to prevent any test request cycles but large enough
        # to smooth out heartbeats between multiple sessions
        delay = random.normalvariate(self.heartbeatInterval, 1)
        # Or if you're OCD or into Wagner/Kraftwerk/Techno you're  probably
        # not a fan of randomness and like regularly spaced metronomic 'doof's
        # - uncomment the line below delay = self.heartbeatInterval
        # delay = self.heartbeatInterval

        self.sendHeartbeatCall = reactor.callLater(delay, self.sendHeartbeat)
        # We'll rely on our heartbeat but 
        myObj = datetime.now()
        #self.heartBeatChecks[myObj] = reactor.callLater( self.heartBeatInterval * 1.5, self.checkHeartbeat, myObj )

    def onLogout(self, msg, inMsgSeqNum, possDupFlag):
        print "onLogout %s" % msg
        self.session.wantToBeLoggedOn = False
        msg = self.fix.Logout(fields=[self.fix.Text("Accepted logoff request")])
        strMsg = self.session.compileMessage(msg, persist=False)
        print ">>> %s" % strMsg
        self.transport.write(strMsg)
        self.transport.loseConnection()
        reactor.callLater(0, self.cleanUpAndDie)
        #self.cleanUpAndDie()

    def checkHeartbeat(self, token):
        assert self.heartBeatChecks.has_key(token)
        del self.heartBeatChecks[token]
        print "Check Heartbeat %s" % token
        if self.state == self.normalMessageProcessing:
            print "No heartbeat recieved for %s (%s seconds)" % (token, datetime.now() - token)
            challenge = "TEST_%s" % str(str(random.random())[2:15])
            testRequestId = self.fix.TestReqID(challenge)
            msg = self.fix.TestRequest(fields=[testRequestId])
            strMsg = self.session.compileMessage(msg)
            #print "Sending heartbeat ... %s" % strMsg
            msgSeqNum = msg.getHeaderFieldValue(self.fix.MsgSeqNum)
            print ">>> %s %s %s" % (msgSeqNum, msg, strMsg)
            self.transport.write(strMsg)
            self.testRequestChecks[challenge] = reactor.callLater(10, self.checkTestRequestAcknowledged, challenge)
        else:
            print "Skipping heartbeat checks - not in normal message processing phase"

    def checkTestRequestAcknowledged(self, challenge):
        assert self.testRequestChecks.has_key(challenge)
        print "He's out of there"
        msg = self.fix.Logout(fields=[self.fix.Text("No response to test request %s" % challenge)])
        strMsg = self.session.compileMessage(msg)
        #print "Sending Logon %s..." % strMsg
        msgSeqNum = msg.getHeaderFieldValue(self.fix.MsgSeqNum)
        print ">>> %s %s %s" % (msgSeqNum, msg, strMsg)
        self.transport.write(strMsg)
        # Bye bye
        self.transport.loseConnection()
        reactor.callLater(0, self.cleanUpAndDie)

    def _logoff(self, reason=None, extremePrejudice=False):
        """Don't call me - call the session objects logoff instead"""
        if not self.state == self.normalMessageProcessing:
            self.transport.loseConnection()
            self.cleanUpAndDie()

        if reason:
            fields = [self.fix.Text(reason)]
        else:
            fields = []

        msg = self.fix.Logout(fields)
        strMsg = self.session.compileMessage(msg)
        self.transport.write(strMsg)

        if extremePrejudice:
            reactor.callLater(0, self.cleanUpAndDie)
        else:
            self.setState(self.awaitingLogout)

    def cleanUpAndDie(self):
        # Get rid of the balls we've got already up in the air!
        # Note to self
        # I assume as long as code is logically correct I don't have to worry about

        if self.state == self.loggedOutState:
            print "Already cleaned up - nothing to do"
        else:
            self.setState(self.loggedOutState)
            calls = [self.sendHeartbeatCall] + self.testRequestChecks.values() + self.heartbeatChecks.values()
            for call in calls:
                if call:
                    try:
                        call.cancel()
                    except AlreadyCancelled:
                        pass

            #self.transport.loseConnection()
            self.loggedIn = False
            self.loggedOut = True
            self.parser = None

            # quick sanity checks on disconnect
            assert self.session is not None
            assert self.session.protocol is self
            self.session.releaseProtocol()
            print "Cleaned up"
            #del self.factory.protocols[self]

    def onHeartbeat(self, msg, seq, dup):
        testRequestID = msg.getField(self.fix.TestReqID)
        if testRequestID:
            #print "Have test request ID %s" % testRequestID
            challenge = testRequestID.value
            if self.testRequestChecks.has_key(challenge):
                self.testRequestChecks[challenge].cancel()
                del self.testRequestChecks[challenge]
            else:
                pass
                #print "Got testRequestID I didn't send!!! %s" % testRequestID
        else:
            now = datetime.now()
            for posted, cb in self.heartBeatChecks.items()[:]:
                #print "Clearing check %s %s after %s seconds" % ( callable, posted, (now-posted).seconds)
                cb.cancel()
                del self.heartBeatChecks[posted]

    def onTestRequest(self, msg, seq, dup):
        #print "onTestRequest %s" % msg
        testRequestId = msg.getField(self.fix.TestReqID)
        #assert self.loggedIn
        msg = self.fix.Heartbeat(fields=[testRequestId])
        strMsg = self.session.compileMessage(msg)
        #print "Test Request %s .. replying with %s" % (testRequestId, strMsg)
        self.transport.write(strMsg)

    def connectionMade(self):
        print "Connection Made"
        self.parser = FIXParser(self.fix,
                                self.onMsg)

    def dataReceived(self, data):
        #print "============================================"
        #print "Got some data!!! %s" % data
        self.parser.feed(data)

    def onResendRequest(self, msg, seq, dup):
        begin = msg.getFieldValue(self.fix.BeginSeqNo)
        tmpEnd = msg.getFieldValue(self.fix.EndSeqNo)
        resendDetails = []
        gap = None
        db = self.session.outDb
        if tmpEnd == 0:
            endSeqNo = self.session.outMsgSeqNum - 1
        else:
            endSeqNo = tmpEnd

        print "onResendRequest %s-%s Playing back %s-%s" % ( begin, tmpEnd, begin, endSeqNo)
        parser = SynchronousParser(self.fix)
        for i in range(begin, endSeqNo + 1):
            #print i , "... " ,
            haveMsg = False
            if db.has_key(i):
                fixMsg = db[i]
                msg, _, _ = parser.feed(fixMsg)
                #print "Recovered %s" % msg
                if msg.Section != 'Session':
                    # We have a message to resend
                    if gap:
                        resendDetails.append(gap)
                    gap = None
                    resendDetails.append(msg)
                    haveMsg = True
            if not haveMsg:
                if gap:
                    gap[1] = i
                else:
                    gap = [i, i]
        if gap:
            resendDetails.append(gap)

        print "Resend Details %s" % len(resendDetails)
        if 1:
            for obj in resendDetails:
                if type(obj) == ListType:
                    # Gap Fill
                    [sendSequenceNumber, lastSequenceNumber] = obj
                    #print "GapFill %s-%s" % (sendSequenceNumber, lastSequenceNumber)
                else:
                    origSeq = obj.getHeaderFieldValue(self.fix.MsgSeqNum)
                    #obj.dump( "GapFill>>>")
                    #print "gf2 =%s %s %s" % (obj, msg.getHeaderField( self.pyfix.MsgSeqNum ).value, origSeq )

        for obj in resendDetails:
            i = 0
            if type(obj) == ListType:
                # Gap Fill
                [sendSequenceNumber, lastSequenceNumber] = obj
                gapFill = self.fix.SequenceReset(fields=[self.fix.NewSeqNo(lastSequenceNumber + 1),
                                                         self.fix.GapFillFlag('Y')])
                fixMsg = self.session.compileMessage(gapFill, possDup=True, forceSequenceNumber=sendSequenceNumber)
                print "Sending sequence reset %s->%s %s" % ( sendSequenceNumber, lastSequenceNumber + 1, fixMsg)
                self.transport.write(fixMsg)
            else:
                # Hmm wonder if this will work. Header of old msg is going to be blatted
                origSeq = obj.getHeaderFieldValue(self.fix.MsgSeqNum)
                print "%10s %s" % (obj, origSeq)
                origSendingTime = obj.getHeaderFieldValue(self.fix.SendingTime)
                fixMsg = self.session.compileMessage(obj,
                                                     possDup=True,
                                                     forceSequenceNumber=origSeq,
                                                     origSendingTime=origSendingTime)
                #obj.dump("Recovered: " )
                #print "REC>>> %s %s %s" % (origSeq, obj, fixMsg)
                self.transport.write(fixMsg)
            i += 1
            if i % 100 == 0:
                print "Recovering %s ..."

    def onSequenceReset(self, msg, seq, dup):
        #print "onSequenceReset %s %s" % ( msg, msg.toFix() )
        isGapFill = msg.getOptionalFieldValue(self.fix.GapFillFlag)
        if isGapFill:
            self.onGapFill(msg)
        else:
            assert False, "Pure sequence reset not handled yet"

    def connectionLost(self, reason):
        if self.state != self.loggedOutState:
            print "PROTOCOL: Connection lost reason = %s" % reason
            self.cleanUpAndDie()
        else:
            print "Connection Closed"

    def onMsg(self, msg, data):
        msgClass = msg.__class__
        msgSeqNum = msg.getHeaderFieldValue(self.fix.MsgSeqNum)
        possDupFlag = msg.getHeaderFieldValue(self.fix.PossDupFlag)

        if self.session is not None:
            strSender = self.session.sender
        else:
            strSender = "UNKN"

        log("<<< %s %s %s->%s %s" % (strSender, msgSeqNum, msg, self.state, data))
        try:
            msg.validate()
        except MessageIntegrityException, e:
            print "Integrity Exception " + e.message
            e.msg.dump()
            self.session.lastIntegrityException = msg, e
            # No further processing required on a message that fails integrity checks
            if self.session.onIntegrityException:
                self.session.onIntegrityException(e)
            return
        except BusinessReject, br:
            self.lastBr = msg, br
            fields = [self.fix.RefSeqNum(msgSeqNum),
                      self.fix.Text(br.message)]
            if br.field is not None:
                fields.append(br.field)
            reject = self.fix.Reject(fields=fields)  # br.field = SessionRejectReason
            print "Creating reject - fields are %s" % str(fields)

            strReject = self.session.compileMessage(reject)
            self.transport.write(strReject)
            # Spec says messages which fail business validation sholud be logged + sequence numbers
            # incremented
            self.session.persistMsgAndAdvanceSequenceNumber(msg.toFix(), checkInSequence=True)
            return
            #return

        self.state.onMsg(msg, msgSeqNum, possDupFlag)
        if self.session is not None:
            self.session.lastByType[msgClass] = msg


class InitiatorFIXProtocol(FIXProtocol):
    AwaitingLogonKlazz = InitiatorAwaitingLogon

    def connectionMade(self):
        assert self.session is not None
        FIXProtocol.connectionMade(self)
        msg = self.fix.Logon(
            fields=[self.fix.EncryptMethod.NONEOTHER, self.fix.HeartBtInt(self.session.heartbeatInterval)])
        # THIS SHOULD BE SOME SORT OF METHOD
        strMsg = self.session.compileMessage(msg)
        msgSeqNum = msg.getHeaderFieldValue(self.fix.MsgSeqNum)
        print ">>> %s %s %s" % (msgSeqNum, msg, strMsg)
        self.transport.write(strMsg)


class AcceptorFIXProtocol(FIXProtocol):
    AwaitingLogonKlazz = AcceptorAwaitingLogon


class Session(object):
    def __init__(self, sessionManager, fix, config):
        self.sessionManager = sessionManager
        self.protocol = None
        self.fix = fix
        self.sender = config.sender
        self.target = config.target
        self.senderCompID = fix.SenderCompID(self.sender)
        self.targetCompID = fix.TargetCompID(self.target)
        self.beginString = fix.BeginString(fix.version)
        self.outMsgSeqNum = 1
        self.inMsgSeqNum = 1
        self.setPersister(BerkeleyPersister(config.persistRoot, self.sender, self.target))
        self.heartbeatInterval = config.heartbeatInterval
        # Why do we need an sp?
        self.sp = SynchronousParser(self.fix)
        self.lastByType = {}
        self.state = None
        if config.app:
            self.setApp(config.app)
        else:
            self.setApp(FIXApplication(fix))

        self.onIntegrityException = None
        self.lastIntegrityException = None
        self.wantToBeLoggedIn = True
        #self.app.setSession(self)


    def setApp(self, app):
        self.app = app
        self.app.setSession(self)

    def setState(self, oldState, newState):
        self.app.set_state(oldState, newState)

    def bindProtocol(self, protocol):
        assert self.protocol is None
        assert protocol.session is None
        protocol.session = self
        self.protocol = protocol
        self.app.setProtocol(protocol)

    def releaseProtocol(self):
        assert self.protocol.session == self
        assert self.protocol is not None
        self.protocol.session = None
        self.protocol = None

    def strConnected(self):
        return {True: " Connected  ",
                False: "Disconnected"}[self.isConnected()]

    def __repr__(self):
        return "Session(%s-%s %s [%s,%s] )" % (self.sender,
                                               self.target,
                                               self.strConnected(),
                                               self.inMsgSeqNum,
                                               self.outMsgSeqNum)

    def dumpIn(self, x):
        self.dumpMsg(self.inDb, x)

    def dumpOut(self, x):
        self.dumpMsg(self.outDb, x)

    def logoff(self, wantToBeLoggedOn=False):
        assert self.isConnected()
        self.wantToBeLoggedOn = wantToBeLoggedOn
        self.protocol._logoff()

    def logon(self): # This translates to "want to be logged on" for an acceptor!
        assert not self.isConnected()
        self.wantToBeLoggedIn = True
        if self.factory:
            assert self.factory.__class__ == InitiatorFactory, "Logic error only initiators keep track of factory"
            self.factory.logon()

    def dumpMsg(self, db, x):
        rawMsg = db[x]
        msg, x, y = self.sp.feed(rawMsg)
        msg.dump()
        print x, y

    def parse(self, msg):
        return self.sp.feed(msg)[0]

    def isConnected(self):
        return self.protocol is not None

    def setPersister(self, persister):
        self.persister = persister
        self.inDb, self.outDb = persister.getTodayPersister()
        #self.persister.report( self.inDb)
        #self.persister.report( self.outDb)
        p = SynchronousParser(self.fix)
        import time

        for db in ( self.inDb, self.outDb):
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

        self.inMsgSeqNum = self.persister.getNextSeq(self.inDb)
        self.outMsgSeqNum = self.persister.getNextSeq(self.outDb)
        print "Setting sequence numbers %s %s" % ( self.inMsgSeqNum, self.outMsgSeqNum)

    def persistMsgAndAdvanceSequenceNumber(self,
                                           msgText,
                                           checkInSequence=True):
        msg, _, _ = self.sp.feed(msgText)
        msgSeq = msg.getHeaderFieldValue(self.fix.MsgSeqNum)
        #print "Persisting %s vs %s" % (msgSeq, self.inMsgSeqNum)
        if checkInSequence:
            seq = self.persister.getNextSeq(self.inDb)
            seq2 = self.persister.getNextSeq(self.outDb)
            assert msgSeq >= seq, "Received %s vs %s %s" % (msgSeq, seq, seq2)

        self.persister.persistInMsg(msgSeq, msgText)
        # XXX Danger make sure this change was okay!!!
        self.inMsgSeqNum = msgSeq + 1

    def compileMessage(self,
                       msg,
                       possDup=False,
                       forceSequenceNumber=None,
                       origSendingTime=None,
                       persist=True,
                       disableValidation=False):

        sendingTime = self.fix.SendingTime(datetime.now())
        bodyLength = self.fix.BodyLength(0)
        checkSum = self.fix.CheckSum(0)

        if forceSequenceNumber:
            seq = forceSequenceNumber
        else:
            seq = self.outMsgSeqNum

        header = [self.beginString,
                  bodyLength,
                  msg.msgTypeField,
                  self.senderCompID,
                  self.targetCompID,
                  self.fix.MsgSeqNum(seq),
                  sendingTime
        ]

        if possDup:
            header = header[:-1] + [self.fix.PossDupFlag('Y')] + header[-1:]

        if origSendingTime:
            header = header[:-1] + [self.fix.OrigSendingTime(origSendingTime)] + header[-1:]

        footer = [checkSum]
        msg.headerFields = header
        msg.footerFields = footer

        # this will check what we've done so far
        #msg.checkStructure()
        #msg.validate()
        msg.calcBodyLength(mutate=True)
        msg.calcCheckSum(mutate=True)
        #msg.checkBodyLength()
        #bl2 = msg.calcBodyLength( )
        #cs2 = msg.calcCheckSum()

        if not disableValidation:
            msg.validate()
            #assert bl==bl2, "Body Length failed before/after consistency check"
        #assert cs==cs2, "Checksum failed before/after consistency check"

        ret = msg.toFix()
        if not possDup:
            if persist:
                self.persister.persistOutMsg(self.outMsgSeqNum, ret)
                #self.outDb[self.outMsgSeqNum] = ret
            #self.outDb.sync()
            self.outMsgSeqNum += 1
        return ret


class AcceptorFactory(Factory):
    initiator = False

    def __init__(self, sm, sessions):
        self.sm = sm
        self.sessions = sessions

    def addSession(self, idTuple, session):
        assert not self.sessions.has_key(idTuple)
        self.sessions[idTuple] = session

    def buildProtocol(self, addr):
        print "Build Protocol Instance %s %s" % (addr, self.sm.acceptorProtocol)
        p = self.sm.acceptorProtocol(self.sm.fix)
        p.factory = self
        return p

    def getSessionForMessage(self, msg):
        f = self.sm.fix
        # They're sending to us so we flip the usual sender/target
        # only used for logon at the moment
        idTuple = ( msg.getHeaderFieldValue(f.TargetCompID),
                    msg.getHeaderFieldValue(f.SenderCompID) )
        session = self.sessions.get(idTuple, None)
        print "Looked up session %s got %s %s" % (str(idTuple), str(session), self.sessions )
        if not session or not session.wantToBeLoggedIn:
            return None
        else:
            return session


class InitiatorFactory(ReconnectingClientFactory):
    #protocol = InitiatingFIXProtocol
    def __init__(self, sm, session, host, port):
        self.sm = sm
        self.session = session
        self.host = host
        self.port = port

    def logon(self):
        self.session.wantToBeLoggedOn = True
        assert self.session.protocol is None
        return reactor.connectTCP(self.host, self.port, self)

    #def logoff(self):
    #    assert self.session.protocol is not None
    #    self.wantToBeLoggedOn = False
    #    if self.session.protocol:
    #        self.session.protocol.logoff()

    def buildProtocol(self, addr):
        print "Build Protocol Instance %s" % addr
        p = self.sm.initiatorProtocol(self.sm.fix)
        p.factory = self
        self.session.bindProtocol(p)
        return p

    def startedConnecting(self, connector):
        print 'Started to connect.'

    def clientConnectionLost(self, connector, reason):
        print 'Lost connection.  Reason:', reason
        print "Wanttobelogged in %s %s" % (self, self.session.wantToBeLoggedOn)
        if not self.session.wantToBeLoggedOn:
            self.stopTrying()
        else:
            ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed. Reason:', reason
        if not self.session.wantToBeLoggedOn:
            self.stopTrying()
        else:
            ReconnectingClientFactory.clientConnectionFailed(self, connector,
                                                             reason)


class SessionExistsException(Exception):
    pass

# Don't know if this was particularly wise.
# One sessino manager which manages incoming and outgoing sessions
class SessionManager(object):
    protocolKlazz = FIXProtocol

    def __init__(self,
                 spec,
                 config,
                 initiatorProtocol=InitiatorFIXProtocol,
                 acceptorProtocol=AcceptorFIXProtocol):
    #senderCompID,
    #targetCompID):
        self.fix = spec
        self.config = config
        self.sessionLookup = {}

        self.initiatorProtocol = initiatorProtocol
        self.acceptorProtocol = acceptorProtocol

        self.beginString = self.fix.BeginString(self.fix.version)

        self.sessionByTuple = {}
        self.acceptorsByTuple = {}
        self.initiatorsByTuple = {}

        self.acceptorsByPort = defaultdict(lambda: {})
        self.initiatorFactories = []
        self.acceptorFactories = {}
        self.sessions = []

        self.perspective = None

        for s in config:
            idTuple = ( s.sender, s.target )
            session = Session(self, spec, s)
            self.sessions.append(session)
            self.sessionByTuple[idTuple] = idTuple
            if s.connectionType == 'initiator':
                #session.host = s.host
                #session.port = s.port
                f = InitiatorFactory(self, session, s.host, s.port)
                session.factory = f
                self.initiatorFactories.append(f)
                self.initiatorsByTuple[idTuple] = session
            else:
                assert s.connectionType == 'acceptor', "Must be acceptor or initiator"
                self.acceptorsByPort[s.port][idTuple] = session
                self.acceptorsByTuple[idTuple] = session
            self.sessionByTuple[idTuple] = session

        for port, sessionMap in self.acceptorsByPort.items():
            af = AcceptorFactory(self, sessionMap)
            self.acceptorFactories[port] = af
        self.sp = SynchronousParser(self.fix)

    def addSession(self, sessionConfig, initiateImmediately=True):
        ### FIXME XXX Untested - i.e. UN*RUN* - check this works
        idTuple = ( sessionConfig.sender, sessionConfig.target)
        if self.sessionByTuple.has_key(idTuple):
            raise SessionExistsException()
        session = Session(self, self.fix, sessionConfig)
        if sessionConfig.connectionType == 'initiator':
            f = InitiatorFactory(self, session, sessionConfig.host, sessionConfig.port)
            session.factory = f
            self.initiatorFactories.append(f)
            self.initiatorsByTuple[idTuple] = session

            if initiateImmediately:
                f.logon()
        else:
            assert sessionConfig.connectionType == 'acceptor', "Must be acceptor or initiator"
            # XXX Note to self. I'm populating these structures so as to keep them consistent
            # but might make sense to figure out which structures are 'scaffolding' for the
            # initial session creation and which need to be 'maintained'
            self.acceptorsByPort[sessionConfig.port][idTuple] = session
            self.acceptorsByTuple[idTuple] = session

            # If we're adding an acceptor to a port that's already listeneing
            # it's enough to just add it to the config.. when someone asks to logon
            # the structure will be there :-)
            if not self.acceptorsByPort.has_key(sessionConfig.port):
                sessionMap = {idTuple: session}
                af = AcceptorFactory(self, sessionMap)
                self.acceptorFactories[sessionConfig.port] = af
            else:
                self.acceptorFactories[sessionConfig.port].addSession(session)

        self.sessionByTuple[idTuple] = session

        for port, sessionMap in self.acceptorsByPort.items():
            af = AcceptorFactory(self, sessionMap)
            self.acceptorFactories[port] = af

    def getConnected(self):
        for port, factory in self.acceptorFactories.items():
            print "Starting acceptor %s" % port
            port = reactor.listenTCP(port, factory)
            print "Port is %s" % port.getHost().port

        for f in self.initiatorFactories:
            print "Startign initiator %s %s %s" % ( f.host, f.port, f)
            f.logon()
            #reactor.connectTCP( f.host, f.port, f)

    # Utility for the remote interfaces
    def dump(self):
        print "INITIATORS"
        print "========="
        for x in self.initiatorsByTuple.items():
            print x

        print "ACCEPTORS"
        print "========="
        for x in self.acceptorsByTuple.items():
            print x


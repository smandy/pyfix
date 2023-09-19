# Our own copy of session.compile message
# Guess it doesn't matter if this drifts from the
# definition on the session class

from testFIXSession import fix
from datetime import datetime

def compileMessageNoPersist(self,
                            msg,
                            possDup=False,
                            forceSequenceNumber=None,
                            _origSendingTime=None,
                            _persist=True,
                            _disableValidation=False):
    sendingTime = fix.SendingTime(datetime.now())
    bodyLength = fix.BodyLength(0)
    checkSum = fix.CheckSum(0)

    if forceSequenceNumber:
        seq = forceSequenceNumber
    else:
        seq = self.outMsgSeqNum

    print(f"{self.sender} compilemessage {seq}")
    header = [self.beginString,
              bodyLength,
              msg.msgTypeField,
              self.senderCompID,
              self.targetCompID,
              self.fix.MsgSeqNum(seq),
              sendingTime
              ]

    footer = [checkSum]
    msg.headerFields = header
    msg.footerFields = footer

    msg.calc_body_length(mutate=True)
    msg.calc_check_sum(mutate=True)

    ret = msg.to_fix()

    # Persisting a message with a bad sequence number is bad news.
    # so many things go wrong with it!

    if not possDup:
        # self.persister.persistOutMsg( self.outMsgSeqNum, ret )
        # self.outDb[self.outMsgSeqNum] = ret
        # self.outDb.sync()
        self.outMsgSeqNum += 1
    return ret


def compileMessageOmitSequenceNumber(self,
                                     msg,
                                     possDup=False,
                                     _forceSequenceNumber=None,
                                     _origSendingTime=None,
                                     _persistTrue=None,
                                     _disableValidation=False):
    sendingTime = fix.SendingTime(datetime.now())
    bodyLength = fix.BodyLength(0)
    checkSum = fix.CheckSum(0)

    header = [self.beginString,
              bodyLength,
              msg.msgTypeField,
              self.senderCompID,
              self.targetCompID,
              sendingTime
              ]

    footer = [checkSum]
    msg.headerFields = header
    msg.footerFields = footer

    msg.calc_body_length(mutate=True)
    msg.calc_check_sum(mutate=True)

    ret = msg.to_fix()

    # Persisting a message with a bad sequence number is bad news.
    # so many things go wrong with it!
    if not possDup:
        self.outMsgSeqNum += 1
        #    self.persister.persistOutMsg( self.outMsgSeqNum, ret )
        #    #self.outDb[self.outMsgSeqNum] = ret
        # self.outDb.sync()
        return ret


def compileMessageOmitMandatoryHeaderField(self,
                                           msg,
                                           possDup=False,
                                           _forceSequenceNumber=None,
                                           _origSendingTime=None,
                                           _persist=True,
                                           disableValidation=False):
    # _sendingTime = fix.SendingTime(datetime.now())
    bodyLength = fix.BodyLength(0)
    checkSum = fix.CheckSum(0)

    seq = self.outMsgSeqNum

    header = [self.beginString,
              bodyLength,
              msg.msgTypeField,
              self.senderCompID,
              self.targetCompID,
              self.fix.MsgSeqNum(seq),
              ]

    footer = [checkSum]
    msg.headerFields = header
    msg.footerFields = footer

    msg.calc_body_length(mutate=True)
    msg.calc_check_sum(mutate=True)

    if not disableValidation:
        msg.validate()

    ret = msg.to_fix()
    if not possDup:
        self.outMsgSeqNum += 1
    return ret


from datetime import datetime
from makeSpec import fix

class DummySession:
    def __init__(self,
                 beginString, 
                 senderCompID,
                 targetCompID ):

        self.sender = senderCompID
        self.target = targetCompID
        
        self.beginString  = fix.BeginString( beginString )
        self.senderCompID = fix.SenderCompID( senderCompID )
        self.targetCompID = fix.TargetCompID( targetCompID )
        self.outMsgSeqNum = 1
        self.inMsgSeqNum  = 1
        
        #self.bodyLength = pyfix.BodyLength(0)
        #self.checkSum   = pyfix.CheckSum( 0 )

    def setPersister(self, persister):
        self.persister = persister

    def compileMessage(self, msg):
        sendingTime = fix.SendingTime( datetime.now() )
        bodyLength = fix.BodyLength(0)
        checkSum   = fix.CheckSum(0)

        header = [ self.beginString,
                   bodyLength,
                   msg.msgTypeField,
                   self.senderCompID,
                   self.targetCompID,
                   fix.MsgSeqNum(self.msgSeqNum),
                   sendingTime]

        footer = [ checkSum ]
        msg.headerFields = header
        msg.footerFields = footer

        # this will check what we've done so far
        msg.checkStructure()
        msg.validate()

        bl = msg.calcBodyLength( mutate = True)
        cs = msg.calcCheckSum( mutate = True )
        msg.checkBodyLength()
        bl2 = msg.calcBodyLength( )
        cs2 = msg.calcCheckSum()
        print bl, bl2, cs, cs2
        self.msgSeqNum += 1



from twisted.internet.protocol import Protocol, ClientFactory

class Session(ClientFactory):
    def __init__(self,
                 beginString, 
                 senderCompID,
                 targetCompID ):

        self.sender = senderCompID
        self.target = targetCompID
        
        self.beginString  = fix.BeginString( beginString )
        self.senderCompID = fix.SenderCompID( senderCompID )
        self.targetCompID = fix.TargetCompID( targetCompID )
        self.outMsgSeqNum = 1
        self.inMsgSeqNum  = 1
        
        #self.bodyLength = pyfix.BodyLength(0)
        #self.checkSum   = pyfix.CheckSum( 0 )

    def setPersister(self, persister):
        self.persister = persister

    def compileMessage(self, msg):
        sendingTime = fix.SendingTime( datetime.now() )
        bodyLength = fix.BodyLength(0)
        checkSum   = fix.CheckSum(0)

        header = [ self.beginString,
                   bodyLength,
                   msg.msgTypeField,
                   self.senderCompID,
                   self.targetCompID,
                   fix.MsgSeqNum(self.msgSeqNum),
                   sendingTime]

        footer = [ checkSum ]
        msg.headerFields = header
        msg.footerFields = footer

        # this will check what we've done so far
        msg.checkStructure()
        msg.validate()

        bl = msg.calcBodyLength( mutate = True)
        cs = msg.calcCheckSum( mutate = True )
        msg.checkBodyLength()
        bl2 = msg.calcBodyLength( )
        cs2 = msg.calcCheckSum()
        print bl, bl2, cs, cs2
        self.msgSeqNum += 1




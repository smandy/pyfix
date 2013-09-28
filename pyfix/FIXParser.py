# $Header: /Users/andy/cvs/dev/python/phroms/fix/FIXParser.py,v 1.17 2009-03-02 02:19:19 andy Exp $

from pprint import pprint as pp
from FIXSpec import SOH, BusinessReject

FIX_PREAMBLE = "8=FIX"
FIX_PREAMBLE_FIELDPAIR = FIX_PREAMBLE.partition("=")

class ParseException(Exception):
    pass

class FIXParser:
    def __init__(self ,
                 spec,
                 cb = None,
                 onDiscard = None,
                 sendData  = True):
        self.fix = spec
        self.buf = ''
        if cb is None:
            self.callback = self.printMsg
        else:
            self.callback = cb

        self.onDiscard = onDiscard
        self.minSize = sum( [ len(x.Tag) + 2 for x in self.fix.StandardHeader.mandatoryFields +
                                                      self.fix.StandardTrailer.mandatoryFields ] )
        self.sendData = sendData
        self.reset()
        
    def printMsg(self, msg, data = ''):
        print "%s %s" % (msg, data )

    def reset(self):
        self.buf = ''
        self.triplets = [ ]
        self.bytesInBuffer = 0

    def checksum(self):
        return sum( [ len(x[1])+1 for x in self.triplets ] ) + len(self.buf)

    def _feed(self, data):
        self._feed( data)
        pp( { "buf"      : self.buf,
              "triplets" : self.triplets,
              "checksum" : self.checksum(), 
              "bytes"    : self.bytesInBuffer  } )
        assert self.bytesInBuffer == self.checksum(), "consistency check have %s bytes but calculate %s" % (self.bytesInBuffer,self.checksum() ) 

    def feed(self, data):
        fix = self.fix
        #self.consumed += chunkSize
        self.buf += data
        self.bytesInBuffer += len(data)
        
        if not self.bytesInBuffer > self.minSize:
            return

        if not "10=" in self.buf:
            return
            #self.bytesInBuffer

        # Not even worth trying up till this point
        # partition string gives a list of 3-tuples.
        # can ensure our fields are well-formed
        # partition -> [ ( '8' ,'=','FIX' ), ( '35' ,'=','D' ) ....
        bits = [ (x.partition('='), x) for x in self.buf.split(SOH) ]
        if self.buf.endswith(SOH):
            # Clean message. Blat the buffer
            self.buf = ''
            x = bits.pop() # Trailing SOH needs to be consumed
        else:
            # Push trailing field back onto the buffer
            remainder = bits.pop()[1]
            #print "Pushing %s back onto buffer - start of a new field that's not been terminated yet" % remainder
            self.buf = remainder
        self.triplets += bits
        
        while self.triplets and not self.triplets[0][1].startswith(FIX_PREAMBLE):
            self.bytesInBuffer -= len(self.triplets[0][1])
            if self.onDiscard:
                crud = self.triplets[0][1] + SOH
                self.onDiscard(crud)
                
            #print "Removing %s" % str(self.triplets[0])
            self.triplets.remove( self.triplets[0] )

        # These turned out to be hotspots so we'll look them up outside the main loop
        msgTypeTag        = fix.MsgType.Tag
        checkSumTag       = fix.CheckSum.Tag
        #sequenceNumberTag = pyfix.MsgSeqNum.Tag
        
        # Okay by now we've consumed all fieldpairs, put whatever isn't a pair back on the buffer,
        # and consumed everything up to the sync FIX= tag
        #fieldCollector = (headerFields, messageFields, footerFields) = ( [], [], [] )
        msgClass, startIdx, fieldCollector, l = None, 0, ( [], [], [] ), 0
        exception      = None
        
        for i,( (key, sep, val), originalField ) in enumerate(self.triplets):
            # Okay we took out time to complain about malformed field but
            # since it's game over we've only delayed the inevitable by a small
            # amount of time :-)
            if not sep:
                raise ParseException( "Malformed field %s" % originalField )
            l += len(originalField)+1

            # This looks like a noop but has the side effect of adding the created field to the appropriate
            # collector bucket
            fix.fieldByID[key](val, isNative=False, collector=fieldCollector)

            if key==msgTypeTag:
            #if isinstance( field, self.pyfix.MsgType):  -> Hotspot
                msgClass  = fix.messageByID.get(val, fix.UnknownMessage)
                if msgClass==fix.UnknownMessage:
                    exception = BusinessReject( "Unknown Message Type %s" % val,
                                                None,
                                                fix.SessionRejectReason.INVALIDMSGTYPE )
            elif key==checkSumTag:
            #elif isinstance( field, self.pyfix.CheckSum): -> HotSpot
                if not msgClass:
                    # At this point all bets are off
                    self.reset()
                    raise ParseException( "Have checksum but no MsgType") # Spec says we don't need to respond - malformed message
                # At this point we know we've got something of reasonable size
                # isnative = False will force parse
                #print fieldCollector

                msg = msgClass( headerFields = fieldCollector[0],
                                fields       = fieldCollector[1],
                                footerFields = fieldCollector[2],
                                isNative = True)
                msg.exception      = exception
                
                self.bytesInBuffer -= l
                msgClass, fieldCollector, l = None, ( [], [], []), 0

                if self.sendData:
                    asFix = "".join( x[1]+SOH for x in self.triplets[startIdx:i+1] )
                    if asFix!=msg.toFix():
                        print asFix
                        print msg.toFix()
                        
                    #assert asFix == msg.toFix(), "Consistency failed :-("
                else:
                    asFix = None
                startIdx=i+1
                self.callback( msg , data = asFix )
                
        if startIdx:
            # Need to slice off everything *beyond* the index
            # otherwise end up with loads of checksums
            self.triplets = self.triplets[startIdx:]

class SynchronousParser(FIXParser):
    def __init__(self, spec):
        FIXParser.__init__(self,
                           spec,
                           cb = self.collect,
                           onDiscard = self.discard ,
                           sendData = False)
    
    def collect( self, msg, data = ''):
        self.msg       = msg
        self.fixString = data

    def discard(self, x):
        self.discarded += x

    def reset(self):
        FIXParser.reset(self)
        self.msg       = None
        self.fixString = None
        self.discarded = ''

    def feed(self, data):
        FIXParser.feed( self, data)
        ret = self.msg, self.fixString, self.discarded
        if self.msg is None:
            raise ParseException("Problem parsing message")
        self.reset()
        return ret

    parse = feed
    

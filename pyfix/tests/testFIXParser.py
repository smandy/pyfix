from pyfix.BerkeleyPersister import BerkeleyPersister
from pyfix.FIXSpec           import parse_specification
from pyfix.FIXParser         import FIXParser

import os.path
import unittest


# Another Noddy Change

class Concat:
    def __init__(self):
        self.buf = ''
        self.messages = 0
        self.discardBuffer = ''

    def onMsg(self,  x , data):
        self.messages += 1
        self.buf += x.to_fix()
        x.validate()

    def onDiscard(self, x):
        #print "Discard : %s" % str(x)
        self.discardBuffer += x

class DoFp( unittest.TestCase ):
    def setUp(self):
        print "Setup!!!"
        from datetime import datetime

        for relpath in [ '../data', './data' ]:
            fp = os.path.abspath( relpath)
            if os.path.exists(fp):
                break
        print fp
        self.bp = BerkeleyPersister( fp, "SENDER","PHROMS", dt = datetime( 2009, 1, 11) )
        self.spec = parse_specification(version = "FIX.4.2")
        (self.inDb,self.outDb) = self.bp.getTodayPersister( )
        # data can arrive in arbitrary shapes and sizes so need
        # to ensure that a parser can cope with all the data ( even byte-at-a-time)
        print [ x.partition("=") for x in "a=b|".split("|") ]
        print [ x.partition("=") for x in "a=b|c".split("|") ]
        print [ x.partition("=") for x in "a=b|c=".split("|") ]
        print [ x.partition("=") for x in "a=b|c=d".split("|") ]

        print self.inDb.stat()

        # Build a big pyfix string
        c = self.inDb.cursor()
        self.megaString = ''
        messages = 0
        while True:
            i_s = c.next()
            if not i_s:
                break
            _, s = i_s
            self.megaString+= s
        print "Megastring is %s long" % len(self.megaString )

    def _test_basic(self):
        # Test the first
        fp = FIXParser(self.spec)
        def doit(x):
            c = x.cursor()
            while True:
                d = c.next()
                if not d:
                    break
                #print d
                print "=" * 80
                print d[1]
                fp.feed(d[1])
        print "In"
        print "=" * 80
        doit( self.inDb )
        print "Out"
        print "=" * 80
        doit( self.outDb )

    def testBigStringOneByteAtATime(self):
        cat = Concat()
        fp = FIXParser(self.spec, cb = cat.onMsg)
        for x in self.megaString:
            fp.feed(x)
        assert cat.buf == self.megaString

    def testBigString(self):
        # Feed the whole thing
        cat2 = Concat()
        fp2 = FIXParser(self.spec,cb = cat2.onMsg)
        fp2.feed(self.megaString)
        assert cat2.buf == self.megaString

    def testDodgyStart(self):
        for i in range(0, len(self.megaString), 10):
            cat = Concat()
            fp = FIXParser(self.spec, cb = cat.onMsg,
                           on_discard= cat.onDiscard)
            s = self.megaString[i:]
            fp.feed(s)
            check =len(cat.buf) +fp.checksum() + len(cat.discardBuffer)  
            assert check == len(s)
            if i % 100 == 0:
                print "%s -> %s..." % (i, cat.messages)
                print "%s bytes sent. %s accounted for (%s parsed %s inbuffer %s discarded" % (len(s), check, len(cat.buf), fp.checksum(), cat.discardBuffer)

    def testDodgyEnd(self):
        for i in range(0, len(self.megaString), 10):
            cat = Concat()
            fp = FIXParser(self.spec, cb = cat.onMsg,
                           on_discard= cat.onDiscard)
            s = self.megaString[:i]
            fp.feed(s)
            check =len(cat.buf) +fp.checksum() + len(cat.discardBuffer)  
            self.assertEqual( check , len(s) )
            if i % 100 == 0:
                print "%s -> %s..." % (i, cat.messages)
                print "%s bytes sent. %s accounted for (%s parsed %s inbuffer %s discarded" % (len(s), check, len(cat.buf), fp.checksum(), cat.discardBuffer)

def test_suite():
    def s(test_class):
        return unittest.makeSuite( test_class)

    def s2(test_class):
        return unittest.TestLoader().loadTestsFromTestCase( DoFp )
    suite = unittest.TestSuite()
    suite.addTests( [ s2(DoFp) ]  )
    return suite
    
if __name__=='__main__':
    import unittest
    unittest.main(defaultTest='test_suite' )
            


import unittest


from pyfix.FIXSpec import parse_specification
from pyfix.FIXParser import SynchronousParser
import os
from pyfix.FIXConfig import SessionConfig

import tempfile

TEST_VERSIONS = ['FIX.4.0',
                 'FIX.4.1',
                 'FIX.4.3',
                 'FIX.4.4',
                 #'FIX.5.0',
                 #'FIX.5.0SP1',
                 'FIX.4.2']

TEST_VERSIONS=['FIX.4.0',
               'FIX.4.1',
               'FIX.4.2',
               'FIX.4.3' ]

TEST_VERSIONS=['FIX.4.2']

class SpecTester(unittest.TestCase):
    version = '4.1'
    
    def __repr__(self):
        return "SpecTester(%s,%s)" % (self.version, self.testMethod)

    __str__=__repr__
    
    def __init__(self, testMethod, version = 'FIX.4.0' ):
        # NB nose wants the init method of a testcase to 
        unittest.TestCase.__init__(self, methodName = testMethod)
        self.version = version
        self.testMethod = testMethod

    def setUp( self):
        self.fix = parse_specification( self.version )
        self.fp = SynchronousParser(self.fix)
        
        self.sendConfig = SessionConfig( 'initiator',
                                         0,
                                         'localhost',
                                         'INITIATOR',
                                         'ACCEPTOR',
                                         os.path.join( tempfile.mktemp(), "sender" ), # Will be tempfile
                                         60,
                                         None
                                         )
        self.ds = Session( None, self.fix, self.sendConfig)
        major, minor = self.version.split('.')[1:]
        self.numVersion = int(major) * 10 + int(minor)
        print "NV = %s" % self.numVersion 

    def test_parse(self):
        codex = [
            [ "ExecID('102')"        , None ],
            [ "OrdStatus.FILLED"     , None ],
            [ "OrderID('myOrderID')" , None ],
            [ "ExecTransType.NEW"    , lambda x,y: y<43 ], # Got dropped in 43
            [ "Symbol( 'CSCO')"      , None ],
            [ "AvgPx( 32.34 )"       , None ],
            [ "LastPx( 32.34 )"      , None ],
            [ "Side.BUY"             , None ],
            [ "ExecType.NEW"         , lambda x,y: y>40 ],
            [ "OrderQty(300)"        , None ],
            [ "CumQty( 100)"         , None ],
            [ "LastShares( 100)"     , lambda x,y: y<43],
            [ "LastQty( 100)"        , lambda x,y: y>42 ],
            [ "LeavesQty( 200)"      , lambda x,y: y>40 ],
            [ "ClOrdID( 'MYOrder')"  , None ] ]

        fields = []
        for expr, cond in codex:
            if cond is None or cond(self.fix.version, self.numVersion ):
                fields.append( eval("self.pyfix.%s" % expr ) )
        
##         msg = self.pyfix.ExecutionReport( fields = [self.pyfix.ExecID( '102'),
##                                              self.pyfix.OrdStatus.FILLED,
##                                              self.pyfix.OrderID('myOrderID'),
##                                              self.pyfix.ExecTransType.NEW,
##                                              self.pyfix.Symbol( 'CSCO'),
##                                              self.pyfix.AvgPx( 32.34 ),
##                                              self.pyfix.Side.BUY,
##                                              self.pyfix.ExecType.NEW,
##                                              self.pyfix.OrderQty(300),
##                                              self.pyfix.CumQty( 100),
##                                              self.pyfix.LeavesQty( 200),
##                                              self.pyfix.ClOrdID( "ORDER_2232") ] )
        msg = self.fix.ExecutionReport( fields = fields )
        asFix = self.ds.compile_message(msg)
        msg2, _ ,_ = self.fp.feed(asFix)
        self.assertEqual( msg2.to_fix(), asFix)

def test_suite():
    print "Suite Called!"
    s = unittest.TestSuite()
    for version in TEST_VERSIONS:
        for testMethod in ['test_parse']:
            print testMethod, version
            s.addTest( SpecTester( testMethod, version) )
    return s

if __name__=='__main__':
    unittest.main(defaultTest='test_suite' )

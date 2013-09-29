from pyfix.FIXSpec import parse_specification, BusinessReject
import unittest

from datetime import datetime 

fix = parse_specification( 'FIX.4.2')

#Noddy Change

class FieldTest( unittest.TestCase ):
    def __str__(self):
        return "%s %s" % ( unittest.TestCase.__str__(self), self.field.to_fix() )

    __repr__=__str__

    def __init__(self, *args, **kwargs):
        # TestCase docs says sholdn't mess with the signature.
        self.field = kwargs['field']
        del kwargs['field']
        unittest.TestCase.__init__(self, *args, **kwargs)
    
    def test_success(self):
        """Works"""
        self.field.validate( fix)

    def test_failure(self):
        self.assertRaises( BusinessReject, self.field.validate, fix)

shouldPass = [ fix.ClOrdID('wayhey' ),
               fix.OrderQty(100),
               fix.SendingTime( datetime.now() ),
               fix.ClOrdID( 'wayhey', is_native = False ),
               fix.OrderQty( '100', is_native= False ),
               fix.SendingTime("20090212-18:47:18", is_native = False),
               fix.LastPx( 23.45 ),
               fix.LastPx( '23.45', is_native= False),
               fix.Side('1'),
               fix.Side('1', is_native = False),
               fix.PossDupFlag( 'Y', is_native = False ),
               fix.PossDupFlag( 'N', is_native = False ),
               ]

shouldFail  = [
    fix.OrderQty('Invalid'),
    fix.OrderQty(None),
    fix.SendingTime('now'),
    fix.SendingTime( 23.45),
    fix.SendingTime(None),
    fix.OrderQty('wayhey'),
    fix.SendingTime( '290212-8:47:18', is_native = False), # i.e. malformed!
    fix.Side('', is_native = False),
    fix.Side('0'),
    fix.Side('0', is_native = False),
    fix.PossDupFlag( 'Z', is_native = False)
            ]



def test_suite():
    suite = unittest.TestSuite()
    for x in shouldPass:
        suite.addTest( FieldTest( 'test_success', field=x) )
        
    for x in shouldFail:
        suite.addTest( FieldTest( 'test_failure', field=x) )
    return suite
    
if __name__=='__main__':
    import unittest
    unittest.main(defaultTest='test_suite' )
            

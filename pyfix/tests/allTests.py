import testFIXParser
import testFIXSpec
import testFields
import testFIXSession
import testRejects
import testIntermittentGaps

import unittest

def test_suite():


    modules = [testFIXParser,
               testFIXSpec,
               testFields,
               testFIXSession,
               testRejects,
               testIntermittentGaps ]

    suites = [ x.test_suite() for x in modules ]
    
    
    return unittest.TestSuite( suites )

if __name__=='__main__':
    unittest.main(defaultTest = 'test_suite' )
    

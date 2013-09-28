# $Header: /Users/andy/cvs/dev/python/phroms/core/IOEParser.py,v 1.7 2009-01-09 22:48:15 andy Exp $


from phroms.messages.Order import Order
from phroms.messages.enum import Side

from phroms.core.ClOrdIDGen      import ClOrdIDGen
from phroms.core.AccountManager  import AccountManager
from phroms.core.BrokerManager   import BrokerManager
from phroms.core.SecurityManager import SecurityManager
from phroms.core.Security        import Security

import traceback
import re
from pprint import pprint as pp

from phroms.util.attr_setter import attr_setter
        
class IOEParser(object):
    """
    iob2500csco
    iob2500csco 201 cap
    ios3200mfnx
    """
    ioe = re.compile( "IO([BS])([0-9]+)([A-Z]+)")
    defaultAccount = "ANDY"

    __metaclass__, attrs = attr_setter, [ 'clOrdIDGenerator','securityManager','brokerManager']

    def __init__(self, idGenerator = ClOrdIDGen() ):
        self.accountManager = AccountManager()
        self.brokerManager  = BrokerManager()
        self.sm             = SecurityManager()
        self.idGenerator    = idGenerator
        self.clOrdIDGenerator = None
        self.securityManager  = None
        self.brokerManager    = None

    def parse(self, s):
        try:
            s = s.upper()
            match = self.ioe.match(s)
            if match:
                (buySell, qty, strSec) = match.groups()
                print "match", match.groups()
                if buySell[0]=='B':
                    buySell = Side.BUY
                else:
                    buySell = Side.SELL

                if self.sm:
                    sec = self.sm.getByFields( [ 'ticker','ric'], strSec)
                    if not sec:
                        return None
                else:
                    sec = Security()
                    sec.ticker = strSec
                qty = int(qty)
                return Order( self.clOrdIDGenerator.makeClOrdID(),
                              sec,
                              int(qty),
                              buySell,
                              self.accountManager.getDefault(),
                              self.brokerManager.getDefault(),
                              px= 0.0 )
        except:
            traceback.print_exc()
            return None
            
if __name__=='__main__':
    ioe = IOEParser()
    s = None
    if 0:
        while not s=='quit':
            s=raw_input()
            ret =ioe.parse(s)
            print ret
        
    o = ioe.parse('iob2500msft')
    print o

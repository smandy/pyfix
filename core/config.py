# $Header: /Users/andy/cvs/dev/python/phroms/core/config.py,v 1.2 2009-01-09 22:48:15 andy Exp $

from phroms.core.AccountManager   import AccountManager
from phroms.core.SecurityManager  import SecurityManager
from phroms.core.OrderGenerator   import OrderGenerator
from phroms.core.OrderManager     import OrderManager
from phroms.tx.fixConverters import FixConverter
from phroms.core.BrokerManager    import BrokerManager
from phroms.core.ClOrdIDGen       import ClOrdIDGen
from phroms.core.ExecIDGen        import ExecIDGen
from phroms.core.PortfolioManager import PortfolioManager

def getSensibleDefaults():
   ret =  { 'accountManager'   : AccountManager()   ,
            'securityManager'  : SecurityManager()  ,
            'orderGenerator'   : OrderGenerator()   ,
            'fixConverter'     : FixConverter()     ,
            'brokerManager'    : BrokerManager()    ,
            'portfolioManager' : PortfolioManager() , 
            'clOrdIDGenerator' : ClOrdIDGen()       ,
            'execIDGen'        : ExecIDGen()        ,
            'orderManager'     : OrderManager() }
   return ret
   
if __name__=='__main__':
    from pprint import pprint as pp
    s = getSensibleDefaults()
    pp(s)

# $Header: /Users/andy/cvs/dev/python/pyfix/core/config.py,v 1.2 2009-01-09 22:48:15 andy Exp $

from pyfix.core.AccountManager   import AccountManager
from pyfix.core.SecurityManager  import SecurityManager
from pyfix.core.OrderGenerator   import OrderGenerator
from pyfix.core.OrderManager     import OrderManager
from pyfix.tx.fixConverters import FixConverter
from pyfix.core.BrokerManager    import BrokerManager
from pyfix.core.ClOrdIDGen       import ClOrdIDGen
from pyfix.core.ExecIDGen        import ExecIDGen
from pyfix.core.PortfolioManager import PortfolioManager

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

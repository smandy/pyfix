# $Header: /Users/andy/cvs/dev/python/phroms/core/SecurityManager.py,v 1.7 2009-01-09 16:27:50 andy Exp $ 

from Manager import Manager
from Security import Security

secDefaults = """
id,ticker,ric,bloombergTicker,sedol,exchange
1,VOD,VOD.L,VOD LN Equity,76435,LSE
2,GS,GS.N,GS US Equity,12345,NYSE
3,CSCO,CSCO.O,CSCO US Equity,43101,OTC
4,INTC,INTC.O,INTC US Equity,43102,OTC
5,MSFT,MSFT.O,MSFT US Equity,43105,OTC
6,GLW,GLW.N,GLW US Equity,43205,OTC
6,PEB,PEB.N,PEB US Equity,43205,OTC
"""

class SecurityManager(Manager):
    def __init__(self,manageClass = Security, defaults = secDefaults):
        Manager.__init__(self, manageClass, defaults)
        self.byRic    = self.indexBy('ric')
        self.byTicker = self.indexBy('ticker')
        self.byName   = self.byTicker # Ticker is the default

    def get(self, strSecurity):
        # Default get implementation - lookup by ticker + ric
        return self.getByFields( strSecurity, [ 'ric','ticker'] )


        
if __name__=='__main__':
    sm = SecurityManager()


    

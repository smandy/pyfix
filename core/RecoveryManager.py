# $Header: /Users/andy/cvs/dev/python/phroms/core/RecoveryManager.py,v 1.5 2009-01-09 22:48:15 andy Exp $

import time
from phroms.messages.Order     import Order
from phroms.messages.Execution import Execution

# XXX Pull from config
DISPLAY_EVERY_N_RECOVERED_ORDERS = 5000

class RecoveryManager(object):
    def __init__(self):
        self.recoveryMap = {}
        self.inRecovery = False

    def setSecurityManager(self, sm):
        self.sm = sm

    def setAccountManager(self, am):
        self.am = am
        
    def setOrderManager(self, orderManager):
        self.orderManager = orderManager
        self.recoveryMap[ Order ]     = self.orderManager.onRecoveredOrder
        self.recoveryMap[ Execution ] = self.orderManager.on_execution

    def setPersister(self, p):
        self.persister = p
        
    def recover(self):
        self.inRecovery = True
        recoveredObjects = 0
        startTime = time.time()
        print "Recovery starting %s" % time.asctime(time.localtime(time.time()))
        while 1:
            obj = self.persister.readObject()
            if not obj:
                break
            #print "Recovered : %s" % obj
            if self.recoveryMap.has_key( obj.__class__):
                self.recoveryMap[obj.__class__](obj)
            else:
                print "No match for class???? %s %s" % (obj.__class__, str(self.recoveryMap.keys()) )
            recoveredObjects += 1
            if recoveredObjects % DISPLAY_EVERY_N_RECOVERED_ORDERS == 0:
                print "Recovered %s objects ..." % recoveredObjects
        endTime = time.time()
        orders = self.orderManager.numOrders
        dur = endTime - startTime
        print "Recovery finished %s" % time.asctime(time.localtime(endTime))
        print "Recovery finished %s secs %s orders = %s orders/sec" % ( dur, orders, orders/dur)
        self.inRecovery = False

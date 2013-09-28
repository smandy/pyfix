from twisted.internet import reactor
import random
#from makeOrder import *

DISPLAY_EVERY_N_SENT_ORDERS = 2000

class MyApplication:
    def setOrderGenerator(self, og):
        self.og = og
        self.ordersSent = 0
    
    def sendOrder(self, order = None):
        #print "SendOrder"
        details, session = random.choice( self.easySessions().items() )
        session = self.indexSessions()[ ('CLIENT1','EXECUTOR','FIX.4.2' )]
        #assert session.
        #session = random.choice( self.ap.sessionsById.keys())

        if not order:
            order = self.og.toFix(self.og.makeOrder())
        #pyfix.Session.sendToTarget( order, session)
        #session.send( order ) 
        #print "queueing order to %s" % str(details)
        reactor.callLater(0, self.orderSend(session, order))


    def setPortfolioManager(self, portMan):
        self.portMan = portMan

    def portDump(self):
        for allocator in self.portMan.allocators:
            print allocator.desc
            items = allocator.portfoliosByIdentifier.items()
            items.sort( lambda x,y: cmp( x[0], y[0]) )
            for desc, portfolio in items:
                print desc
                portfolio.positionManager.dumpPositions()
        

    def orderSend(self, session, order):
        self.ordersSent += 1
        if self.ordersSent % DISPLAY_EVERY_N_SENT_ORDERS ==0:
            print "%s orders sent" % self.ordersSent
        def ret():
            #print "firing order send %s" % order
            #print "Sending order ",
            session.send(order)
        return ret

    def getSessionDetails(self):
        return [ self.fixSettings.get(x) for x in self.fixApplication.sessionsById.keys() ]

    def getSessions(self):
        return self.fixApplication.sessionsById.values()

    def indexSessions(self):
        ret = {}
        
        for x in self.fixApplication.sessionsById.keys():
            #settings = self.fixSettings.get(x)
            #print settings
            tup = sessionIDTuple(x)
            ret[tup] = self.fixApplication.sessionsById[x]
        return ret 

    def easySessions(self):
        return dict( ( ( s[0].getSenderCompID().getString(),s[0].getTargetCompID().getString() ) , s[1] ) for s in self.fixApplication.sessionsById.items() )

    def setOrderManager(self, om):
        self.om = om

    def setPositionManager(self, pm):
        self.pm = pm

    def setDeferringApplication(self, deferringApplication):
        self.deferringApplication = deferringApplication
        
    def setSocketInitiator(self, socketInitiator):
        self.socketInitiator = socketInitiator

    def setFixApplication(self, fixApplication):
        print "FixApplication is %s" % fixApplication
        self.fixApplication = fixApplication
        
def sessionIDTuple(sid):
    return ( sid.getSenderCompID().getString(),
             sid.getTargetCompID().getString(),
             sid.getBeginString().getString()) 

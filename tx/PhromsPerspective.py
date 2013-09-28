# $Header: /Users/andy/cvs/dev/python/phroms/twisted/PhromsPerspective.py,v 1.17 2009-01-08 13:00:26 andy Exp $

from twisted.spread import pb
from twisted.internet import reactor
import traceback

class PhromsPerspective(pb.Root):
    def __init__(self):
        self.fillListeners = []
        self.orderStateListeners = []
        self.guis = []
        self.mdc = None

    def setMarketDataClient(self, mdc):
        self.mdc = mdc
        self.mdc.add( self.onTick )

    def setOrderManager(self, om):
        self.orderManager = om

    def logToGuis(self, x):
        toIter = self.guis
        #self.callRemoteOverList( self.guis
        for gui in toIter:
            try:
                #print "Calling Gui"
                #gui.callRemote(  'onTick' , "Tick : %s" % str( evt) ).addErrback( self.expunge, self.guis, gui )
                gui.callRemote(  'onLog'  , x ).addErrback( self.expunge, self.guis, gui) 
            except:
                traceback.print_exc()
                self.expungeGui(gui)

    def onTick(self, _, evt):
        toIter = self.guis
        #self.callRemoteOverList( self.guis
        for gui in toIter:
            try:
                print "Calling Gui"
                #gui.callRemote(  'onLog' , "Tick : %s" % str( evt) ).addErrback( self.expunge, self.guis, gui )
                gui.callRemote( 'onTick',evt ).addErrback( self.expunge, self.guis, gui )
            except:
                traceback.print_exc()
                self.expungeGui(gui)

    def expungeGui(self, badBoy):
        print "Expunging bad gui"
        self.guis = [ x for x in self.guis if not x==badBoy ]

    def setIoeParser( self, p):
        self.ioeParser = p

    def setOrderStateListener(self, osl):
        self.orderStateListener = osl
        osl.add( self.onOrderState)
        
    def setFillListener(self, fl):
        self.fl = fl
        print "Perspective is registering as a fillListener"
        fl.add( self.onFill )

    def remoteCaller(self, target, method, *args):
        def ret():
            target.callRemote( method, *args)
        return ret

    def callMade(self, x):
        print "Call to %s succeeded" % x

    def callFailed(self, x, l):
        print "Call to %s failed, evicting" % x
        l.remove(x)

    def onOrderState(self, _, os ):
        toIter = self.orderStateListeners[:]
        for x in toIter:
            try:
                #d = reactor.callLater(0, self.remoteCaller( x, 'onOrderState', args) )
                x.callRemote( 'onOrderState', os ).addErrback( self.expunge, self.orderStateListeners, x )
            except:
                traceback.print_exc()
                self.expunge(None, self.orderStateListeners, x)
            
    def onFill(self, _, orderState_execution ):
        #if self.fillListeners:
        #    traceback.print_stack()
        toIter = self.fillListeners[:]
        for x in toIter:
            #print "Calling %s.onFill with args %s" % ( x, str(args) )
            #d = reactor.callLater(0, self.remoteCaller( x, 'onFill', [ orderState_execution[1] ] ) )
            try:
                x.callRemote( 'onFill', orderState_execution ).addErrback( self.expunge, self.fillListeners, x )
            except:
                traceback.print_exc()
                print "Exception locally raised  - expunging"
                self.expunge(None,  self.fillListeners, x ) # We use expungelisteneer as an errback so keep the 
            #d.addCallback( self.callMade, [ x ] )
            #d.addErrback( self.callMade, [ x, self.fillListeners ] )
            #x.callRemote( 'notify', *args)

    def expunge(self, err, l, victim):
        #traceback.print_stack()
        print "Expunging %s from %s %s" % (err, victim, l)
        while victim in l:
            l.remove(victim)

    def expungeFillListener( self, _, victim ):
        print "Trying to expunge error broker : %s" % victim
        self.fillListeners = [ x for x in self.fillListeners if not x==victim ]

    def make_binger(self, ttl, target):
        def binger():
            target.callRemote( 'bing', ttl)
            if ttl>0:
                reactor.callLater( 1, self.make_binger(ttl-1, target))
        return binger

    def remote_addGui(self, gui):
        print "Adding gui %s" % gui
        self.guis.append( gui )
        self.logToGuis( "Gui Registered %s" % gui )

    def remote_registerFillListener(self, listener ):
        print "Adding fill listener %s" % listener
        self.fillListeners.append( listener )

    def remote_onGuiTextCommand(self, cmd):
        self.logToGuis( "Trying to parse : %s" % cmd )
        # Cmd is unicode?!!
        order = self.ioeParser.parse( str(cmd) )
        print "Have order %s" % order
        if order:
            self.orderManager.on_order(order)

    def remote_registerOrderStateListener(self, listener):
        self.orderStateListeners.append( listener )

    def remote_bingme(self, ttl, target):
        reactor.callLater( 1, self.make_binger( ttl, target) )

    def remote_startOrderSender( self ):
        self.orderManager.startOrderSender()
        

    def remote_die( self):
        reactor.stop()

class PhromsReporter(pb.Referenceable):
    def __init__(self, app):
        self.app = app
        

# $Header: /Users/andy/cvs/dev/python/phroms/examples/simpleordersend/sender.py,v 1.5 2009-03-02 16:57:32 andy Exp $

from __future__ import with_statement

import yaml
from twisted.internet import reactor

from pyfix.FIXProtocol import SessionManager, NormalMessageProcessing
from pyfix.FIXSpec import parse_specification
from pyfix.FIXConfig import makeConfig
from pyfix.FIXApplication import FIXApplication
import time, cPickle
from pprint import pprint as pp
import traceback
from collections import defaultdict

fix = parse_specification( "FIX.4.2" )

class DelayData:
    def __init__(self):
        self.count = 0
        self.startTime = time.time()
        self.messages = 0
        self.latencies = []
        self._endTime = None

    def endTime(self):
        if self._endTime is None:
            return time.time()
        else:
            return self._endTime

    def mean(self):
        return sum(self.latencies) / len(self.latencies)

    def frequency(self):
        t  = self.endTime()-self.startTime
        if t==0:
            return 0
        return self.count/t

class Sender(FIXApplication):
    def __init__(self, fix):
        FIXApplication.__init__(self, fix)
        self.dispatchDict = { fix.Heartbeat : self.onHeartbeat }
        self.testRequests = {}
        self.latencies = defaultdict( lambda: DelayData() )

        #frequncies = [ 1., 10, 30, 50, 75, 100, 110, 120, 130, 140, 150, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270 ]

        frequencies = range( 10, 300, 5)
        self.delays = [ 1./x for x in frequencies]
        
        #self.delays = [ 0.0005, 0.0001]

        self.delay = self.delays.pop(0)
        self.stopped = False

        #strMsg = self.session.compileMessage( myOrder )
        #msgSeqNum = myOrder.getHeaderFieldValue( pyfix.MsgSeqNum)
        #print "APP>> %s %s %s" % (msgSeqNum, myOrder, strMsg)
        #self.protocol.transport.write( strMsg )

    def set_state(self, old_state, newState):
        self.state = newState
        if newState.__class__==NormalMessageProcessing:
            reactor.callLater( 0.2 , self.startTiming)
            self.reportStats()

    def reportStats(self):
        for d, x in self.latencies.items():
            print d, 1.0/d, x.frequency(), x.frequency()*d, len(x.latencies), x.mean() 
        reactor.callLater(1, self.reportStats)

    def startTiming(self):
        conch = ( time.time(), self.delay)
        strConch = cPickle.dumps( conch )
        testRequestId = self.fix.TestReqID( strConch )
        msg = self.fix.TestRequest( fields = [ testRequestId ] )
        strMsg = self.session.compile_message(msg)
        self.protocol.transport.write( strMsg )
        reactor.callLater( self.delay, self.startTiming)

    def intervalFor(self, delay):
        if delay > 0.1:
            return 0.1
        if delay > 0.02:
            return 0.01
        else:
            return 0.001

    def onHeartbeat(self, protocol, msg, seq, possDup):
        if self.stopped:
            return
        timeNow = time.time()
        #print "Heartbeat!"
        request = msg.get_optional_field_values( self.fix.TestReqID, None )
        if request is not None:
            try:
                s = cPickle.loads( request )
                #print "Got pickle %s" % str(s)
                t, delay = s
                latency = timeNow - t
                dd = self.latencies[delay]
                dd.count += 1
                dd.latencies.append( latency )
                if timeNow - dd.startTime>=10.:
                    dd._endTime = timeNow
                    if not self.delays:
                        self.stopped = True
                        reactor.stop()
                        return
                    self.delay = self.delays.pop(0)
                    print "Setting delay to %s" % self.delay
            except:
                print "Duff test request id %s" % request
                traceback.print_exc()
                
            
config = yaml.load( open( '../config/sender.yaml','r') )
senderConfig  = makeConfig( config )
for x in senderConfig:
    x.app = Sender(fix)
    app = x.app

if __name__=='__main__':
    sessionManager = SessionManager( fix, senderConfig )
    sessionManager.getConnected()
    reactor.run()
    from pylab import plot, show
    data= []
    for d, x in app.latencies.items():
        if not x._endTime:
            x._endTime = time.time()
        timeTaken = x.endTime() - x.startTime
        messages = x.count
        freq = messages/timeTaken
        data.append( (d, timeTaken, x.count, x.mean(), freq ) )

    data.sort( lambda x,y: cmp(x[0], y[0]) )
    with open( './stats_%s', 'w') as f:
        f.write( cPickle.dumps( data ))
        
    pp(data)
    plot( [ 1.0/x[0] for x in data ],
          [ x[4] for x in data ] )
    show()

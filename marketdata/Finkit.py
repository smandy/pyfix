
# $Id: Finkit.py,v 1.3 2009-01-06 17:49:39 andy Exp $
#
#from Globals import *

import random
import threading
import time

from phroms.util.Observable import Observable

BROKER_QUANTITIES = [10,20]
USE_GUI = 0

LOOP_INTERVAL = 1

def enumerateList(x):
    fd = {}
    rd = {}
    for i in range(len(x)):
        fd[i]=x[i]
        rd[x[i]]=i
    return (fd, rd)


stockParams= [
    ("CSCO",   random.randint(50,100), 0.01, 0.01, 1.01, 0.99, 0.1),
    ("MFNX",   random.randint(50,100), 0.01, 0.01, 1.01, 0.99, 0.1),
    ("SEBL",   random.randint(50,100), 0.01, 0.01, 1.01, 0.99, 0.1),
    ("PIA",    random.randint(50,100), 0.01, 0.01, 1.01, 0.99, 0.1),
    ("PUMA",   random.randint(50,100), 0.01, 0.01, 1.01, 0.99, 0.1),
    ("IBM",    random.randint(50,100), 0.01, 0.01, 1.01, 0.99, 0.1),
    ("GLW",    random.randint(50,100), 0.01, 0.01, 1.01, 0.99, 0.1),
    ("AMAT",   random.randint(50,100), 0.01, 0.01, 1.01, 0.99, 0.1),
    ]        

class Null:
    def __init__(self, *args, **kwargs): pass
    def __call__(self, *args, **kwargs): pass
    def __repr__(self): return "Null()"
    def __nonzero__(self): return 0
    def __getattr__(self, x): return self
    def __setattr__(self, name, value): return self
    def __delattr__(self, name): return self

class Killable:
    pass

class UniqGen:
    def __init__(self,
                 prepend,
                 base=0):
        self._i = 0
        self._prepend = prepend
        
    def get(self):
        self._i+=1
        return "%s%05d" % (self._prepend, self._i)

def dumpToFile(rw, f):
    f = open(f, 'w')
    for x in rw._tickData:
        f.write( "%s,%s\n" % (x[0], x[1]) )
    f.close()

class UniquelyIdentifiable:
    def getPk(self):
        id = self.lastId
        while self.ids.has_key(id):
            id+=1
            #print id
        self.ids[id] = self
        self.instances.append(self)
        return id

class PriceManager(threading.Thread,
                   Observable,
                   Killable):
    def __init__(self, params=stockParams, verbose = 1, interval = 1):
        Observable.__init__(self)
        threading.Thread.__init__(self)
        self._walkers = []
        self._prices  = {}
        self._verbose  = verbose
        self._interval = interval
        self._running  = 1
        self._registeredObservers = {}
        self._observers = []
        self._oneShotObservers = []
        
        for tup in params:
            security = tup[0]
            print "Making walker for %s" % security
            walker = RandomWalker( *tup)
            (sec, px) = walker.peekPrice()
            self._prices[sec] = px
            self._walkers.append(walker)
            walker.add(self.onTick)

    def onTick(self, caller, evt):
        self.notify( evt )

    def run(self):
        for walker in self._walkers:
            walker.start()
        
        while self._running:
            time.sleep(self._interval)
            quays = self._prices.keys()
            quays.sort()
            
            if self._verbose:
                for quay in quays:
                    print "%10s : %10s" % (quay, self._prices[quay])
                    
    def getPrice(self, security):
        if not self._prices.has_key(security):
            #TODO - instantiate walker for new security
            return 0.0
        else:
            return self._prices[security]

    #def notify(self,caller, (sec, px) ):
    #    self._prices[sec] = px
        
    # This will take responsibility for telling walkers to die
    def kill(self):
        for walker in self._walkers:
            walker.kill()
        self._running = 0

class RandomWalker(threading.Thread, Observable, Killable):
    """This class will implement a lognormal-ish random walk"""

    # TODO - let time 'telescope' - i.e. fit a trading day
    # into 5 mins etc. that way timestamps will become relevant again
    def __init__(self,
                 security,
                 initialPrice,
                 pu,
                 pd,
                 up,
                 down,
                 timestep):
        threading.Thread.__init__(self)
        Observable.__init__(self)
        self._security = security
        self._prx      = initialPrice
        self._pu       = pu
        self._pd       = pd
        self._up       = up
        self._down     = down
        self._timestep = timestep
        self._running = 1
        self._tickData = []
        self._storeTicks = 1

    def run(self):
        while self._running:
            time.sleep(self._timestep)
            rand = random.random()

            priceChanged = 1
            if rand<self._pu: # Up
                self._prx *= self._up
            elif rand>(1-self._pd): # Down
                self._prx *= self._down
            else: # No Change
                priceChanged = 0

            if priceChanged:
                self._tickData.append( (time.time(), self._prx) )
                evt = (self._security, self._prx)
                self.notify(evt)

    def peekPrice(self):
        evt = (self._security, self._prx)
        return evt

    def kill(self):
        self._running=0

class Position:
    (enumState, stateEnum)= enumerateList( [ 'NEW',
                                             'CHANGED',
                                             'CLOSED' ] )
    def __init__(self,
                 quay,
                 attribs = {} ):
        self._quay      = quay
        self._contracts = 0
        self._volume    = 0
        self._status    = self.stateEnum['NEW']
        self._attribs   = {}

    def avgPrx(self):
        if self._contracts!=0:
            avgPrx = self._volume / self._contracts
        else:
            avgPrx = 0.0
        return avgPrx

    def __repr__(self):
        return "%s %s %s (%s)" % (self._contracts,
                                  str(self._quay),
                                  self.avgPrx(),
                                  self._volume)

def killThreads():
    for thread in threading.enumerate():
        if isinstance(thread, Killable):
            thread.kill()


if __name__=='__main__':
    pm = PriceManager()
    pm.start()

        


   

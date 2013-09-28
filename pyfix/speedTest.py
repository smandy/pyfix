
from FIXParser import SynchronousParser
from BerkeleyPersister import BerkeleyPersister
from datetime import datetime
import time

from FIXSpec import  parse_specification
fixSpec    = parse_specification( version= "FIX.4.2" )

fr = "/Users/andy/persist/send"
bp = BerkeleyPersister(fr, dt = datetime( 2009, 1, 13) )
(inDb,outDb) = bp.getTodayPersister( "SENDER", "PHROMS")

#p = BerkeleyPersister( fileRoot, dt = datetime(2009, 11,1) )
p = SynchronousParser(fixSpec)

def doit():
    for db in ( inDb, outDb):
        start = time.time()
        i = 0.0
        c = db.cursor()
        while True:
            v = c.next()
            if not v:
                break
            msg, _, _ = p.feed(v[1])
            i += 1
        endTime =time.time()
        dur = endTime - start
        print "%s parsed %s messages in %s secs (%s/sec)" % (db, i, dur , i/dur )
doit()

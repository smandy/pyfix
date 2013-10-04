from pyfix.persistence.BerkeleyPersister import BerkeleyPersister

fileRoot = "/Users/andy/dev/python/phroms/examples/multiplexer/persist/mux"

from datetime import datetime
from pyfix.FIXParser import  SynchronousParser
from pyfix.FIXSpec import parse_specification

fix = parse_specification('FIX.4.2')

def get( maxn = None, filterKlazz = None):
    bp = BerkeleyPersister( fileRoot , "MUX","SOURCE1", dt = datetime( 2009,2,24) )
    #bp = BerkeleyPersister( fileRoot , "SOURCE1","MUX", dt = datetime( 2009,2,13) )
    db = bp.outDb
    fp = SynchronousParser( fix)
    c = db.cursor()
    i = 0
    while True:
        d = c.next()
        #print d
        if not d:
            break
        msg, _,_ = fp.feed( d[1])

        if filterKlazz and not msg.__class__==fix.ExecutionReport:
            #print "Chucking out %s vs %s" % (msg.__class__, filterKlazz)
            continue

        #print msg.getFieldValue( pyfix.LastPx)
        yield msg
        i +=1
        if maxn and i>maxn:
            break
    c.close()

if 1:
    for i in get(maxn=10, filterKlazz = [ fix.ExecutionReport ]):
        print i




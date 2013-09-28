# $Header: /Users/andy/cvs/dev/python/phroms/alladin/discoverer.py,v 1.2 2009-02-28 21:38:31 andy Exp $

from twisted.internet import reactor
from pprint import pprint as pp

from pyfix.alladin.Discovery import Discoverer


def gotResults(r):
    pp(r)

d = Discoverer().addCallback( gotResults)

reactor.run()


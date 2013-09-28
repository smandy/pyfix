# $Header: /Users/andy/cvs/dev/python/phroms/examples/webadmin/web.py,v 1.4 2009-03-02 16:55:37 andy Exp $

from twisted.web import server, resource
import yaml
from twisted.internet import reactor

from phroms.examples.simpleordersend.sender import fix, config
from pyfix.FIXProtocol import SessionManager
from pyfix.FIXConfig   import makeConfig

class LinksPage(resource.Resource):
    isLeaf = 1
    
    def __init__(self, sessionManager ):
        resource.Resource.__init__(self)
        self.sm = sessionManager

    def setPositionManager(self, pm):
        self.positionManager = pm

    def setOrderManager(self, om):
        self.orderManager = om

    def wrapHeader( self, names, toWrap = "TD"):
        toWrap, newTr = "TR", toWrap
        return "<%s>%s</%s>" % (toWrap,
                                "".join( [ "<%s>%s</%s>" % (newTr, str(x), newTr) for x in names ] ),
                                toWrap)

    def wrapSessions( self, eyeThames):
        retLines =  []
        retLines.append( "<TABLE BORDER=1>")
        retLines.append( self.wrapHeader(  [ "Connected",
                                             "SenderCompID",
                                             "TargetCompID",
                                             "InMsgSeqNum",
                                             "OutMsgSeqNum",
                                             "State" ] , "TH") )
        for tup,session in eyeThames:
            sender,target = tup

            if session.isConnected() and session.protocol is not None:
                strState = str( session.protocol.state.__class__.__name__)
            else:
                strState = "N/A"
            
            retLines.append( self.wrapHeader( [ session.strConnected(),
                                          sender, target,
                                          session.inMsgSeqNum,
                                          session.outMsgSeqNum, strState ] , "TD" ) )
        retLines.append( "</TABLE>")
        return retLines

    def render(self, request):
        print request, type(request), dir(request)
        retLines = [ "<H1>Phroms Output</H1>"]
        sm = self.sm
        if sm.initiatorsByTuple:
            retLines.append( "<H2>INITIATORS</H2>" )
            retLines += self.wrapSessions( sm.initiatorsByTuple.items() )
        if sm.acceptorsByTuple:
            retLines.append( "<H2>ACCEPTORS</H2>" )
            retLines += self.wrapSessions( sm.acceptorsByTuple.items() )
        return "\n".join(retLines)


if __name__=='__main__':
    cfg = config['manhole']
    senderConfig   = makeConfig(yaml.load( open( '../config/sender.yaml','r')) )
    sm = SessionManager( fix, senderConfig )
    s = sm.sessions[0]

    from phroms.tx.ssh import getManholeFactory
    reactor.listenTCP( cfg['listenPort'], getManholeFactory(globals(), passwords = cfg['passwords'] ))

    linksPage = LinksPage( sm )
    site = server.Site( linksPage )
    reactor.listenTCP( config['webServer']['listenPort'], site)
    
    sm.getConnected()
    reactor.run()


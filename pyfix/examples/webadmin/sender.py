


import calculator

from nevow import  rend, loaders,  appserver, static
from twisted.web import server

from web import LinksPage

import os
class Examples(rend.Page):
    addSlash = True ## This is a directory-like resource
    docFactory = loaders.xmlfile(os.path.abspath('.')+'/index.html')
    child_sources = static.File('.', defaultType='text/plain')
    #child_sources.processors['.py'] = Sources
    child_sources.contentTypes = {}
    child_cssfile = static.File('index.css')
    children = dict()

    def child_calculator(self, ctx):
        return calculator.CalculatorParentPage(calc=calculator.Calculator())

#linksPage = LinksPage()

import yaml
from twisted.internet import reactor

from phroms.examples.simpleordersend.sender import SendingProtocol, fix, config
from pyfix.FIXProtocol     import SessionManager
from phroms.tx.fixConfig   import NativeConfig

if __name__=='__main__':
    cfg = config['manhole']
    senderConfig   = NativeConfig( yaml.load( open( '../config/sender.yaml','r').read() ) )
    sm = SessionManager( fix, senderConfig, initiatorProtocol = SendingProtocol )
    s = sm.sessions[0]

    # XXX comment me out before committing - only for debug
    from phroms.tx.ssh         import getManholeFactory
    reactor.listenTCP( cfg['listenPort'], getManholeFactory(globals(), passwords = cfg['passwords'] ))

    linksPage = LinksPage( sm )
    site = server.Site( linksPage )
    reactor.listenTCP( config['webServer']['listenPort'], site)
    linksPage = LinksPage(sm)
    reactor.listenTCP( config['nevow']['listenPort'], appserver.NevowSite(Examples()))
    
    site = server.Site( linksPage )
    
    sm.getConnected()
    reactor.run()


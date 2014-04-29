#import quickfix as pyfix
from pprint import pprint as pp

def make_dictionary(d):
    ret = fix.Dictionary()
    for q,v in d.items():
        ret.setString(q, v)
    return( ret )

class SessionConfig(object):
    __slots__=['sender','target','persistRoot','heartbeatInterval',
               'host','port','connectionType', 'app', 'd' ]
    def __init__(self,
                 connectionType,
                 port,
                 host,
                 sender,
                 target,
                 persistRoot,
                 heartbeatInterval,
                 app = None,
                 metaData = None):
        self.sender = sender
        self.target = target
        self.persistRoot = persistRoot
        self.heartbeatInterval = heartbeatInterval
        self.host = host
        self.port = port
        self.connectionType = connectionType
        self.app = app

    # The main reason for this apparent insanity is to help out
    # someone logged in remotely who wants to knock up a session
    # interactively from a prototyle
    def clone(self):
        return SessionConfig(self.connectionType,
                             self.port,
                             self.host,
                             self.sender,
                             self.target,
                             self.persistRoot,
                             self.heartbeatInterval,
                             self.app,
                             self.metaData)

def makeConfig(d):
    ret = []
    for chunk in d['sessions']:
        sess = d['default'].copy()
        sess.update( chunk )
        argList = [ 'ConnectionType',
                    'HeartbeatInterval',
                    'SenderCompID',
                    'TargetCompID',
                    'Port' ]
        for x in argList:
            assert sess.has_key(x), "Missing field %s" % x

        assert sess['ConnectionType'] in ['initiator','acceptor' ]
        if sess['ConnectionType']=='initiator':
            assert sess.has_key('Host')
            host = sess['Host']
        else:
            host = None
        s = SessionConfig( sess['ConnectionType'],
                           sess['Port'],
                           host, # Optional
                           sess['SenderCompID'],
                           sess['TargetCompID'],
                           sess['PersistRoot'],
                           sess['HeartbeatInterval'] , metaData = sess)
        ret.append( s )
    return ret

if __name__=='__main__':
    import yaml
    d = yaml.load( open( 'fixConfig.yaml','r').read() )
    x = makeConfig( d ) 

    

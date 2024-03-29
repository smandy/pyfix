#import quickfix as pyfix
from pprint import pprint as pp
import yaml


def make_dictionary(d):
    ret = {}
    for q, v in d.items():
        ret.setString(q, v)
    return(ret)


class SessionConfig(object):
    __slots__ = ['sender', 'target','persistRoot', 'heartbeatInterval',
                 'host', 'port', 'connectionType', 'app', 'd']

    def __init__(self,
                 connectionType,
                 port,
                 host,
                 sender,
                 target,
                 persistRoot,
                 heartbeatInterval,
                 app=None):
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
                             self.app)


def makeConfig(d):
    ret = []
    for chunk in d['sessions']:
        sess = d['default'].copy()
        sess.update(chunk)
        argList = ['ConnectionType',
                   'HeartbeatInterval',
                   'SenderCompID',
                   'TargetCompID',
                   'Port']
        for x in argList:
            assert sess.has_key(x), f"Missing field {x}"

        assert sess['ConnectionType'] in ['initiator', 'acceptor']
        if sess['ConnectionType'] == 'initiator':
            assert sess.has_key('Host')
            host = sess['Host']
        else:
            host = None
        s = SessionConfig(sess['ConnectionType'],
                          sess['Port'],
                          host,
                          sess['SenderCompID'],
                          sess['TargetCompID'],
                          sess['PersistRoot'],
                          sess['HeartbeatInterval'])
        ret.append(s)
    return ret

if __name__ == '__main__':
    with open('fixConfig.yaml', 'r') as f:
        d = yaml.load(f.read(), yaml.FullLoader)
        cfg = makeConfig(d)

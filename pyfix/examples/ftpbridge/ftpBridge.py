from twisted.python.filepath import FilePath
import yaml
from twisted.internet import reactor

from pyfix.examples.simpleordersend.sender import fix, config
from pyfix.FIXProtocol import SessionManager
from pyfix.FIXConfig import makeConfig
from pyfix.util.sender import SendingProtocol
from pyfix.tx.ssh import getManholeFactory

from twisted.cred.portal import Portal
from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse, ANONYMOUS
from twisted.protocols.ftp import FTPFactory, FTPRealm, IFTPShell, FTPAnonymousShell, FTPShell, _FileWriter
from twisted.cred.checkers import AllowAnonymousAccess
from twisted.internet import defer
from fileParser import FileParser


class MyFile(object):
    def __init__(self, app, path):
        self.data = ''
        self.app = app
        self.path = path

    def write(self, s):
        self.data += s

    def close(self):
        print "MyFile.close()!\n%s" % self.data
        fields = FileParser().parse(self.data)
        if self.app.protocol is not None:
            for x in fields:
                self.app.protocol.sendOrderFromFragments(x)


class MyFTPShell(FTPShell):
    def __init__(self, app):
        # Any attempt to access the filesystem will choke now since I've not
        # set filesystem root. Find
        """

        @type self: object
        """
        print "MyFTPShell : %s" % app
        self.app = app

        self.filesystemRoot = FilePath('/home/andy')
        pass


    def list(self, path, keys=()):
        #d = FTPShell.list(self, path, keys)
        print "list called with %s %s" % ( str(path), str(keys) )
        # FIXME TODO XXX
        return defer.succeed([])

    def openForWriting(self, path):
        return defer.succeed(_FileWriter(MyFile(self.app, path)))


class MyFTPRealm(FTPRealm):
    def __init__(self, app):
        self.app = app
        self.avatar = None

    def requestAvatar(self, avatar_id, mind, *interfaces):
        for iface in interfaces:
            if iface is IFTPShell:
                if avatar_id is ANONYMOUS:
                    avatar = FTPAnonymousShell(self.anonymousRoot)
                else:
                    avatar = MyFTPShell(self.app)
                    self.avatar = avatar
                    print "Avatar is MyFTPShell %s" % avatar
                return IFTPShell, avatar, getattr(avatar, 'logout', lambda: None)
        raise NotImplementedError("Only IFTPShell interface is supported by this realm")


if __name__ == '__main__':
    cfg = config['manhole']
    senderConfig = makeConfig(yaml.load(open('../config/sender.yaml', 'r').read()))
    sm = SessionManager(fix, senderConfig, initiatorProtocol=SendingProtocol)
    s = sm.sessions[0]
    p = Portal(MyFTPRealm(s),
               [AllowAnonymousAccess(), InMemoryUsernamePasswordDatabaseDontUse(**config['ftpServer']['passwords'])])
    f = FTPFactory(p)
    reactor.listenTCP(cfg['listenPort'], getManholeFactory(globals(), passwords=cfg['passwords']))
    reactor.listenTCP(2011, f)
    sm.getConnected()

    reactor.run()

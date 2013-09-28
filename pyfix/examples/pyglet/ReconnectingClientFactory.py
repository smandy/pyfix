
from twisted.spread import pb
from twisted.internet import protocol

class ReconnectingPBClientFactory(pb.PBClientFactory, log.Loggable,
                                  protocol.ReconnectingClientFactory):
    """
    Reconnecting client factory for normal PB brokers.

    Users of this factory call startLogin to start logging in, and should
    override getLoginDeferred to get the deferred returned from the PB server
    for each login attempt.
    """

    maxDelay = 5

    def __init__(self):
        pb.PBClientFactory.__init__(self)
        self._doingLogin = False

    def clientConnectionFailed(self, connector, reason):
        log.msg("connection failed to %s, reason %r" % (
            connector.getDestination(), reason))
        pb.PBClientFactory.clientConnectionFailed(self, connector, reason)
        RCF = protocol.ReconnectingClientFactory
        RCF.clientConnectionFailed(self, connector, reason)

    def clientConnectionLost(self, connector, reason):
        log.msg("connection lost to %s, reason %r" % (
            connector.getDestination(), reason))
        pb.PBClientFactory.clientConnectionLost(self, connector, reason,
                                             reconnecting=True)
        RCF = protocol.ReconnectingClientFactory
        RCF.clientConnectionLost(self, connector, reason)

    def clientConnectionMade(self, broker):
        log.msg("connection made")
        self.resetDelay()
        pb.PBClientFactory.clientConnectionMade(self, broker)
        if self._doingLogin:
            d = self.login(self._credentials, self._client)
            self.gotDeferredLogin(d)

    def startLogin(self, credentials, client=None):
        self._credentials = credentials
        self._client = client

        self._doingLogin = True

    # methods to override

    def gotDeferredLogin(self, deferred):
        """
        The deferred from login is now available.
        """
        raise NotImplementedError

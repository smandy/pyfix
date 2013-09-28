class SessionInfo:
    def __init__(self , parent, d, defaultAccount, sid, session, t):
        self.parent = parent
        self.loggedOn       = False
        self.defaultAccount = defaultAccount
        self.sid = sid
        self.session = session
        self.tuple = t
        self.d = d

    # Guess all of the senders can have 'send' methods.
    # duck typing - gotta love it
    def sendExecution(self, orderState, execution):
        assert execution.__class__==Execution
        foreignEx = self.parent.fixConverter.convertLocalExecutionToForeign( orderState, execution )
        self.session.send( foreignEx )

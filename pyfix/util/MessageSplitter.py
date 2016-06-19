class MessageSplitter:
    def __init__(self, dispatch):
        self.dispatch = dispatch
    
    def __call__(self, sender, msg, seq, possDup):
        klazz = msg.__class__
        if self.dispatch.has_key( klazz ):
            self.dispatch[klazz](sender, msg, seq, possDup)

class SplitterClient(object):
    
    def onMessage( self, sender, msg, seq, possDup):
        msgKlazz = msg.__class__
        if self.dispatchDict.has_key( msgKlazz ):
            self.dispatchDict[msgKlazz]( msg, seq, possDup)

    def onStateChange(self, oldState, newState):
        self.state = newState

    def onConnection(self, protocol):
        self.protocol = protocol
        
        

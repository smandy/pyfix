class Observable:
    def __init__(self):
        self.listeners = []

    def add(self, l):
        self.listeners.append( l )

    def notify(self, o):
        #print "notify"
        for x in self.listeners:
            x( self, o)

def bing( sender, obj):
    print "Bing : %s %s" % (sender, obj)
    
def bong( sender, obj):
    print "Bong : %s %s" % (sender, obj)

class Bingable:
    def __init__(self):
        pass

    def bing(self, sender, obj):
        print "%s.bing( %s %s)" % (self, sender, obj)

if __name__=='__main__':
    o = Observable()
    o.add( bing )
    o.add( bong )
    o.add( Bingable().bing )
    o.notify( "Wayhey")
    

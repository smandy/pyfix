class Observable:
    def __init__(self):
        self.listeners = []

    def add(self, listener):
        self.listeners.append(listener)

    def notify(self, o):
        # print "notify"
        for x in self.listeners:
            x(self, o)

def bing(sender, obj):
    print(f"Bing : {sender} {obj}")
    
def bong( sender, obj):
    print("Bong : %s %s" % (sender, obj))

class Bingable:
    def __init__(self):
        pass

    def bing(self, sender, obj):
        print("%s.bing( %s %s)" % (self, sender, obj))

if __name__=='__main__':
    obs = Observable()
    obs = obs.add(bing)
    obs = obs.add(bong)
    obs = obs.add(Bingable().bing)
    obs = obs.notify("Wayhey")

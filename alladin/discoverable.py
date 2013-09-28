from Discovery import Discoverable, getConch
from twisted.internet import reactor

if __name__=='__main__':
    for i in range(20):
        myData = { 'i' : '127.0.0.1',
                   's' : 'bladibla',
                   'p' : 2343,
                   'c' : getConch(),
                   'Desc' : 'Multicast examples2' } # i.e. some arbitrary data
        d = Discoverable( myData )
    #reactor.listenMulticast( PORT, d )
    reactor.run()

    
    


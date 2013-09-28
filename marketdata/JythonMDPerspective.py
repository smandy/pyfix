from MDPerspective import *


if __name__=='__main__':
    import sys
    sys.path.insert(0, 
    "/Library/Frameworks/Python.framework/Versions/2.5.2001/lib/python2.5/site-packages")
    perspective = MDPerspective()
    print "Listening..."
    reactor.listenTCP(MDPORT, pb.PBServerFactory( perspective ) )
    print "Starting reactor..."
    reactor.run()

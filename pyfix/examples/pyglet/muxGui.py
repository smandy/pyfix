import phroms.pyglet.pygletreactor as pygletreactor

pygletreactor.install() # <- this must come before...

import pyglet

from phroms.alladin.Discovery import Discoverer
from pyglet.window import key

from twisted.internet import reactor # <- ...importing this reactor!
from twisted.spread import pb

# Create a Pyglet window with a simple message
#window = pyglet.window.Window(fullscreen=True)
window = pyglet.window.Window(width=1000)

fps_display = pyglet.clock.ClockDisplay()

Label = pyglet.text.Label
HTMLLabel = pyglet.text.HTMLLabel

labels = None

from pyfix.FIXSpec import parseSpecification

fix = parseSpecification("FIX.4.2")
from pyfix.FIXParser import SynchronousParser

sp = SynchronousParser(fix)

import traceback

lastOrder = ''
lastExecution = ''
orderObject = ''
executionObject = ''

#Useful snippet from the web.
##         # figure the line height
##         l = pyglet.text.Label('My', font_size=self.style['font_size'],
##             font_name=self.style['font_name'], dpi=self.dpi)
##         super(InterpreterElement, self).__init__(l.content_height,
##             l.content_height - self.height, self.width)

sessionsFound = None

keyMap = dict((getattr(key, "_%s" % i), i) for i in range(10))
print keyMap


def draw_session_list():
    global sessionLabel, sessionsFound
    s = ''
    #print "Sessions found ", sessionsFound

    if sessionsFound is not None:
        if len(sessionsFound) == 0:
            s = "No Sessions Found\n"
        else:
            for i, (d, addr) in enumerate(sessionsFound):
                host, port = addr
                s += "%s) %s %s:%s\n" % (i, d['description'], host, d['port'] )
        s += "<SPACE> - Refresh list"
    else:
        s = "Discovering sessions ..."

    l1 = Label(s, font_name='Andale Mono', font_size=20, x=200, y=300, multiline=True, width=600)
    l1.color = ( 255, 255, 255, 255)
    l1.draw()


def draw_session_display():
    global labels, lastOrder, lastExecution, executionObject, orderObject
    tmplate = '<p><font color="red">%s</p></font>'
    if mg.strOrder is not lastOrder:
        tmp, _, _ = sp.parse(mg.strOrder)
        orderObject = "\n".join(tmp.getDump())
        #orderObject = r"".join( [ tmplate % x for x in tmp.getDump() ] )
        #orderObject = r"<br>".join( tmp.getDump() )
        lastOrder = mg.strOrder

    if mg.strExec is not lastExecution:
        tmp, _, _, = sp.parse(mg.strExec)
        executionObject = "\n".join(tmp.getDump())
        lastExecution = mg.strExec
    try:
        if not labels or len(labels) != len(mg.ss):
            labels = []
            y = 150
            for sess in mg.ss:
                l = Label('TMP',
                          x=20,
                          y=y)
                labels.append(l)
                y += l.content_height
                y += 5

            l1 = Label('', font_name='Courier New', font_size=14, x=650, y=430, multiline=True, width=80)
            l2 = Label('', font_name='Courier New', font_size=14, x=300, y=430, multiline=True, width=80)

            l1.color = (0, 255, 0, 255 )
            l2.color = (0, 0, 255, 255 )

            labels.append(l1)
            labels.append(l2)

        for ( l, tup) in zip(labels[:-2], mg.ss):
            sender, target, isConnected, inMsgSeqNum, outMsgSeqNum = tup
            strMsg = "%s %s %s %s %s" % (sender,
                                         target,
                                         str(isConnected),
                                         inMsgSeqNum,
                                         outMsgSeqNum )
            l.text = strMsg
        labels[-2].text = executionObject
        labels[-1].text = orderObject

        for x in labels:
            x.draw()
    except:
        print "Exception"
        traceback.print_exc()


draw_func = draw_session_list
sessions = []


def onSessionList(sl):
    global sessionsFound, draw_func
    print "sl is %s" % sl
    sessionsFound = sl
    #draw_func = draw_session_display

    #if draw_func==draw_session_list:
    #    startDiscovery()


def startDiscovery():
    Discoverer(domain="pyfix_perspective").addCallback(onSessionList)


@window.event
def on_draw():
    global draw_func
    window.clear()
    fps_display.draw()
    draw_func()
    #draw_session_display()
    #label.draw()
    #draw_session_display()


@window.event
def on_key_press(symbol, modifiers):
    print symbol
    m = keyMap.get(symbol, None)
    if m is not None and draw_func == draw_session_list:
        print "Mapped Key %s->%s" % ( symbol, m)
        connectToSession(m)
    elif symbol == key.SPACE:
        global sessionsFound
        sessionsFound = None
        startDiscovery()


def connectToSession(i):
    global draw_func, mg, sessionsFound
    if not i in range(len(sessionsFound)):
        return
    session = sessionsFound[i]
    d, hostPort = session
    print session
    port = d['port']
    host = hostPort[0]
    mg = MuxGui(host, port)
    draw_func = draw_session_display
    sessionsFound = None


@window.event
def on_close():
    reactor.stop()


from pbutil import ReconnectingPBClientFactory


class MuxGui(pb.Referenceable, pb.PBClientFactory):
    def __init__(self, host, port):
        pb.PBClientFactory.__init__(self)
        self.host = host
        self.port = port
        self.ss = []
        pbFactory = pb.PBClientFactory()
        x = reactor.connectTCP(self.host, self.port, self)

        self.strOrder = ''
        self.strExec = ''
        #pbFactory.getRootObject().addCallback( self.connected).addErrback( self.notConnected)

        # Calling gotRootobject should make me interfact compatible with the Reconectingfactory
        # We don't want to be reconnecting however, if gui disconnects it should be down to the
        # user to connect.
        self.getRootObject().addCallback(self.gotRootObject)

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed %s" % reason
        ReconnectingPBClientFactory.clientConnectionFailed(self, connector, reason)

    def notConnected(self, *args):
        print "Not connected %s" % str(args)

    def gotRootObject(self, rootObj):
        print "Got root object - registering"
        rootObj.notifyOnDisconnect(self.disconnected)
        rootObj.callRemote('addSessionListener', self)

    def disconnected(self, obj):
        global draw_func
        draw_func = draw_session_list
        startDiscovery()

    def remote_onOrder(self, order):
        self.strOrder = order

    def remote_onExecution(self, execution):
        self.strExec = execution

    def remote_onSessionState(self, ss):
        #print "Got ss %s" % datetime.now()
        self.ss = ss


if __name__ == '__main__':
    #mg = MuxGui()
    mg = None
    Discoverer(domain="pyfix_perspective").addCallback(onSessionList)
    reactor.run()


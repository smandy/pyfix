
import wx
import sys

import traceback

try:
    from wx import glcanvas
    haveGLCanvas = True
except ImportError:
    haveGLCanvas = False

import random

try:
    # The Python OpenGL package can be found at
    # http://PyOpenGL.sourceforge.net/
    from OpenGL import GL
    from OpenGL import GLUT
    haveOpenGL = True
except ImportError:
    haveOpenGL = False

#----------------------------------------------------------------------


buttonDefs = {
    wx.NewId() : ('CubeCanvas',      'Cube'),
    wx.NewId() : ('ConeCanvas',      'Cone'),
    }

class ButtonPanel(wx.Panel):
    def __init__(self, parent, log):
        wx.Panel.__init__(self, parent, -1)
        self.log = log

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add((20, 30))
        keys = buttonDefs.keys()
        keys.sort()
        for k in keys:
            text = buttonDefs[k][1]
            btn = wx.Button(self, k, text)
            box.Add(btn, 0, wx.ALIGN_CENTER|wx.ALL, 15)
            self.Bind(wx.EVT_BUTTON, self.OnButton, btn)

        #** Enable this to show putting a GLCanvas on the wx.Panel
        if 0:
            c = CubeCanvas(self)
            c.SetSize((200, 200))
            box.Add(c, 0, wx.ALIGN_CENTER|wx.ALL, 15)

        self.SetAutoLayout(True)
        self.SetSizer(box)


    def OnButton(self, evt):
        if not haveGLCanvas:
            dlg = wx.MessageDialog(self,
                                   'The GLCanvas class has not been included with this build of wxPython!',
                                   'Sorry', wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()

        elif not haveOpenGL:
            dlg = wx.MessageDialog(self,
                                   'The OpenGL package was not found.  You can get it at\n'
                                   'http://PyOpenGL.sourceforge.net/',
                                   'Sorry', wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()

        else:
            canvasClassName = buttonDefs[evt.GetId()][0]
            canvasClass = eval(canvasClassName)
            frame = wx.Frame(None, -1, canvasClassName, size=(400,400))
            canvas = canvasClass(frame)
            frame.Show(True)

class MyCanvasBase(glcanvas.GLCanvas):
    def __init__(self, parent, *args, **kwags):
        glcanvas.GLCanvas.__init__(self, parent, -1)
        self.init = False
        # initial mouse position
        self.lastx = self.x = 30
        self.lasty = self.y = 30
        self.size = None
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMotion)

    def OnEraseBackground(self, event):
        pass # Do nothing, to avoid flashing on MSW.

    def OnSize(self, event):
        size = self.size = self.GetClientSize()
        if self.GetContext():
            self.SetCurrent()
            GL.glViewport(0, 0, size.width, size.height)
        event.Skip()

    def OnPaint(self, event = None):
        dc = wx.PaintDC(self)
        self.SetCurrent()
        if not self.init:
            self.InitGL()
            self.init = True
        self.OnDraw()

    def OnMouseDown(self, evt):
        self.CaptureMouse()
        self.x, self.y = self.lastx, self.lasty = evt.GetPosition()

    def OnMouseUp(self, evt):
        self.ReleaseMouse()

    def OnMouseMotion(self, evt):
        if evt.Dragging() and evt.LeftIsDown():
            self.lastx, self.lasty = self.x, self.y
            self.x, self.y = evt.GetPosition()
            self.Refresh(False)

class DotsCanvas( MyCanvasBase ):
    def InitGL(self):
        # set viewing projection
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glFrustum(-0.5, 0.5, -0.5, 0.5, 1.0, 3.0)

        # position viewer
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glTranslatef(0.0, 0.0, -2.0)

        # position object
        GL.glRotatef(self.y, 1.0, 0.0, 0.0)
        GL.glRotatef(self.x, 0.0, 1.0, 0.0)

        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glEnable(GL.GL_LIGHT0)
        self.colorChoices = [ (0.0, 0.0, 1),
                              (0.0, 1.0, 0.0),
                              (0.0, 1.0, 1.0),
                              (1.0, 0.0, 0.0),
                              (0.0, 1.0, 0.0) ]

    def OnDraw(self):
        source = self.perspective.deltas
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        try:
            items = source.items()
            if items:
                items.sort( lambda x,y: cmp(x[0], y[0] ) )

                pmin, pmax = None, None
                #print source
                for (q,v) in source.items():
                    if pmin is None:
                        pmin = v
                    else:
                        pmin = min(v, pmin)

                    if pmax is None:
                        pmax = v
                    else:
                        pmax = max( pmax, v)

                #print pmin, pmax
                i = 0.0
                s = len(source)
                GL.glBegin(GL.GL_QUADS)
                scale = pmax - pmin
                for (q,v) in items:
                    x1 = i/s
                    x2 = (i+0.75)/s
                    y1 = 0.0
                    y2 = (v-pmin)/scale
                    c = random.choice(self.colorChoices)
                    #glColor3f( *c )
                    GL.glNormal3f( 0.0, 0.0, 1.0)
                    GL.glVertex3f( x1, y1, 0.0)
                    GL.glVertex3f( x2, y1, 0.0)
                    GL.glVertex3f( x2, y2, 0.0)
                    GL.glVertex3f( x1, y2, 0.0)

                    GL.glNormal3f( 0.0, 0.0, 1.0)
                    GL.glVertex3f( x1, y1, 0.2)
                    GL.glVertex3f( x2, y1, 0.2)
                    GL.glVertex3f( x2, y2, 0.2)
                    GL.glVertex3f( x1, y2, 0.2)

                    GL.glNormal3f( 0.0, 0.0, -1.0)
                    GL.glVertex3f( x1, y2, 0.0)
                    GL.glVertex3f( x1, y2, 0.2)
                    GL.glVertex3f( x2, y2, 0.2)
                    GL.glVertex3f( x2, y2, 0.0)

                    i += 1
                GL.glEnd()
        except:
            traceback.print_exc()

        if self.size is None:
            self.size = self.GetClientSize()
        w, h = self.size
        w = max(w, 1.0)
        h = max(h, 1.0)
        xScale = 180.0 / w
        yScale = 180.0 / h
        GL.glRotatef((self.y - self.lasty) * yScale, 1.0, 0.0, 0.0);
        GL.glRotatef((self.x - self.lastx) * xScale, 0.0, 1.0, 0.0);
            
        self.SwapBuffers()
            
class CubeCanvas(MyCanvasBase):
    def InitGL(self):
        # set viewing projection
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glFrustum(-0.5, 0.5, -0.5, 0.5, 1.0, 3.0)
        # position viewer
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glTranslatef(0.0, 0.0, -2.0)
        # position object
        GL.glRotatef(self.y, 1.0, 0.0, 0.0)
        GL.glRotatef(self.x, 0.0, 1.0, 0.0)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glEnable(GL.GL_LIGHT0)

    def OnDraw(self):
        # clear color and depth buffers
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        # draw six faces of a cube
        GL.glBegin(GL.GL_QUADS)
        GL.glNormal3f( 0.0, 0.0, 1.0)
        GL.glVertex3f( 0.5, 0.5, 0.5)
        GL.glVertex3f(-0.5, 0.5, 0.5)
        GL.glVertex3f(-0.5,-0.5, 0.5)
        GL.glVertex3f( 0.5,-0.5, 0.5)

        GL.glNormal3f( 0.0, 0.0,-1.0)
        GL.glVertex3f(-0.5,-0.5,-0.5)
        GL.glVertex3f(-0.5, 0.5,-0.5)
        GL.glVertex3f( 0.5, 0.5,-0.5)
        GL.glVertex3f( 0.5,-0.5,-0.5)

        GL.glNormal3f( 0.0, 1.0, 0.0)
        GL.glVertex3f( 0.5, 0.5, 0.5)
        GL.glVertex3f( 0.5, 0.5,-0.5)
        GL.glVertex3f(-0.5, 0.5,-0.5)
        GL.glVertex3f(-0.5, 0.5, 0.5)

        GL.glNormal3f( 0.0,-1.0, 0.0)
        GL.glVertex3f(-0.5,-0.5,-0.5)
        GL.glVertex3f( 0.5,-0.5,-0.5)
        GL.glVertex3f( 0.5,-0.5, 0.5)
        GL.glVertex3f(-0.5,-0.5, 0.5)

        GL.glNormal3f( 1.0, 0.0, 0.0)
        GL.glVertex3f( 0.5, 0.5, 0.5)
        GL.glVertex3f( 0.5,-0.5, 0.5)
        GL.glVertex3f( 0.5,-0.5,-0.5)
        GL.glVertex3f( 0.5, 0.5,-0.5)

        GL.glNormal3f(-1.0, 0.0, 0.0)
        GL.glVertex3f(-0.5,-0.5,-0.5)
        GL.glVertex3f(-0.5,-0.5, 0.5)
        GL.glVertex3f(-0.5, 0.5, 0.5)
        GL.glVertex3f(-0.5, 0.5,-0.5)
        GL.glEnd()

        if self.size is None:
            self.size = self.GetClientSize()
        w, h = self.size
        w = max(w, 1.0)
        h = max(h, 1.0)
        xScale = 180.0 / w
        yScale = 180.0 / h
        GL.glRotatef((self.y - self.lasty) * yScale, 1.0, 0.0, 0.0);
        GL.glRotatef((self.x - self.lastx) * xScale, 0.0, 1.0, 0.0);
        self.SwapBuffers()

class ConeCanvas(MyCanvasBase):
    def InitGL( self ):
        GL.glMatrixMode(GL.GL_PROJECTION)
        # camera frustrum setup
        GL.glFrustum(-0.5, 0.5, -0.5, 0.5, 1.0, 3.0)
        GL.glMaterial(GL.GL_FRONT, GL.GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
        GL.glMaterial(GL.GL_FRONT, GL.GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
        GL.glMaterial(GL.GL_FRONT, GL.GL_SPECULAR, [1.0, 0.0, 1.0, 1.0])
        GL.glMaterial(GL.GL_FRONT, GL.GL_SHININESS, 50.0)
        GL.glLight(GL.GL_LIGHT0, GL.GL_AMBIENT, [0.0, 1.0, 0.0, 1.0])
        GL.glLight(GL.GL_LIGHT0, GL.GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
        GL.glLight(GL.GL_LIGHT0, GL.GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        GL.glLight(GL.GL_LIGHT0, GL.GL_POSITION, [1.0, 1.0, 1.0, 0.0])
        GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
        GL.glEnable(GL.GL_LIGHTING)
        GL.glEnable(GL.GL_LIGHT0)
        GL.glDepthFunc(GL.GL_LESS)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        # position viewer
        GL.glMatrixMode(GL.GL_MODELVIEW)
        # position viewer
        GL.glTranslatef(0.0, 0.0, -2.0);
        #
        GLUT.glutInit(sys.argv)


    def OnDraw(self):
        # clear color and depth buffers
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        # use a fresh transformation matrix
        GL.glPushMatrix()
        # position object
        #glTranslate(0.0, 0.0, -2.0)
        GL.glRotate(30.0, 1.0, 0.0, 0.0)
        GL.glRotate(30.0, 0.0, 1.0, 0.0)

        GL.glTranslate(0, -1, 0)
        GL.glRotate(250, 1, 0, 0)
        GLUT.glutSolidCone(0.5, 1, 30, 5)
        GL.glPopMatrix()
        GL.glRotatef((self.y - self.lasty), 0.0, 0.0, 1.0);
        GL.glRotatef((self.x - self.lastx), 1.0, 0.0, 0.0);
        # push into visible buffer
        self.SwapBuffers()



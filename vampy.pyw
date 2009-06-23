#!/usr/bin/env python
"Main file for VAMPy project"
#from vampy.wxgui import VampyApp
from wx import App
import vampy.wxgui as vgui

class VampyApp(App):
    '''wxPython application for VAMP front end'''
    def OnInit(self):
        self.frame = vgui.VampyFrame(parent=None, id=-1, title='VAMPy')
        self.frame.Show()
        return True
    def Reload(self):
        """
        Reload GUI without restart
        shuts down the main frame, reloads its module and creates a new frame
        FIXME: memory leak with this type of reloading
        """
        self.frame.DestroyChildren()
        self.frame.Destroy()
        reload(vgui)
        self.OnInit()

app = VampyApp(False)
app.MainLoop()
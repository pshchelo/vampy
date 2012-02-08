#!/usr/bin/env python
"Main file for VAMPy project"
import wx
from wxgui import uimain, resources

class VamPyApp(wx.App):
    '''Actual wxPython application'''
    def OnInit(self):
        customartprovider = resources.CustomArtProvider()
        wx.ArtProvider.Push(customartprovider)
        frame = uimain.VampyFrame(parent=None, id=-1)
        frame.Show()
        return True   

app = VamPyApp(False)
app.MainLoop()

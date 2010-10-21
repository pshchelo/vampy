#!/usr/bin/env python
"Only tensions analysis for VAMPy project"
from wx import PySimpleApp
from vampy.wxgui.tension import TensionsFrame

app = PySimpleApp(False)
frame = TensionsFrame(parent=None, id=-1)
frame.Show()
app.MainLoop()
#!/usr/bin/env python
"Main file for VAMPy project"
from wx import PySimpleApp
from vampy.wxgui.uimain import VampyFrame

app = PySimpleApp(False)
frame = VampyFrame(parent=None, id=-1)
frame.Show()
app.MainLoop()
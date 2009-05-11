#!/bin/env python
"""
Collection of GUI elements created by Pavlo Shchelokovskyy.
This module cannot be used on it own.
Provides following objects:
    OneParamFilePanel - simple panel for processing one file with one parameter;
    NumValidator - validator instance suitable for integers or floats;
    ValidTextEntryDialog - similar to wx.TextEntryDialog but allows a custom validator to be attached
"""

import wx
import os

def rgba_wx2mplt(wxcolour):
    """
    Convert wx.Colour instance to tuple of rgba values to range 0-1 (used by matplotlib).
    @param wxcolour: wx.Colour instance
    """
    mpltrgba = []
    wxrgba = wxcolour.Get(includeAlpha=True)
    for item in wxrgba:
        converted = float(item)/255
        mpltrgba.append(converted)
    return tuple(mpltrgba)

class DoubleSlider(wx.Panel):
    '''
    Provides a panel with two sliders to visually set 2 values (i.e. minimum and maximum, limits etc)
    TODO: implement all missing  methods of wx.Slider
    TODO: make styles work as with normal slider, but also some panel styling would be great
    '''
    def __init__(self, parent, id, value = (1,100), min=1, max=100, gap = 0, style=wx.SL_HORIZONTAL, panelstyle=wx.TAB_TRAVERSAL|wx.NO_BORDER, name=None):
        wx.Panel.__init__(self, parent, id, style=panelstyle)
        self.gap = gap
        initmin, initmax = value
        self.minslider = wx.Slider(self, -1, initmin, min, max, style=style)
        self.maxslider = wx.Slider(self, -1, initmax, min, max, style=style)
        self.Bind(wx.EVT_SLIDER, self.OnSlideMin, self.minslider)
        self.Bind(wx.EVT_SLIDER, self.OnSlideMax, self.maxslider)
        if style == wx.SL_HORIZONTAL:
            sizer = wx.BoxSizer(wx.VERTICAL)
        elif style == wx.SL_VERTICAL:
            sizer = wx.BoxSizer(wx.HORIZONTAL)
        else:
            print 'strange style'        
        sizer.Add(self.minslider)
        sizer.Add(self.maxslider)
        self.SetSizer(sizer)
        self.Fit()
        
    def SetValue(self, value):
        min, max = value
        self.minslider.SetValue(min)
        self.maxslider.SetValue(max)
    def GetValue(self):
        return self.minslider.GetValue(), self.maxslider.GetValue()
        
    def SetMin(self, min):
        self.minslider.SetMin(min)
        self.maxslider.SetMin(min)
    def GetMin(self):
        minmin = self.minslider.GetMin()
        minmax = self.maxslider.GetMin()
        if minmin != minmax:
            raise AssertionError
        else:
            return minmin
        
    def SetMax(self, max):
        self.minslider.SetMax(max)
        self.maxslider.SetMax(max)
    def GetMax(self):
        maxmin = self.minslider.GetMax()
        maxmax = self.maxslider.GetMax()
        if maxmin != maxmax:
            raise AssertionError
        else:
            return maxmax
        
    def SetRange(self, range):
        self.minslider.SetRange(range)
        self.maxslider.SetRange(range)
    def GetRange(self):
        rangemin = self.minslider.GetRange()
        rangemax = self.maxslider.GetRange()
        if rangemin != rangemax:
            raise AssertionError
        else:
            return rangemax
        
    def OnSlideMin(self, evt):
        min, max = self.GetValue()
        rangemin, rangemax = self.GetRange()
        if min > rangemax-self.gap:
            value = rangemax-self.gap, rangemax
            self.SetValue(value)
            evt.Skip()
            return
        if min > max-self.gap:
            value = min, min+self.gap
            self.SetValue(value)
            evt.Skip()
            return
        evt.Skip()
    def OnSlideMax(self, evt):
        min, max = self.GetValue()
        rangemin, rangemax = self.GetRange()
        if max < rangemin+self.gap:
            value = rangemin, rangemin+self.gap
            self.SetValue(value)
            evt.Skip()
            return
        if max < min-self.gap:
            value = max-self.gap, max
            self.SetValue(value)
            evt.Skip()
            return
        evt.Skip()
        
class NumValidator(wx.PyValidator):
    """
    Validator that allows integer or float numbers (configurable), with optional min and max limits.
    """
    def __init__(self, flag, min = None, max = None):
        """
        Constructor method
        @param flag: from ['int', 'float'] - string
        @param min: optional minimum value - int or float
        @param max: optional maximim value - int or float
        """
        wx.PyValidator.__init__(self)
        self.flag = flag
        self.min = min
        self.max = max
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        """
        Every Validator must implement this method
        """
        return NumValidator(self.flag, min = self.min, max = self.max)

    def Validate(self, win):
        """
        Actual validating method.
        @param win: parent window
        """
        txtCtrl = self.GetWindow()
        value = txtCtrl.GetValue()
        ### leftovers from trying to make it with regular expressions
#        intpattern = r"^[-]?[0-9]+$"
#        floatpattern = r"^[-]?[0-9]*\.?[0-9]+([eE][-]?[0-9]+)?$"
        if self.flag == 'int':
            try:
                number = int(value)
            except ValueError:
                wx.MessageBox('Not an integer!','Error')
                self.FocusAttention(txtCtrl)
                return False
        if self.flag == 'float':
            try:
                number = float(value)
            except ValueError:
                wx.MessageBox('Not a float!','Error')
                self.FocusAttention(txtCtrl)
                return False
        if type(self.min) != type(None) and number < self.min:
            wx.MessageBox('Out of range!','Error')
            self.FocusAttention(txtCtrl)
            return False
        if type(self.max) != type(None) and number > self.max:
            wx.MessageBox('Out of range!','Error')
            self.FocusAttention(txtCtrl)
            return False
        txtCtrl.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
        txtCtrl.Refresh()
        return True
    
    def FocusAttention(self, widget):
        """
        Bring attention to the non-validating widget
        @param widget: non-validating widget
        """
        widget.SetBackgroundColour("pink")
        widget.SetFocus()
        widget.Refresh()
    
    def TransferToWindow(self):
        return

    def TransferFromWindow(self):
        return

    def OnChar(self, event):
        """
        Method for in-place validation of characters typed
        @param event: fired event
        """
        key = event.GetKeyCode()
        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            event.Skip()
            return
        intchar = "0123456789-"
        floatchar = intchar+".e"
        if self.flag == 'int' and chr(key) in intchar:
            event.Skip()
            return
        if self.flag == 'float' and chr(key) in floatchar:
            event.Skip()
            return
        if not wx.Validator_IsSilent():
            wx.Bell()
        return

class ValidTextEntryDialog(wx.Dialog):
    """
    similar to wx.TextEntryDialog but allows a custom validator to be attached
    Method summary:
    Get.Value() - returns the value of the text field
    """
    def __init__(self, parent, id, caption, defaultValue, validator):
        wx.Dialog.__init__(self, parent, id, caption)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.txt = wx.TextCtrl(self, -1, defaultValue, validator=validator)
        sizer.Add(self.txt,0,0)
        
        hbox = wx.StdDialogButtonSizer()
        okBtn = wx.Button(self, wx.ID_OK, 'OK')
        okBtn.SetDefault()
        closeBtn = wx.Button(self, wx.ID_CANCEL, 'Cancel')
        hbox.AddButton(okBtn)
        hbox.AddButton(closeBtn)
        hbox.Realize()
        
        sizer.Add(hbox)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()
    
    def GetValue(self):
        return self.txt.GetValue()
    
class OneParamFilePanel(wx.Panel):
    """
    Provides wxPython class for simple panel to:
    - open a file,
    - enter one parameter,
    - process file with this parameter.
    Method summary:
    GetParam() - returns value of the parameter text field
    GetFilename() - returns path to the file opened
    """
    def __init__(self, parent, id, processor,
                 paramname = "Parameter", processname = "Process!",
                 wildcards = "All files (*.*)|*.*"):
        wx.Panel.__init__(self, parent, id)
        self.wildcard = wildcards
        vbox = wx.BoxSizer(wx.VERTICAL)
        filebutton = wx.Button(self, wx.ID_OPEN)
        self.Bind(wx.EVT_BUTTON, self.OnOpenFile, filebutton)
        vbox.Add(filebutton, 0, wx.EXPAND)
        self.filename = ""
        self.filename_short = wx.StaticText(self, -1,
                                            "Using file: %s"%self.filename,
                                            style = wx.ALIGN_CENTER)
        vbox.Add(self.filename_short, 0, wx.EXPAND)

        hbox = wx.BoxSizer()
        hbox.Add(wx.StaticText(self, -1, paramname+":"), 0, wx.EXPAND)
        self.param = wx.TextCtrl(self, -1, style = wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, processor, self.param)
        hbox.Add(self.param, 0, wx.EXPAND)
        vbox.Add(hbox, 0, wx.EXPAND)

        processbutton = wx.Button(self, -1, processname)
        self.Bind(wx.EVT_BUTTON, processor, processbutton)
        vbox.Add(processbutton, 0, wx.EXPAND)
        self.SetSizer(vbox)
        self.Fit()

    def OnOpenFile(self, event):
        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir="",
            defaultFile="",
            wildcard=self.wildcard,
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetPath()
            self.filename_short.SetLabel(
                            "Using file: %s"%os.path.basename(self.filename))
            self.Fit()
        dlg.Destroy()

    def GetParam(self):
        return self.param.GetValue()

    def GetFilename(self):
        return self.filename

if __name__=="__main__":
    print __doc__
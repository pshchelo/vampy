#!/bin/env python
"""
Collection of GUI elements created by Pavlo Shchelokovskyy.
This module cannot be used on it own.
Provides following functions:
    rgba_wx2mplt - Convert wx.Colour to colour format used by matplotlib
Provides following objects:
    OneParamFilePanel - simple panel for processing one file with one parameter;
    NumValidator - validator instance suitable for integers or floats;
    ValidTextEntryDialog - similar to wx.TextEntryDialog but allows a custom validator to be attached
    DoubleSlider - panel with two sliders to visually set 2 values
"""

import wx
import os

def rgba_wx2mplt(wxcolour):
    """
    Convert wx.Colour instance to float tuple of rgba values to range in 0-1 used by matplotlib.
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
    The instance of this class has to be bound to an event handler by itself and not by parent
    (i.e. USE doubleslider.Bind(event, callback) AND NOT parent.Bind(event, callback, doubleslider))
    '''
    def __init__(self, parent, id, 
                 value = (1,100), min=1, max=100, gap = None, 
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 panelstyle=wx.TAB_TRAVERSAL|wx.NO_BORDER, 
                 style=wx.SL_HORIZONTAL, name=wx.PanelNameStr):
        wx.Panel.__init__(self, parent, id, pos=pos, size=size, style=panelstyle, name=name)
        low, high = value
        self.lowslider = wx.Slider(self, -1, low, min, max, style=style)
        self.highslider = wx.Slider(self, -1, high, min, max, style=style)
        if gap != None: # if the coupling between two sliders is set
            self.gap = gap
            self.Bind(wx.EVT_SLIDER, self.OnSlideLow, self.lowslider)
            self.Bind(wx.EVT_SLIDER, self.OnSlideHigh, self.highslider)
        if style & wx.SL_VERTICAL:
            sizer = wx.BoxSizer(wx.HORIZONTAL)
        else:  # horizontal sliders are default
            sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.lowslider, 0, wx.GROW)
        sizer.Add(self.highslider, 0, wx.GROW)
        self.SetSizer(sizer)
        self.Fit()
        
    def GetLow(self):
        return self.lowslider.GetValue()
    def SetLow(self, int):
        return self.lowslider.SetValue(int)
    def GetHigh(self):
        return self.highslider.GetValue()
    def SetHigh(self, int):
        return self.highslider.SetValue(int)
    def GetValue(self):
        return self.GetLow(), self.GetHigh()
    def SetValue(self, value):
        low, high = value
        self.SetLow(low)
        self.SetHigh(high)
    
    Low = property(GetLow, SetLow)
    High = property(GetHigh, SetHigh)
    Value = property(GetValue, SetValue)
    
    def GetMin(self):
        return self.lowslider.GetMin()
    def SetMin(self, int):
        self.lowslider.SetMin(int)
        self.highslider.SetMin(int)
    def GetMax(self):
        return self.lowslider.GetMax()
    def SetMax(self, int):
        self.lowslider.SetMax(int)
        self.highslider.SetMax(int)
    def GetRange(self):
        return self.lowslider.GetRange()
    def SetRange(self, min, max):
        self.lowslider.SetRange(min, max)
        self.highslider.SetRange(min, max)
    
    Min = property(GetMin, SetMin)
    Max = property(GetMax, SetMax)
    Range = property(GetRange, SetRange)
        
    def GetLineSize(self):
        return self.lowslider.GetLineSize()
    def SetLineSize(self, int):
        self.lowslider.SetLineSize(int)
        self.highslider.SetLineSize(int)
    def GetPageSize(self):
        return self.lowslider.GetPageSize()
    def SetPageSize(self, int):
        self.lowslider.SetPageSize(int)
        self.highslider.SetPageSize(int)
    
    LineSize = property(GetLineSize, SetLineSize)
    PageSize = property(GetPageSize, SetPageSize)
    
    def OnSlideLow(self, evt):
       low, high = self.GetValue()
       min, max = self.GetRange()
       if low > max-self.gap:
           self.SetLow(max-self.gap)
           return
       if low > high-self.gap:
           self.SetHigh(low+self.gap)
    
    def OnSlideHigh(self, evt):
       low, high = self.GetValue()
       min, max = self.GetRange()
       if high < min+self.gap:
           self.SetHigh(min+self.gap)
           return
       if high < low+self.gap:
           self.SetLow(high-self.gap)
        
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
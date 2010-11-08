'''
Extra wxPython dialogs for VamPy project
'''

import wx
from libshch import wxutil
from vampy.common import DEFAULT_PRESSACC, DEFAULT_SCALE

class VampyOtherUserDataDialog(wx.Dialog):
    """
    Dialog to collect additional data from user
    
    asks for:
    - number of pressure stage, i.e. the column in the pressure file or  
    the part of the image filename from where to read pressures
    - conversion factor from pixels to micrometers
    - pressure readings accuracy
    
    """
    def __init__(self, parent, id):
        wx.Dialog.__init__(self, parent, id, 'Additional Parameters:')
        
        vsizer = wx.BoxSizer(wx.VERTICAL)
        self.stagerb=wx.RadioBox(self, -1, 'Stage No.', choices = ['1','2'], majorDimension=2)
        vsizer.Add(self.stagerb, 1, wx.GROW)
        
        flsz = wx.FlexGridSizer(-1,2)
        label = wx.StaticText(self, -1, 'Scale (um/pixel)')
        flsz.Add(label, 1)
        self.scale = wx.TextCtrl(self, -1, '%s'%DEFAULT_SCALE, validator = wxutil.NumValidator('float', min=0))
        flsz.Add(self.scale,1)
        
        label = wx.StaticText(self, -1, 'Pressure Accuracy (Pa)')
        flsz.Add(label)
        self.pressacc = wx.TextCtrl(self, -1, '%s'%DEFAULT_PRESSACC, validator = wxutil.NumValidator('float', min=0))
        flsz.Add(self.pressacc)
        
        vsizer.Add(flsz)
        btnbox = wx.StdDialogButtonSizer()
        okBtn = wx.Button(self, wx.ID_OK, 'OK')
        okBtn.SetDefault()
        closeBtn = wx.Button(self, wx.ID_CANCEL, 'Cancel')
        btnbox.AddButton(okBtn)
        btnbox.AddButton(closeBtn)
        btnbox.Realize()
        
        vsizer.Add(btnbox)
        
        self.SetSizer(vsizer)
        self.Layout()
        self.Fit()
    
    def GetData(self):
        scale = float(self.scale.GetValue())
        pressacc = float(self.pressacc.GetValue())
        stage = self.stagerb.GetSelection()        
        return stage, scale, pressacc
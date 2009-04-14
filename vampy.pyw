#!/usr/bin/env python
"""
wxPython GUI for VAMP project
TODO: add values export to files
TODO: create (or copy?) a wx.Frame subclass for holding a matplotlib plot,
probably with the toolbar and status bar
"""
import glob, sys, os
OWNPATH = sys.path[0]
#import re

import wx

from numpy import pi, log
import matplotlib as mplt
mplt.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure

import vampy.load as vload
import vampy.features as vfeat
import vampy.analysis as vanalys
import vampy.fitting as vfit

from myutils.mywx import NumValidator, rgba_wx2mplt
from myutils.base64icons import GetIconBundle

SIDES = ['left','right','top','bottom']
DEFAULT_SCALE = '0.3225'  # Teli CS3960DCL, 20x objective
DEFAULT_PRESSACC = '0.00981'  # 1 micrometer of water stack

class VampyMenuBar(wx.MenuBar):
    '''Menu Bar for wxPython VAMP front-end'''
    def __init__(self, parent):
        wx.MenuBar.__init__(self)
        for eachMenuData in self.menuData(parent):
            menuLabel, menuItems = eachMenuData
            self.Append(self.createMenu(menuItems, parent), menuLabel)

    def menuData(self, parent):
        return [["&File", [
                ("&Open Folder...\tCtrl+O", "Open folder with images", parent.OnOpenFolder),
                ("", "", ""),
                ("&Exit", "Exit application", parent.OnExit)]],
                ["&Help", [
                ("&Help", "Display help", parent.OnHelp),
                ("&About...", "Show info about application", parent.OnAbout)]]]

    def createMenu(self, menuData, parent):
        menu = wx.Menu()
        for eachLabel, eachStatus, eachHandler in menuData:
            if not eachLabel:
                menu.AppendSeparator()
                continue
            menuItem = menu.Append(-1, eachLabel, eachStatus)
            parent.Bind(wx.EVT_MENU, eachHandler, menuItem)
        return menu

class VampyStatusBar(wx.StatusBar):
    '''Status Bar for wxPython VAMP frontend'''
    def __init__(self, parent):
        wx.StatusBar.__init__(self, parent)
        self.SetFieldsCount(1)
        
    def SetPosition(self, evt):
        if evt.inaxes:
            self.SetStatusText('x = %i, y = %i'%(int(evt.xdata), int(evt.ydata)), 0)

class VampyPreprocessPanel(wx.Panel):
    '''Sets parameters to preprocess images'''
    def __init__(self, parent, preprocessor):
        wx.Panel.__init__(self, parent, -1)
        sizer = wx.FlexGridSizer(5,2, 5,5)

        for side in SIDES:
            title = wx.StaticText(self, -1, side+'crop:')
            cropping = wx.TextCtrl(self, -1, '0', 
                                    style = wx.TE_PROCESS_ENTER,
                                    name = side+'crop', validator = NumValidator('int', min=0))
            self.Bind(wx.EVT_TEXT_ENTER, preprocessor, cropping)
            sizer.Add(title, 0, 0)
            sizer.Add(cropping, 0, 0)
            
        title = wx.StaticText(self, -1, 'Orientation:')
        sizer.Add(title, 0, 0)
        orient = wx.Choice(self,-1, choices=SIDES, size = (90,25), 
                            name = 'orient')
        orient.SetSelection (0)
        self.Bind(wx.EVT_CHOICE, preprocessor, orient)
        sizer.Add(orient, 0, 0)
        self.SetSizer(sizer)
        for child in self.GetChildren():
            child.Enable(False)
    
    def Initialize(self):
        for child in self.GetChildren():
            child.Enable(True)
    
    def GetOrient(self):
        return wx.FindWindowByName('orient').GetStringSelection()
    
    def GetCrop(self):
        crops = {}
        for side in SIDES:
            ctrl = wx.FindWindowByName(side+'crop')
            crop = ctrl.GetValue()
            crops[side] = int(crop)
        return crops

class VampyProcessPanel(wx.Panel):
    """Shows other parameters needed for starting processing of images."""
    def __init__(self, parent, id, processor):
        wx.Panel.__init__(self, parent, id)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        paramsizer = wx.FlexGridSizer(2,2)
        self.numparams = ('sigma','mismatch')
        self.boolparams = ('subpix','extra')
        for param in self.numparams:
            label = wx.StaticText(self, -1, param)
            val = wx.TextCtrl(self, -1, '0', name = param, validator = NumValidator('float', min = 0))
            paramsizer.AddMany([(label,0,0), (val,0,0)])
        
        for param in self.boolparams:
            cb = wx.CheckBox(self, -1, param+"?", style=wx.ALIGN_RIGHT, name=param)
            paramsizer.Add(cb,0,0)
        
        label = wx.StaticText(self, -1, 'mode')
        val = wx.Choice(self, -1, choices=('phc','dic'), name = 'mode')
        val.SetSelection(0)
        paramsizer.AddMany([(label,0,0), (val,0,0)])
        
        label = wx.StaticText(self, -1, 'polar')
        val = wx.Choice(self, -1, choices=('left','right'), name = 'polar')
        val.SetSelection(0)
        paramsizer.AddMany([(label,0,0), (val,0,0)])        
        
        vsizer.Add(paramsizer)
        
        btn = wx.Button(self, -1, 'Start')
        self.Bind(wx.EVT_BUTTON, processor, btn)
        vsizer.Add(btn)
        
        self.SetSizer(vsizer)
        self.Fit()
        self.SetState(False)
    
    def Initialize(self):
        self.SetState(True)
        for param in self.numparams:
            ctrl = wx.FindWindowByName(param)
            ctrl.SetValue('3')
        for param in self.numparams:
            ctrl = wx.FindWindowByName(param)
            ctrl.Enable(False)
        for cb in self.boolparams:
            ctrl = wx.FindWindowByName(cb)
            ctrl.Enable(False)
        
    def SetState(self, state):
        for child in self.GetChildren():
            child.Enable(state)
    
    def GetParams(self):
        params = {}
        for param in self.numparams:
            ctrl = wx.FindWindowByName(param)
            params[param] = float(ctrl.GetValue())
        for param in self.boolparams:
            params[param] = wx.FindWindowByName(param).GetValue()
        
        mode = wx.FindWindowByName('mode').GetStringSelection()
        polar = wx.FindWindowByName('polar').GetStringSelection()
        params['mode'] = mode, polar
        
        return params

class VampyImagePanel(wx.Panel):
    '''Shows image and sliders affecting image'''
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        
        self.Imgs = None
        
        vsizer = wx.BoxSizer(wx.VERTICAL)
        self.figure = Figure(facecolor = rgba_wx2mplt(self.GetBackgroundColour()))
        
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.canvas.mpl_connect('motion_notify_event', parent.statusbar.SetPosition)
        vsizer.Add(self.canvas, 1, wx.ALIGN_LEFT|wx.ALIGN_TOP|wx.GROW)
        
        slidersizer = wx.FlexGridSizer(cols=2)
        self.ImgNoTxt = wx.TextCtrl(self, -1, "0", size=(50,20),
                                style = wx.TE_READONLY | wx.TE_CENTER)
        slidersizer.Add(self.ImgNoTxt, 0)
        self.ImgNoSlider = wx.Slider(self, -1, 1, 0, 1)
        self.Bind(wx.EVT_SCROLL, self.OnSlide, self.ImgNoSlider)        
        slidersizer.Add(self.ImgNoSlider, 1, wx.GROW)
        
        self.paramsliders = {}
        ### structure - name:(title, colour, initial value); initial value < 0 means from the end
        self.paramsdata = {'minaspest':('Aspirated', 'yellow', 1), 'minvesest':('Vesicle','green', -1)}
        for key in sorted(self.paramsdata.keys()):
            label = wx.StaticText(self, -1, self.paramsdata[key][0])
            label.SetBackgroundColour(self.paramsdata[key][1])
            slidersizer.Add(label, 0, wx.ALIGN_RIGHT)
            slider = wx.Slider(self, -1, 1, 0, 1, name = key)
            self.Bind(wx.EVT_SCROLL, self.OnSlide, slider)
            slidersizer.Add(slider, 1, wx.GROW|wx.ALIGN_LEFT)
            self.paramsliders[key] = slider
        slidersizer.AddGrowableCol(1,1)
        vsizer.Add(slidersizer, 0, wx.GROW)
        for child in self.GetChildren():
            child.Enable(False)
        self.SetSizer(vsizer)
        self.Fit()
        
    def GetImgNo(self):
        return self.ImgNoSlider.GetValue()
        
    def SetImgNo(self):
        self.ImgNoTxt.SetValue(str(self.GetImgNo()))
    
    def SetRanges(self):
        for slider in self.paramsliders.values():
            if slider.GetValue() >= self.Imgs.shape[2]:
                slider.SetValue(self.Imgs.shape[2]-1)
            slider.SetRange(0,self.Imgs.shape[2])
    
    def Initialize(self):
        '''Draw the first image and initialize sliders'''
        for child in self.GetChildren():
            child.Enable(True)
        self.ImgNoSlider.SetRange(1, len(self.Imgs))
        self.ImgNoSlider.SetValue(1)
        self.SetImgNo()
        
        for key in self.paramsliders.keys():
            slider = self.paramsliders[key]
            slider.SetRange(0,self.Imgs.shape[2]-1)
            init = self.paramsdata[key][2]
            if init >= 0:
                slider.SetValue(init)
            else:
                slider.SetValue(self.Imgs.shape[2]+init-1)
        self.Draw()
    
    def GetParams(self):
        params = {}
        params['images'] = self.Imgs
        for key in self.paramsdata:
            sldr = self.paramsliders[key]
            params[key] = sldr.GetValue()
        return params
    
    def OnSlide(self, evt):
        self.SetImgNo()
        #FIXME: too explicit, find more general way
        if self.paramsliders['minaspest'].GetValue() > self.paramsliders['minvesest'].GetValue():
            self.paramsliders['minaspest'].SetValue(self.paramsliders['minvesest'].GetValue())
        self.Draw()

    def Draw(self):
        '''refresh image pane'''
        ImgNo = self.GetImgNo()
        self.axes.clear()
        for key in self.paramsdata.keys():
            sldr = self.paramsliders[key]
            value = sldr.GetValue()
            self.axes.axvline(value, color = self.paramsdata[key][1])
        self.axes.imshow(self.Imgs[ImgNo-1], cmap = mplt.cm.gray)
        self.canvas.draw()
    
class VampyFrame(wx.Frame):
    '''wxPython VAMP frontend'''
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        
        self.OpenedImgs = None
        self.menubar = VampyMenuBar(self)
        self.SetMenuBar(self.menubar)
        
        self.statusbar = VampyStatusBar(self)
        self.SetStatusBar(self.statusbar)
        
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.imgpanel = VampyImagePanel(self, -1)
        hsizer.Add(self.imgpanel, 1, wx.GROW)
        
        paramssizer = wx.BoxSizer(wx.VERTICAL)
        self.preprocpanel = VampyPreprocessPanel(self, self.Preprocess)
        paramssizer.Add(self.preprocpanel, 1, wx.ALL|wx.GROW)
        
        self.procpanel = VampyProcessPanel(self, -1, self.Process)
        paramssizer.Add(self.procpanel, 1, wx.ALL|wx.GROW)
        hsizer.Add(paramssizer, 0, wx.GROW)
        self.SetSizer(hsizer)
        self.Fit()
        self.Centre()
        self.SetIcons(GetIconBundle('wxblockslogoset'))
    
    def OnOpenFolder(self, evt):
        """
        Open directory of files, load them and initialise GUI
        @param evt: incoming event from caller
        """
        dirDlg = wx.DirDialog(self, message="Choose a directory",
                                defaultPath = OWNPATH)
        if dirDlg.ShowModal() != wx.ID_OK:
            dirDlg.Destroy()
            return
        folder = dirDlg.GetPath()
        dirDlg.Destroy()
        #TODO: add choice of file extension, tif or png
        extensions = ['png','tif']
        extDlg = wx.SingleChoiceDialog(self, 'Choose image file type', 'File type', extensions)
        if extDlg.ShowModal() != wx.ID_OK:
            extDlg.Destroy()
            return
        fileext = extDlg.GetStringSelection()
        extDlg.Destroy()
        
        filenames = glob.glob(folder+'/*.'+fileext)
        if len(filenames) == 0:
            msg = "No such files in the selected folder!"
            self.OnError(msg)
            self.OnOpenFolder(evt)
        else:
            filenames.sort()
            self.OpenedImgs, msg = vload.read_images(filenames)
            if msg:
                self.OnError(msg)
                self.OnOpenFolder(evt)
            else:
                self.imgpanel.Imgs = self.OpenedImgs.copy()
                self.imgpanel.Initialize()
                self.preprocpanel.Initialize()
                self.procpanel.Initialize()
    
    def OnError(self, msg):
        """
        Display an error dialog
        @param msg: error message to display (type = string)
        """
        errDlg = wx.MessageDialog(self, msg, "Error!", wx.ICON_ERROR)
        errDlg.ShowModal()
        errDlg.Destroy()
        
    def Preprocess(self, evt):
        """
        respond to preprocessing parameters
        @param evt: incoming event from caller
        """
        orient = self.preprocpanel.GetOrient()
        if self.preprocpanel.Validate():
            crop = self.preprocpanel.GetCrop()
        else:
            return
        self.imgpanel.Imgs = vload.preproc_images(self.OpenedImgs, orient, crop)
        self.imgpanel.SetRanges()
        self.imgpanel.Draw()
        evt.Skip()
        
    def Process(self, evt):
        """
        start actual processing of images 
        @param evt: incoming event from caller
        """
        if self.procpanel.Validate():
            params = self.procpanel.GetParams()
        else:
            return
        params.update(self.imgpanel.GetParams())
        
        ### testing if 'cancel' was pressed somewhere (None is returned)
        try:
            pressures, pressacc, scale = self.GetExtraUserData()
        except(TypeError):
            return
        
        if len(params['images']) % len(pressures) != 0:
            self.OnError('Number of images is not multiple of number of pressures!')
            return
        else:
            aver = len(params['images'])/len(pressures)#number of images to average within
        
        out, extra_out = vfeat.locate(**params)
        geometry, mesg = vanalys.get_geometry(**out)
        if mesg:
            self.OnError(mesg)
            return
        avergeom = vanalys.averageImages(aver, **geometry)
        geometryframe = VampyGeometryFrame(self, -1, **avergeom)
        geometryframe.Show()
        
        tensiondata = vanalys.tension_evans(pressures, pressacc, scale, **avergeom)
        tensionframe = VampyTensionsFrame(self, -1, tensiondata)
        tensionframe.Show()
        evt.Skip()
        
    def GetExtraUserData(self):
        fileDlg = wx.FileDialog(self, message="Choose a pressure protocol file",
                                defaultDir = OWNPATH, style = wx.OPEN,
                                wildcard = "Data files (TXT, CSV, DAT)|*.txt;*.TXT;*.csv;*.CSV;*.dat;*.DAT | All files (*.*)|*.*")
        if fileDlg.ShowModal() != wx.ID_OK:
            fileDlg.Destroy()
            return
        filename = fileDlg.GetPath()
        fileDlg.Destroy()
        
        dlg = VampyOtherUserDataDialog(self, -1)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        stage, scale, pressacc = dlg.GetData()
        dlg.Destroy()
        pressures = vload.read_pressures(filename, stage)
        return pressures, pressacc, scale
    
    def OnExit(self, evt):
        self.Close()
        
    def OnAbout(self, evt):
        description = """Vesicle Aspiration with MicroPipettes made with Python
Short instructions:
Open folder with images, rotate so that pipette sticks from the left, crop if needed, set parameters and click start!"""
        info = wx.AboutDialogInfo()
        info.SetName('VAMPy')
        info.SetDescription(description)
        info.AddDeveloper('Pavlo Shchelokovskyy')
        wx.AboutBox(info)
        evt.Skip()
        
    def OnHelp(self, evt):
        #TODO: write a (simple) online help
        self.OnAbout(evt)
    
class VampyOtherUserDataDialog(wx.Dialog):
    """
    Dialog to collect additional data from user
    """
    def __init__(self, parent, id):
        wx.Dialog.__init__(self, parent, id, 'Additional Parameters:')
        
        vsizer = wx.BoxSizer(wx.VERTICAL)
        self.stagerb=wx.RadioBox(self, -1, 'Stage No.', choices = ['1','2'], majorDimension=2)
        vsizer.Add(self.stagerb, 1, wx.GROW)
        
        flsz = wx.FlexGridSizer(-1,2)
        label = wx.StaticText(self, -1, 'Scale (um/pixel)')
        flsz.Add(label, 1)
        self.scale = wx.TextCtrl(self, -1, DEFAULT_SCALE, validator = NumValidator('float', min=0))
        flsz.Add(self.scale,1)
        
        label = wx.StaticText(self, -1, 'Pressure Accuracy (Pa)')
        flsz.Add(label)
        self.pressacc = wx.TextCtrl(self, -1, DEFAULT_PRESSACC, validator = NumValidator('float', min=0))
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

class VampyTensionsFrame(wx.Frame):
    def __init__(self, parent, id, tensiondata):
        wx.Frame.__init__(self, parent, id, title = 'Dilation vs Tension')
        panel = wx.Panel(self, -1)
        self.tau, self.tau_err = tensiondata['tension']
        self.alpha, self.alpha_err = tensiondata['dilation']
        pansizer = wx.BoxSizer(wx.VERTICAL)
        self.figure = Figure(facecolor = rgba_wx2mplt(panel.GetBackgroundColour()))
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(panel, -1, self.figure)
        pansizer.Add(self.canvas, 1, wx.ALIGN_LEFT|wx.ALIGN_TOP|wx.GROW)
        
        self.Slider = wx.Slider(panel, -1, 1, 1, len(self.tau))
        self.Bind(wx.EVT_SCROLL, self.OnSlide, self.Slider)        
        pansizer.Add(self.Slider, 0, wx.GROW)
        panel.SetSizer(pansizer)
        panel.Fit()
        self.SetIcons(GetIconBundle('wxblockslogoset'))
        self.Fit()
        self.Draw()
        
    def OnSlide(self, evt):
        self.Draw()
        evt.Skip()
    
    def Draw(self):
        slider = self.Slider.GetValue()
        self.axes.clear()

        x = self.tau[slider:]
        y = self.alpha[slider:]
        self.axes.plot(self.tau, self.alpha, 'ro', label = 'Measured')
        
#        x_b, y_b, sx_b, sy_b = self.tau[1:slider], self.alpha[1:slider], self.tau_err[1:slider], self.alpha_err[1:slider]
#        x_e, y_e, sx_e, sy_e = self.tau[slider:], self.alpha[slider:], self.tau_err[slider:], self.alpha_err[slider:]
#        slope_b, interc_b, bend, bend_sd = vanalys.bending_evans(x_b, y_b, sx_b, sy_b)
#        slope_e, interc_e, elas, elas_sd = vanalys.elastic_evans(x_e, y_e, sx_e, sy_e)
#
#        self.axes.plot(x_b, vanalys.dilation_bend_evans(x_b, slope_b, interc_b), label = 'Fit low-P')
#        self.axes.plot(x_e, vanalys.dilation_elas_evans(x_e, slope_e, interc_e), label = 'Fit high-P')
#        
#        self.axes.axvline(self.tau[slider])

        fit, fit_sd, mesg, success = vfit.nls_Fournier(x, y)
        
        if success != 1:
            title = 'Fit Error: %s'%mesg
        else:
            a0_T, bend, elas = fit
#            bend_sd, a0_T_sd, elas_sd = fit_sd
#            title = 'kappa = %f +- %f kT; K = %f +- %f mN/m'%(bend, bend_sd, elas/1000., elas_sd/1000.)
            title = 'kappa = %f kT; K = %f mN/m'%(bend, elas/1000.)
            f = vfit.alpha_Fournier()
            self.axes.plot(x, f(fit, x), label = 'Fournier fit')
        self.axes.set_title(title)
        self.axes.legend()
        self.canvas.draw()

class VampyGeometryFrame(wx.Frame):
    def __init__(self, parent, id, **kwargs):
        wx.Frame.__init__(self, parent, id, size = (1024,768), title = 'Vesicle Geometry')
        panel = wx.Panel(self, -1)
        pansizer = wx.BoxSizer()
        self.figure = Figure(facecolor = rgba_wx2mplt(panel.GetBackgroundColour()))
        self.canvas = FigureCanvas(panel, -1, self.figure)
        pansizer.Add(self.canvas, 1, wx.GROW)
        area, area_err = kwargs['area']
        x = xrange(1, len(area)+1)
        
        self.areaplot = self.figure.add_subplot(221, title = 'Area')
        self.areaplot.errorbar(x, area, area_err, fmt='bo-', label='Area')
        
        self.volumeplot = self.figure.add_subplot(222, title = 'Volume')
        volume, volume_err = kwargs['volume']
        self.volumeplot.errorbar(x, volume, volume_err, fmt='bo-',  label='Volume')
        
        self.vesradplot = self.figure.add_subplot(223, title = 'Vesicle Radius')
        vesrad, vesrad_err = kwargs['vesrad']
        self.vesradplot.errorbar(x, vesrad, vesrad_err, fmt='bo-', label='Vesicle Radius')
        
        self.asplplot = self.figure.add_subplot(224, title = 'Aspirated Length')
        aspl, aspl_err = kwargs['aspl']
        self.asplplot.errorbar(x, aspl, aspl_err, fmt='bo-', label='Aspirated Length')
        
        self.SetIcons(GetIconBundle('wxblockslogoset'))
#        sizer.Add(panel, 1, wx.GROW)
        panel.SetSizer(pansizer)
        panel.Fit()
        self.canvas.draw()

class VampyApp(wx.App):
    '''wxPython application for VAMP front end'''
    def OnInit(self):
        frame = VampyFrame(parent=None, id=-1, title='VAMPy')
        frame.Show()
        return True

if __name__ == "__main__":
    app = VampyApp(False)
    app.MainLoop()
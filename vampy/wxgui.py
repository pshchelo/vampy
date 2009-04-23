#!/usr/bin/env python
"""
wxPython GUI for VAMP project
TODO: add values export to files
TODO: create (or copy?) a wx.Frame subclass for holding a matplotlib plot,
probably with the toolbar and status bar
"""
import glob, sys, os
OWNPATH = sys.path[0]

import wx

from numpy import pi, log, empty
import matplotlib as mplt
mplt.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure

import load as vload
import features as vfeat
import analysis as vanalys
import fitting as vfit
import output as vout

from myutils.mywx import NumValidator, rgba_wx2mplt
from myutils.base64icons import GetIconBundle

SIDES = ['left','right','top','bottom']
DEFAULT_SCALE = '0.3225'  # micrometer/pixel, Teli CS3960DCL, 20x objective
DEFAULT_PRESSACC = '0.00981'  # 1 micrometer of water stack
CROP_CFG_FILENAME = 'vampy-crop.cfg'

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
                ("&About...", "Show info about application", parent.OnAbout)]],
                ["Debug", [
                ("Reload modules", "Reload ", parent.OnReload)]]]

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
        Nsides = len(SIDES)
        sizer = wx.GridBagSizer()
        
        for index,side in enumerate(SIDES):
            title = wx.StaticText(self, -1, side+'crop:')
            cropping = wx.TextCtrl(self, -1, '0', 
                                    style = wx.TE_PROCESS_ENTER,
                                    name = side+'crop', validator = NumValidator('int', min=0))
            self.Bind(wx.EVT_TEXT_ENTER, preprocessor, cropping)
            sizer.Add(title, (index,0), (1,1), wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
            sizer.Add(cropping,(index,1),(1,1), wx.ALIGN_LEFT|wx.GROW)
        
        savebtn = wx.Button(self, -1, 'Save crop info')
        self.Bind(wx.EVT_BUTTON, self.OnSave, savebtn)
        sizer.Add(savebtn, (Nsides,0), (1,2), wx.GROW|wx.ALIGN_CENTER_HORIZONTAL)
        
        title = wx.StaticText(self, -1, 'Orientation:')
        sizer.Add(title, (Nsides+1,0), (1,1), wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        orient = wx.Choice(self,-1, choices=SIDES, name = 'orient')
        orient.SetSelection (0)
        self.Bind(wx.EVT_CHOICE, preprocessor, orient)
        sizer.Add(orient, (Nsides+1,1),(1,1), wx.ALIGN_LEFT|wx.GROW)
        
        self.SetSizer(sizer)
        for child in self.GetChildren():
            child.Enable(False)
    
    def Initialize(self, imgcfg):
        for child in self.GetChildren():
            child.Enable(True)
        for side in SIDES:
            cropctrl = wx.FindWindowByName(side+'crop')
            cropctrl.SetValue(str(imgcfg[side]))
    
    def GetOrient(self):
        return wx.FindWindowByName('orient').GetStringSelection()
#    def SetOrient(self, orient):
#        ctrl = wx.FindWindowByName('orient')
#        if orient in SIDES:
#            
#            ctrl
#            return
#        else:
#            mesg = 'Orientation is not valid'
#            wx.MessageDialog(None, mesg, 'Error', wx.OK | wx.ICON_ERROR).ShowModal()
#            return
    
    def GetCrop(self):
        crops = {}
        for side in SIDES:
            ctrl = wx.FindWindowByName(side+'crop')
            crop = ctrl.GetValue()
            crops[side] = int(crop)
        return crops
    
    def OnSave(self, evt):
        crops = self.GetCrop()
        orient = self.GetOrient()
        lines = []
        for key in crops.keys():
            lines.append('%s\t%i\n'%(key, crops[key]))
        try:
            conffile = open(CROP_CFG_FILENAME, 'w')
        except IOError:
            wx.MessageBox('An error occurred while saving crop info', 'Error')
            evt.Skip()
            return    
        conffile.writelines(lines)
        conffile.close()
        wx.MessageBox('Crop info saved', 'Info')
        evt.Skip()

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
        '''Draw the first image and initialise sliders'''
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
        self.folder = dirDlg.GetPath()
        dirDlg.Destroy()
        
        os.chdir(self.folder)
        extensions = ['png','tif']
        extDlg = wx.SingleChoiceDialog(self, 'Choose image file type', 'File type', extensions)
        if extDlg.ShowModal() != wx.ID_OK:
            extDlg.Destroy()
            return
        fileext = extDlg.GetStringSelection()
        extDlg.Destroy()
        
        filenames = glob.glob(self.folder+'/*.'+fileext)
        if len(filenames) == 0:
            msg = "No such files in the selected folder!"
            self.OnError(msg)
            self.OnOpenFolder(evt)
        else:
            filenames.sort()
            self.OpenedImgs, imgcfg, msg = self.LoadImages(filenames)
            if msg:
                self.OnError(msg)
                self.OnOpenFolder(evt)
            else:
                self.preprocpanel.Initialize(imgcfg)
                self.procpanel.Initialize()
                self.imgpanel.Imgs = self.OpenedImgs.copy()
                self.imgpanel.Initialize()
                self.Preprocess(evt)
    
    def LoadImages(self, filenames):
        imgcfgfilename = os.path.join(self.folder, CROP_CFG_FILENAME)
        imgcfg = vload.read_conf_file(imgcfgfilename)
        test, mesg = vload.read_grey_image(filenames[0])
        if mesg:
            return None, imgcfg, mesg
        images = empty((len(filenames), test.shape[0], test.shape[1]), test.dtype)
        progressdlg = wx.ProgressDialog('Loading images','Loading images',len(filenames),
                                        style = wx.PD_AUTO_HIDE|wx.PD_CAN_ABORT|wx.PD_REMAINING_TIME)
        keepLoading = True
        for index, filename in enumerate(filenames):
            ### open the image file
            keepLoading = progressdlg.Update(index+1)
            if not keepLoading:
                mesg = 'Progress cancelled! Not all images have been loaded.'
                break
            img, mesg = vload.read_grey_image(filename)
            if mesg:
                return None, imgcfg, mesg
            ### test that the image has the same shape as others
            if img.shape != test.shape:
                mesg = 'Error: Images have different dimensions!'
                return None, imgcfg, mesg
            images[index, :] = img
        progressdlg.Destroy()
        return images, imgcfg, mesg
        
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
                                defaultDir = self.folder, style = wx.OPEN,
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
    
    def OnReload(self, evt):
        reload(vload)
        reload(vanalys)
        reload(vfeat)
        reload(vout)
        reload(vfit)
        evt.Skip()
        
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
        self.tau, self.tau_err = tensiondata['tension']
        self.alpha, self.alpha_err = tensiondata['dilation']
#        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        
        panel = wx.Panel(self, -1)
        pansizer = wx.BoxSizer(wx.VERTICAL)
        
        self.figure = Figure(facecolor = rgba_wx2mplt(panel.GetBackgroundColour()))
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(panel, -1, self.figure)
        pansizer.Add(self.canvas, 1, wx.ALIGN_LEFT|wx.ALIGN_TOP|wx.GROW)
        
        if self.tau[0] == 0:
            slider = 1
        else:
            slider = 0
        self.Slider = wx.Slider(panel, -1, slider, 0, len(self.tau))
        self.Bind(wx.EVT_SCROLL, self.OnSlide, self.Slider)
        pansizer.Add(self.Slider, 0, wx.GROW)
        panel.SetSizer(pansizer)
#        hsizer.Add(pansizer)
        
#        fitpanel = wx.Panel(self, -1)
#        fitchoice = wx.ListBox(self, -1, choices = vout.FITS_IMPLEMENTED.keys())
#        hsizer.Add(fitpanel)
        
        panel.Fit()
        self.SetIcons(GetIconBundle('wxblockslogoset'))
#        self.SetSizer(hsizer)
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
        sx = self.tau_err[slider:]
        sy = self.alpha_err[slider:]
        self.axes.plot(self.tau, self.alpha, 'ro', label = 'Measured')
        
#        x_b, y_b, sx_b, sy_b = self.tau[1:slider], self.alpha[1:slider], self.tau_err[1:slider], self.alpha_err[1:slider]
#        x_e, y_e, sx_e, sy_e = self.tau[slider:], self.alpha[slider:], self.tau_err[slider:], self.alpha_err[slider:]
#        slope_b, interc_b, bend, bend_sd = vanalys.bending_evans(x_b, y_b, sx_b, sy_b)
#        slope_e, interc_e, elas, elas_sd = vanalys.elastic_evans(x_e, y_e, sx_e, sy_e)
#
#        self.axes.plot(x_b, vanalys.dilation_bend_evans(x_b, slope_b, interc_b), label = 'Fit low-P')
#        self.axes.plot(x_e, vanalys.dilation_elas_evans(x_e, slope_e, interc_e), label = 'Fit high-P')
        
#        self.axes.axvline(self.tau[slider])

#        fit, fit_sd, mesg, success = vfit.nls_Fournier(x, y)
        fit = vfit.odrlinlog(x, y, sx, sy)
        bend, intercept = fit.beta
        
        bend_sd, intercept_sd = fit.sd_beta
        success = 1
        if success != 1:
            title = 'Fit Error: %s'%mesg
        else:
#            a0_T, bend, elas = fit
#            bend_sd, a0_T_sd, elas_sd = fit_sd
#            title = 'kappa = %f +- %f kT; K = %f +- %f mN/m'%(bend, bend_sd, elas/1000., elas_sd/1000.)
#            title = 'kappa = %f kT; K = %f mN/m'%(bend, elas/1000.)
#            f = vfit.alpha_Fournier()
#            self.axes.plot(x, f(fit, x), label = 'Fournier fit')
            title = 'kappa = %f +- %f kT'%(1/(8*pi*bend), bend_sd/(8*pi*bend))
            f = vanalys.dilation_bend_evans
            self.axes.plot(x, f(x, bend, intercept), label = 'Evans fit')
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
        
        aspl, aspl_err = kwargs['aspl']
        x = xrange(1, len(aspl)+1)
        self.asplplot = self.figure.add_subplot(221, title = 'Aspirated Length')
        self.asplplot.errorbar(x, aspl, aspl_err, fmt='bo-', label='Aspirated Length')
        
        self.vesradplot = self.figure.add_subplot(222, title = 'Vesicle Radius')
        vesrad, vesrad_err = kwargs['vesrad']
        self.vesradplot.errorbar(x, vesrad, vesrad_err, fmt='bo-', label='Vesicle Radius')
        
        self.areaplot = self.figure.add_subplot(223, title = 'Area')
        area, area_err = kwargs['area']
        self.areaplot.errorbar(x, area, area_err, fmt='bo-', label='Area')
        
#        self.volumeplot = self.figure.add_subplot(224, title = 'Volume')
#        volume, volume_err = kwargs['volume']
#        self.volumeplot.errorbar(x, volume, volume_err, fmt='bo-',  label='Volume')
        
        self.veslplot = self.figure.add_subplot(224, title = 'Outer Radius')
        vesl, vesl_err = kwargs['vesl']
        self.veslplot.errorbar(x, vesl, vesl_err, fmt='bo-',  label='Outer Radius')
        
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
    app = VampyApp(True)
    app.MainLoop()
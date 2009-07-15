#!/usr/bin/env python
'''Top frame of the VamPy application
'''
import glob, os

import wx

from numpy import empty

import matplotlib as mplt
mplt.use('WXAgg', warn=False)
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar2
from matplotlib.figure import Figure

import vampy
from vampy import analysis, features, load

import tension, debug, geometry

import libshch
from libshch import wxutil, util

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
        self.scale = wx.TextCtrl(self, -1, '%s'%vampy.DEFAULT_SCALE, validator = wxutil.NumValidator('float', min=0))
        flsz.Add(self.scale,1)
        
        label = wx.StaticText(self, -1, 'Pressure Accuracy (Pa)')
        flsz.Add(label)
        self.pressacc = wx.TextCtrl(self, -1, '%s'%vampy.DEFAULT_PRESSACC, validator = wxutil.NumValidator('float', min=0))
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

class VampyImageConfigPanel(wx.Panel):
    '''Sets parameters to configure the image properties'''
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        box = wx.StaticBox(self, -1, 'Image Config')
        boxsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        cropbox = wx.StaticBox(self, -1, 'Croppings')
        cropboxsizer = wx.StaticBoxSizer(cropbox, wx.VERTICAL)
        cropsizer = wx.FlexGridSizer(cols=2)
        
        for index,side in enumerate(vampy.SIDES):
            title = wx.StaticText(self, -1, side)
            cropping = wx.TextCtrl(self, -1, '0', 
                                    style = wx.TE_PROCESS_ENTER,
                                    name = side+'crop', validator = wxutil.NumValidator('int', min=0))
            self.Bind(wx.EVT_TEXT_ENTER, parent.OnConfigImage, cropping)
            cropsizer.Add(title, 1, wx.GROW|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
            cropsizer.Add(cropping, 1, wx.ALIGN_LEFT|wx.GROW)
        cropsizer.AddGrowableCol(1)
        cropboxsizer.Add(cropsizer, 1, wx.GROW)
        boxsizer.Add(cropboxsizer, 1, wx.GROW)
        
        sizer = wx.FlexGridSizer(cols=2)
        for value in self.ChoiceParams():
            paramname, longName, choices = value
            label = wx.StaticText(self, -1, paramname)
            chbox = wx.Choice(self, -1, choices=choices, name=paramname)
            sizer.Add(label, 1, wx.GROW|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
            sizer.Add(chbox, 1, wx.GROW|wx.ALIGN_LEFT)
        sizer.AddGrowableCol(0)
        sizer.AddGrowableCol(1)
        boxsizer.Add(sizer, 0, wx.GROW)
        self.Bind(wx.EVT_CHOICE, parent.OnConfigImage, wx.FindWindowByName('orient'))
        self.Bind(wx.EVT_CHOICE, self.OnModeChoice, wx.FindWindowByName('mode'))
        
        for boolparam in self.BoolParams():
            cb = wx.CheckBox(self, -1, boolparam+"?", style=wx.ALIGN_LEFT, name=boolparam)
            boxsizer.Add(cb, 0, wx.ALIGN_LEFT)

        self.SetSizer(boxsizer)
        self.Fit()
        for child in self.GetChildren():
            child.Enable(False)
    
    def ChoiceParams(self):
        return (
                ('orient', 'Pipette orientation', vampy.SIDES),
                ('mode', 'Image mode', ('phc', 'dic')),
                ('polar', 'DiC polarization', ('left', 'right'))
                )
    
    def BoolParams(self):
        return ('fromnames', 'darktip')
    
    def Initialize(self, imgcfg):
        for child in self.GetChildren():
            child.Enable(True)
        for side in vampy.SIDES:
            cropctrl = wx.FindWindowByName(side+'crop')
            cropctrl.SetValue(str(imgcfg.get(side, 0)))
        
        for value in self.ChoiceParams():
            paramname, LongName, choices = value
            ctrl = wx.FindWindowByName(paramname)
            ctrl.SetStringSelection(imgcfg.get(paramname, choices[0]))
        self.OnModeChoice(wx.EVT_CHOICE)
        
        for boolparam in self.BoolParams():
            cb = wx.FindWindowByName(boolparam)
            cb.SetValue(int(imgcfg.get(boolparam, 0)))
    
    def GetCrop(self):
        crops = {}
        for side in vampy.SIDES:
            ctrl = wx.FindWindowByName(side+'crop')
            crop = ctrl.GetValue()
            crops[side] = int(crop)
        return crops
    
    def GetOrient(self):
        return wx.FindWindowByName('orient').GetStringSelection()
        
    def GetChoices(self):
        params = {}
        for value in self.ChoiceParams():
            paramname, longName, choices = value
            params[paramname] = wx.FindWindowByName(paramname).GetStringSelection() #to convert from unicode
        return params
        
    def GetBools(self):
        params = {}
        for boolparam in self.BoolParams():
            params[boolparam] = wx.FindWindowByName(boolparam).GetValue()
        return params
    
    def GetParams(self):
        params = self.GetChoices()
        params.update(self.GetBools())
        params.update(self.GetCrop())
        return params
    
    def OnModeChoice(self, evt):
        modectrl = wx.FindWindowByName('mode')
        polarctrl = wx.FindWindowByName('polar')
        if modectrl.GetStringSelection() == 'dic':
            polarctrl.Enable(True)
        else:
            polarctrl.Enable(False)

class VampyAnalysisPanel(wx.Panel):
    """Shows other parameters needed for starting processing of images."""
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        box = wx.StaticBox(self, -1, 'Analysis Options')
        vsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        paramsizer = wx.FlexGridSizer(2,2)
        self.numparams = ('sigma','mismatch')
        self.boolparams = ('subpix','extra')
        
        for param in self.numparams:
            label = wx.StaticText(self, -1, param)
            val = wx.TextCtrl(self, -1, '0', name = param, validator = wxutil.NumValidator('float', min = 0))
            paramsizer.AddMany([(label,0,0), (val,0,0)])
        
        for param in self.boolparams:
            cb = wx.CheckBox(self, -1, param+"?", style=wx.ALIGN_LEFT, name=param)
            paramsizer.Add(cb,0,0)
        
        vsizer.Add(paramsizer)
        
        btn = wx.Button(self, -1, 'Analyse')
        self.Bind(wx.EVT_BUTTON, parent.OnAnalyse, btn)
        vsizer.Add(btn)
        
        self.SetSizer(vsizer)
        self.Fit()
        self.SetState(False)
        
    def Initialize(self):
        self.SetState(True)
        for param in self.numparams:
            ctrl = wx.FindWindowByName(param)
            ctrl.SetValue('3')
            ctrl.Enable(False)
        ### temporarily disabled, since not well implemented yet
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
        return params

class VampyImagePanel(wx.Panel):
    '''Shows image and sliders affecting image'''
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id, style = wx.BORDER_SUNKEN)
        
        self.Imgs = None
        
        vsizer = wx.BoxSizer(wx.VERTICAL)
        self.figure = Figure(facecolor = wxutil.rgba_wx2mplt(self.GetBackgroundColour()))
        
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.canvas.mpl_connect('motion_notify_event', parent.statusbar.SetPosition)
        vsizer.Add(self.canvas, 1, wx.ALIGN_LEFT|wx.ALIGN_TOP|wx.GROW)
        
        
#        self.im = self.axes.imshow(empty((1,1)), aspect='equal', cmap=mplt.cm.gray)
#        self.pipest = self.axes.axvspan(0,0, fc='g', alpha=0.5)
#        self.minaspest = self.axes.axvline(0)
#        self.minvesest = self.axes.axvline(0)
#        self.pipaxis, = self.axes.plot([], [], 'y--')
#        self.upinwallline, = self.axes.plot([],[], 'y-')
#        self.lowinwallline, = self.axes.plot([],[], 'y-')
#        self.upoutwallline, = self.axes.plot([],[], 'y-')
#        self.lowoutwallline, = self.axes.plot([],[], 'y-')
        
        
        navtoolbar = NavigationToolbar2(self.canvas)
        navtoolbar.Realize()
        vsizer.Add(navtoolbar, 0, wx.ALIGN_LEFT|wx.GROW)
        
        slidersizer = wx.FlexGridSizer(cols=2)
        self.ImgNoTxt = wx.TextCtrl(self, -1, "0", size=(50,20),
                                style = wx.TE_READONLY | wx.TE_CENTER)
        slidersizer.Add(self.ImgNoTxt, 0)
        self.ImgNoSlider = wx.Slider(self, -1, 1, 0, 1)
        self.Bind(wx.EVT_SCROLL, self.OnSlide, self.ImgNoSlider)        
        slidersizer.Add(self.ImgNoSlider, 1, wx.GROW)
        
        self.paramsliders = []
        
        regionlabel = wx.StaticText(self, -1, 'Aspirated\nVesicle')
        slidersizer.Add(regionlabel, 0, wx.ALIGN_RIGHT)
        self.regionslider = wxutil.DoubleSlider(self, -1, (0,1), 0, 1, gap=2, name='aspves')
        self.Bind(wx.EVT_SLIDER, self.OnSlide, self.regionslider)
        self.paramsliders.append(self.regionslider)
        slidersizer.Add(self.regionslider, 1, wx.GROW|wx.ALIGN_LEFT)
        
        tiplabel = wx.StaticText(self, -1, 'Pipette Tip')
        slidersizer.Add(tiplabel, 0, wx.ALIGN_RIGHT)
        self.tipslider = wxutil.DoubleSlider(self, -1, (0,1), 0, 1, gap=2, name='tip')
        self.Bind(wx.EVT_SLIDER, self.OnSlide, self.tipslider)
        self.paramsliders.append(self.tipslider)
        slidersizer.Add(self.tipslider, 1, wx.GROW|wx.ALIGN_LEFT)
        
        slidersizer.AddGrowableCol(1,1)
        vsizer.Add(slidersizer, 0, wx.GROW)
        
        hsizer = wx.BoxSizer()
        axslidersizer = wx.FlexGridSizer(rows=2)
        
        name = 'axis'
        label = wx.StaticText(self, -1, name)
        axslidersizer.Add(label)
        self.axisslider = wxutil.DoubleSlider(self, -1, (0,1), 0, 1, style=wx.SL_VERTICAL, name=name)
        self.Bind(wx.EVT_SLIDER, self.OnSlide, self.axisslider)
        
        name = 'pipette'
        label = wx.StaticText(self, -1, name)
        self.pipetteslider = wxutil.DoubleSlider(self, -1, (0,1), 0, 1, style=wx.SL_VERTICAL, name=name)
        self.Bind(wx.EVT_SLIDER, self.OnSlide, self.pipetteslider)
        axslidersizer.Add(label)
        
        axslidersizer.Add(self.axisslider, 1, wx.GROW|wx.ALIGN_TOP)
        axslidersizer.Add(self.pipetteslider, 1, wx.GROW|wx.ALIGN_TOP)
        
        self.paramsliders.append(self.axisslider)
        self.paramsliders.append(self.pipetteslider)
            
        axslidersizer.AddGrowableRow(1,1)
        hsizer.Add(axslidersizer, 0, wx.GROW)
        hsizer.Add(vsizer, 1, wx.GROW)
        for child in self.GetChildren():
            child.Enable(False)
        self.SetSizer(hsizer)
        self.Fit()
        
    def GetImgNo(self):
        return self.ImgNoSlider.GetValue()
        
    def SetImgNo(self):
        self.ImgNoTxt.SetValue(str(self.GetImgNo()))
#    
    def SetRanges(self):
        imgno, ysize, xsize = self.Imgs.shape
        self.regionslider.SetRange(0,xsize-1)
        self.tipslider.SetRange(0,xsize-1)
        self.axisslider.SetRange(0, ysize-1)
        self.pipetteslider.SetRange(0, ysize/2)
    
    def Initialize(self):
        '''Draw the first image and initialise sliders'''
        for child in self.GetChildren():
            child.Enable(True)
        self.ImgNoSlider.SetRange(1, len(self.Imgs))
        self.ImgNoSlider.SetValue(1)
        self.SetImgNo()
        ImgsNo, ysize, xsize = self.Imgs.shape

        self.regionslider.SetRange(0, xsize-1)
        self.regionslider.SetValue((1, xsize-2))
        
        self.tipslider.SetRange(0, xsize-1)
        self.tipslider.SetValue((xsize/2, xsize/2+1))
        
        self.axisslider.SetRange(0, ysize-1)
        self.axisslider.SetValue((ysize/2, ysize/2))
        self.pipetteslider.SetRange(0, ysize/2)
        self.pipetteslider.SetValue((ysize/4, ysize/4))
        self.Draw()
    
    def GetParams(self):
        params = self.GetSlidersPos()
        params['images'] = self.Imgs
        return params
    
    def GetSlidersPos(self):
        params = {}
        for slider in self.paramsliders:
            key = str(slider.GetName())
            params[key] = slider.GetValue()
        return params
    
    def SetSlidersPos(self, imgcfg):
#===============================================================================
#        Here the actual names of parameters are referenced by hardcoding
#===============================================================================
        imgno, ysize, xsize = self.Imgs.shape
        
        strvalue = imgcfg.get('aspves', '')
        value, mesg = util.split_to_int(strvalue, (0, xsize-1))
        if mesg:
            self.GetParent().OnError(mesg)
        self.regionslider.SetValue(value)
        
        strvalue = imgcfg.get('tip', '')
        value, mesg = util.split_to_int(strvalue, (xsize/2, xsize/2+1))
        if mesg:
            self.GetParent().OnError(mesg)
        self.tipslider.SetValue(value)
        
        for key in ('axis','pipette'):
            strvalue = imgcfg.get(key, '')
            value, mesg = util.split_to_int(strvalue, (0, ysize/4))
            if mesg:
                self.GetParent().OnError(mesg)
            wx.FindWindowByName(key).SetValue(value)
        
        self.Draw()
            
    def OnSlide(self, evt):
        self.SetImgNo()
        self.Draw()

    def Draw(self):
        '''refresh image pane'''
        ImgNo = self.GetImgNo()
        self.axes.clear()
        for value in self.regionslider.GetValue():
            self.axes.axvline(value)
        ydots = self.axisslider.GetValue()
        xdots = [0, self.regionslider.GetLow()]
        self.axes.plot(xdots, ydots, 'y--')
        
        tiplimleft, tiplimright = self.tipslider.GetValue()
        self.axes.axvspan(tiplimleft, tiplimright, fc='g', alpha=0.5)
        
        piprad, pipthick = self.pipetteslider.GetValue()
        
        line1 = [ydots[0]+piprad+pipthick, ydots[1]+piprad+pipthick]
        line2 = [ydots[0]+piprad, ydots[1]+piprad]
        line3 = [ydots[0]-piprad, ydots[1]-piprad]
        line4 = [ydots[0]-piprad-pipthick, ydots[1]-piprad-pipthick]
        
        self.axes.plot(xdots, line1, 'y-')
        self.axes.plot(xdots, line2, 'y-')
        self.axes.plot(xdots, line3, 'y-')
        self.axes.plot(xdots, line4, 'y-')
        
        self.axes.imshow(self.Imgs[ImgNo-1], aspect='equal', cmap=mplt.cm.gray)
        
#        self.im.set_array(self.Imgs[ImgNo-1])
        
#        self.axes.relim()
#        self.axes.autoscale_view()
        self.canvas.draw()
        
    
class VampyFrame(wx.Frame):
    '''wxPython VAMP frontend'''
    def __init__(self, parent, id):
        self.maintitle = 'VamPy'
        wx.Frame.__init__(self, parent, id, title=self.maintitle)
        customartprovider = wxutil.CustomArtProvider()
        wx.ArtProvider.Push(customartprovider)
        
        self.folder = None
        self.OpenedImgs = None
        
        self.menubar = wxutil.SimpleMenuBar(self, self.MenuData())
        self.SetMenuBar(self.menubar)
        
        self.toolbar = wxutil.SimpleToolbar(self, *self.ToolbarData())
        self.SetToolBar(self.toolbar)
        self.toolbar.Realize()
        
        self.statusbar = wxutil.PlotStatusBar(self)
        self.SetStatusBar(self.statusbar)
        
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.imgpanel = VampyImagePanel(self, -1)
        hsizer.Add(self.imgpanel, 1, wx.GROW)
        
        paramssizer = wx.BoxSizer(wx.VERTICAL)

        self.imgconfpanel = VampyImageConfigPanel(self)
        paramssizer.Add(self.imgconfpanel, 0, wx.ALL|wx.GROW)
        
        self.analysispanel = VampyAnalysisPanel(self, -1)
        paramssizer.Add(self.analysispanel, 0, wx.ALL|wx.GROW)
        
        emptypanel = wx.Panel(self, -1)
        paramssizer.Add(emptypanel, 1, wx.ALL|wx.GROW)
        hsizer.Add(paramssizer, 0, wx.GROW)
        self.SetSizer(hsizer)
        self.Fit()
        self.Centre()
        
        self.SetFrameIcons(libshch.WXPYTHON, (16,24,32))
        
    def SetFrameIcons(self, artid, sizes):
        ib = wx.IconBundle()
        for size in sizes:
            ib.AddIcon(wx.ArtProvider.GetIcon(artid, size = (size,size)))
        self.SetIcons(ib)
    
    def ToolbarData(self):
        bmpsavetxt = wx.ArtProvider.GetBitmap(libshch.SAVETXT, wx.ART_TOOLBAR, (24,24))
        return ((
                (bmpsavetxt, 'Save Image Info', 'Save image info', False),
                 self.OnSave),
                )
    
    def MenuData(self):
        return [["&File", [
                ("&Open Folder...\tCtrl+O", "Open folder with images", self.OnOpenFolder),
                ("", "", ""),
                ("&Exit", "Exit application", self.OnExit)]],
                ["&Help", [
                ("&Help", "Display help", self.OnHelp),
                ("&About...", "Show info about application", self.OnAbout)]],
                ["Debug", [
                ("Reload", "Reload all dependencies", self.OnReload),
                ("Debug image", "Debug current image", self.OnDebugImage)]]]
             
    def OnOpenFolder(self, evt):
        """
        Open directory of files, load them and initialise GUI
        @param evt: incoming event from caller
        """
        if not self.folder:
            self.folder = vampy.OWNPATH
        dirDlg = wx.DirDialog(self, message="Choose a directory",
                                defaultPath = self.folder)
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
        
        self.imgfilenames = glob.glob(self.folder+'/*.'+fileext)
        if len(self.imgfilenames) == 0:
            msg = "No such files in the selected folder!"
            self.OnError(msg)
            self.OnOpenFolder(evt)
        else:
            self.imgfilenames.sort()
            self.OpenedImgs, imgcfg, msg = self.LoadImages()
            if msg:
                self.OnError(msg)
                self.OnOpenFolder(evt)
            else:
                self.imgconfpanel.Initialize(imgcfg)
                self.analysispanel.Initialize()
                self.imgpanel.Imgs = self.OpenedImgs
                self.imgpanel.Initialize()
                self.OnConfigImage(evt)
                self.imgpanel.SetSlidersPos(imgcfg)
                upperdir, self.imagedir = os.path.split(self.folder)
                dir, self.imagedate = os.path.split(upperdir)
                title = '%s : %s - %s'%(self.imagedate, self.imagedir, self.maintitle)
                self.SetTitle(title)
    
    def LoadImages(self):
        if self.OpenedImgs != None:
#            del(self.OpenedImgs)
            self.OpenedImgs = None
        imgcfgfilename = os.path.join(self.folder, vampy.CFG_FILENAME)
        imgcfg = load.read_conf_file(imgcfgfilename)
        test, mesg = load.read_grey_image(self.imgfilenames[0])
        if mesg:
            return None, imgcfg, mesg
        try:
            images = empty((len(self.imgfilenames), test.shape[0], test.shape[1]), test.dtype)
        except MemoryError:
            mesg = 'Memory Leak. Restart the application.'
            self.OnError(mesg)
#            images = None
            return
        progressdlg = wx.ProgressDialog('Loading images','Loading images',len(self.imgfilenames),
                                        style = wx.PD_AUTO_HIDE|wx.PD_CAN_ABORT|wx.PD_REMAINING_TIME)
        keepLoading = True
        for index, filename in enumerate(self.imgfilenames):
            ### open the image file
            keepLoading = progressdlg.Update(index+1)
            if not keepLoading:
                mesg = 'Progress cancelled! Not all images have been loaded.'
                break
            img, mesg = load.read_grey_image(filename)
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
        
    def OnConfigImage(self, evt):
        """
        respond to preprocessing parameters
        @param evt: incoming event from caller
        """
        orient = self.imgconfpanel.GetOrient()
        if self.imgconfpanel.Validate():
            crop = self.imgconfpanel.GetCrop()
        else:
            return
        self.imgpanel.Imgs = load.preproc_images(self.OpenedImgs, orient, crop)
        self.imgpanel.SetRanges()
        self.imgpanel.Draw()
        
    def OnAnalyse(self, evt):
        """
        starts actual image analysis 
        @param evt: incoming event from caller
        """
        if self.analysispanel.Validate():
            params = self.analysispanel.GetParams()
        else:
            return
        params.update(self.imgpanel.GetParams())
        params.update(self.imgconfpanel.GetParams())
        
        ### testing if 'cancel' was pressed somewhere or 
        ### errors when converting from string to float while loading (None is returned)
        try:
            pressures, pressacc, scale, aver = self.GetExtraUserData(params['fromnames'], len(params['images']))
        except(TypeError): # catching type error
            return
        out, extra_out = features.locate(params)
        geometrydata, mesg = analysis.get_geometry(out)
        if mesg:
            self.OnError(mesg)
            return
        avergeom = analysis.averageImages(aver, **geometrydata)
        geometryframe = geometry.GeometryFrame(self, -1, avergeom)
#        geometryframe.Show()
        
        tensionframe = tension.TensionsFrame(self, -1, pressures, pressacc, scale, avergeom)
        tensionframe.Show()
        evt.Skip()
        
    def GetExtraUserData(self, pressfromfilenames, imgsNo):
        if not pressfromfilenames:
            fileDlg = wx.FileDialog(self, message="Choose a pressure protocol file",
                                    defaultDir = self.folder, style = wx.OPEN,
                                    wildcard = vampy.DATWILDCARD)
            if fileDlg.ShowModal() != wx.ID_OK:
                fileDlg.Destroy()
                return
            pressfilename = fileDlg.GetPath()
            fileDlg.Destroy()
        
        dlg = VampyOtherUserDataDialog(self, -1)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        stage, scale, pressacc = dlg.GetData()
        dlg.Destroy()
        if pressfromfilenames:
            pressures, aver, mesg = load.read_pressures_filenames(self.imgfilenames, stage)
        else:
            pressures, mesg = load.read_pressures_file(pressfilename, stage)
            if imgsNo % len(pressures) != 0:
                self.OnError('Number of images is not multiple of number of pressures!')
                return
            else:
                aver = imgsNo/len(pressures)#number of images to average within
        if mesg:
            self.OnError(mesg)
            return None
        return pressures, pressacc, scale, aver
    
    def OnExit(self, evt):
        self.Close()
        
    def OnSave(self, evt):
        intparams = self.imgconfpanel.GetCrop()
        stringparams = self.imgconfpanel.GetChoices()
        intparams.update(self.imgconfpanel.GetBools())
        intparams.update(self.imgpanel.GetSlidersPos())
        lines = []
        for key in stringparams.keys():
            lines.append('%s\t%s\n'%(key, stringparams[key]))
        for key in intparams.keys():
            line = '%s'%key
            if type(intparams[key]) in (int, bool):
                line += '\t%i'%intparams[key]
            else:
                line += len(intparams[key])*'\t%i'%intparams[key]
            line += '\n'
            lines.append(line)
            
        try:
            conffile = open(vampy.CFG_FILENAME, 'w')
        except IOError:
            wx.MessageBox('An error occurred while saving image info', 'Error')
            evt.Skip()
            return
        conffile.writelines(lines)
        conffile.close()
        wx.MessageBox('Image info saved', 'Info')
        evt.Skip()
        
    def OnReload(self, evt):
        """
        Explicitly reloads all imported modules from VAMPy projects.
        @param evt: incoming event from caller
        """
        reload(load)
        reload(analysis)
        reload(features)
        reload(util)
        reload(tension)
        reload(debug)
        reload(geometry)
        print '='*10+'Reloaded'+'='*10
    
    def OnDebugImage(self, evt):
        """
        Process only the current image
        TODO:process set of images?
        and display more additional information on it
        """
        imgNo = self.imgpanel.GetImgNo()
        if self.analysispanel.Validate():
            params = self.analysispanel.GetParams()
        else:
            return
        params.update(self.imgpanel.GetParams())
        params.update(self.imgconfpanel.GetParams())
        img = params['images'][imgNo-1]
        params['images'] = img.reshape(1, img.shape[0], img.shape[1])
        params['extra'] = True
        out, extra_out = features.locate(params)
        extra_out = extra_out[0]
        ImageDebugFrame = debug.ImageDebugFrame(self, -1, img, out, extra_out)
        ImageDebugFrame.Show()
        
    def OnAbout(self, evt):
        description = """Vesicle Aspiration with MicroPipettes made with Python"""
        info = wx.AboutDialogInfo()
        info.SetName('VAMPy')
        info.SetDescription(description)
        info.AddDeveloper('Pavlo Shchelokovskyy')
        wx.AboutBox(info)
        
    def OnHelp(self, evt):
        """
        TODO: write a (simple) online help
        @param evt:
        """
        self.OnAbout(evt)

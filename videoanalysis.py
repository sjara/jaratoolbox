#!/usr/bin/env python

'''
Functions and classes for video analysis.
'''

import numpy as np
import cv2
import matplotlib.pyplot as plt


class Video(object):
    '''
    Basic class to load a video.
    '''
    def __init__(self,filename):
        self.filename = filename
        self.cap = cv2.VideoCapture(self.filename)
        self.nFrames = int(self.cap.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT))
        self.frameSize = [int(self.cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)),
                          int(self.cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))]
        self.fps = self.cap.get(cv2.cv.CV_CAP_PROP_FPS) # Sometimes it is NaN
        self.frame = None
    def get_current_frame(self):
            return int(self.cap.get(cv2.cv.CV_CAP_PROP_POS_FRAMES))
    def release(self):
        self.cap.release()

        
class ColorRange(object):
    '''Define a color range'''
    def __init__(self,colorLimits):
        '''colorLimits is a list of two (B,R,G) lists defining extremes of a color'''
        self.colorLimits = colorLimits
        self.lower = np.array(colorLimits[0], dtype = "uint8")
        self.upper = np.array(colorLimits[1], dtype = "uint8")
    def __str__(self):
        return 'B:{0}-{1} R:{2}-{3} G:{4}-{5}'.format(self.lower[0],self.lower[1],self.lower[2],
                                                      self.upper[0],self.upper[1],self.upper[2])
    
    
class ColorTracker(Video):
    '''
    Subclass with methods for tracking mouse.
    '''
    def __init__(self,filename, colorLimits):
        '''
        Warning! OpenCV work in BRG format (not RGB). This class will work with BRG format.
        colorLimits is a list where each item is two (B,R,G) lists defining range of each color.
                   for example:
                   limitsR = [[40, 20, 150], [90, 70, 255]]
                   limitsG = [[70, 170, 110], [150, 255, 150]]
                   colorRange = [limitsR,limitsG]
        '''
        super(ColorTracker, self).__init__(filename)
        self.colorLimits = colorLimits
        self.nColors = len(self.colorLimits)
        self.colors = []
        self.set_color_ranges()
    def set_color_ranges(self):
        
    def process(self):
        
        pass

    
class ImageRegion(object):
    '''Define coordinates of a region'''
    def __init__(self,corners):
        '''Coords is a list of two (x,y) coordinates defining corners of a region.'''
        self.corners = corners
        self.hrange = [corners[0][0],corners[1][0]]
        self.vrange = [corners[0][1],corners[1][1]]
    def __str__(self):
        return 'h=[{0}:{1}] v=[{2}:{3}]'.format(self.hrange[0],self.hrange[1],self.vrange[0],self.vrange[1])

    
class StimDetector(Video):
    '''
    Subclass to find changes in average intensity. For example to find light on/off.
    '''
    def __init__(self, filename, coords):
        '''
        coords is a list where each item is a set of (x,y) coordinates defining corners of a region.
               for example: [ [[280, 70], [300, 80]], [[535, 65], [550, 75]] ]
        '''
        super(StimDetector, self).__init__(filename)
        self.coords = coords
        self.nRegions = len(self.coords)
        self.regions = []
        self.set_coords(self.coords) # This will set self.regions
        self.intensity = np.empty((self.nRegions,self.nFrames))
    def set_coords(self,coords):
        for indregion,thesecoords in enumerate(coords):
            self.regions.append(ImageRegion(thesecoords))
    def print_regions(self):
        for oneRegion in self.regions:
            print oneRegion
    def measure(self):
        '''Measure average intensity in regions'''
        for indf in range(self.nFrames):
            if indf%100==0:
                print 'Processing frame {0}/{1}'.format(self.get_current_frame(),self.nFrames)
            self.ret, self.frame = self.cap.read()
            gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            for indregion,oneregion in enumerate(self.regions):
                chunk = gray[slice(*oneregion.vrange), slice(*oneregion.hrange)]
                #1/0
                self.intensity[indregion,indf] = np.mean(chunk)
        
    
class DefineCoordinates(Video):
    '''
    Subclass to move through video and define a region.
    '''
    def __init__(self,filename,skip=10):
        super(DefineCoordinates, self).__init__(filename)
        plt.clf()
        self.coords = []
        self.skip = skip
        self.fig = plt.gcf()
        self.ret, self.frame = self.cap.read()
        self.show_frame()
        self.fig.show()
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.kpid = self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        print('Place mouse on image and press the RIGHT arrow to move forward,')
        print('then click on the image to print coordinates')
    def on_key_press(self, event):
        if event.key=='>' or event.key=='.' or event.key=='right':
            for ind in range(self.skip):
                self.ret, self.frame = self.cap.read()
            self.show_frame()
        '''
        if event.key=='<' or event.key==',' or event.key=='left':
            self.cap.set(cv2.cv.CV_CAP_PROP_POS_FRAMES,self.get_current_frame()-1);
            self.ret, self.frame = self.cap.read()
            self.show_frame()
        '''
    def on_click(self,event):
        '''Process mouse event for selecting coordinates on image'''
        theseCoords = [int(event.xdata),int(event.ydata)]
        print('x={0}, ydata={1}'.format(*theseCoords))
        self.coords.append(theseCoords)
    def show_frame(self):
        plt.imshow(self.frame)
        plt.title(self.get_current_frame())
        plt.draw()

if __name__ == "__main__":
    CASE=3
    if CASE==1:
        filename = '/data/videos/d1pi013/d1pi013_20160519-5.mkv'
        vid = ColorTracker(filename)
        vid.release()
    if CASE==2:
        filename = '/data/videos/d1pi013/d1pi013_20160519-5.mkv'
        vid = DefineCoordinates(filename)
    if CASE==3:
        filename = '/data/videos/d1pi013/d1pi013_20160519-5.mkv'
        coords = [ [[280, 70], [300, 80]], [[535, 65], [550, 75]] ]
        #coords = [[[279, 68], [297, 82]], [[534, 64], [550, 76]]]
        vid = StimDetector(filename,coords)
        vid.print_regions()
        vid.measure()
        plt.clf()
        plt.plot(vid.intensity.T)
    if CASE==4:
        filename = '/data/videos/d1pi013/d1pi013_20160519-5.mkv'
        limitsR = [[40, 20, 150],
                   [90, 70, 255]]
        limitsG = [[70, 170, 110],
                   [150, 255, 150]]
        colorRange = [limitsR,limitsG]
        

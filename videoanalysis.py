#!/usr/bin/env python

'''
Functions and classes for video analysis.
'''

import numpy as np
import cv2
import matplotlib.pyplot as plt
from jaratoolbox import extrafuncs


class Video(object):
    '''
    Basic class to load a video.
    '''
    def __init__(self,filename):
        self.filename = filename
        self.cap = cv2.VideoCapture(self.filename)
        # For some reason, nFrames is not always accurate.
        self.nFrames = int(self.cap.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT))
        self.frameSize = [int(self.cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)),
                          int(self.cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))]
        self.fps = self.cap.get(cv2.cv.CV_CAP_PROP_FPS) # Sometimes it is NaN
        self.frame = None
    def read(self):
        self.ret, self.frame = self.cap.read()
        currentFrame = int(self.cap.get(cv2.cv.CV_CAP_PROP_POS_FRAMES))
        if not self.ret:
            # If it returns False, it has reached the end of the file.
            # and nFrames needs to be fixed.
            self.nFrames = currentFrame
            print 'WARNING: reached end of video file.'
        '''
        if not self.ret:
            currentFrame = int(self.cap.get(cv2.cv.CV_CAP_PROP_POS_FRAMES))
            print 'WARNING: Could not read frame {0}. I will rewind and retry.'.format(currentFrame)
            self.cap.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, currentFrame)
            self.ret, self.frame = self.cap.read() # Read previous frame
            #self.ret, self.frame = self.cap.read() # Read failed frame
            if not self.ret:
                #raise IOError('Could not read frame.')
                print 'Could not read frame. Will replace with blank frame'
                blankFrame = np.zeros([self.frameSize[1],self.frameSize[0],3],dtype=np.uint8)
                self.frame = blankFrame  # If it cannot read frame, make it blank
        '''
        return (self.ret, self.frame)
    def get_current_frame(self):
            return int(self.cap.get(cv2.cv.CV_CAP_PROP_POS_FRAMES))
    def show_frame(self, frameIndex):
        '''Note that this is very inefficient as it load the video up to this frame
           This is necessary to load all pixels, because of the compression strategy
           and not knowing where the key frame is.
        '''
        for indf in range(frameIndex):
            self.ret, self.frame = self.cap.read()
        frameRGB = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        plt.imshow(frameRGB)
        plt.title('Frame: {}'.format(frameIndex))
        plt.show()
        return frameRGB
    def release(self):
        self.cap.release()

        
class ColorRange(object):
    '''Define a color range'''
    def __init__(self,colorLimits):
        '''colorLimits is a list of two 3-element lists defining extremes of a color
        For OpenCV, these can be BGR or HSV spaces.
        '''
        self.colorLimits = colorLimits
        self.lower = np.array(colorLimits[0], dtype = "uint8")
        self.upper = np.array(colorLimits[1], dtype = "uint8")
    def __str__(self):
        return '{0}-{1} \t {2}-{3} \t {4}-{5}'.format(self.lower[0],self.upper[0],
                                                      self.lower[1],self.upper[1],
                                                      self.lower[2],self.upper[2])
    

def OLD_massCenter(img, minPixels=1):
    '''Find center of mass of binary image
    http://docs.opencv.org/2.4/modules/imgproc/doc/structural_analysis_and_shape_descriptors.html

    minPixels: if image has less than minPixels on, return (NaN,NaN)
    '''
    #if np.any(img):
    if np.sum(img>0)>=minPixels:
        imgMoments = cv2.moments(img)
        xbar = imgMoments['m10']/imgMoments['m00']
        ybar = imgMoments['m01']/imgMoments['m00']
        return [xbar,ybar]
    else:
        return [np.nan,np.nan]

def mass_center(img, minPixels=1):
    '''Find center of mass of binary image or contours.
    http://docs.opencv.org/2.4/modules/imgproc/doc/structural_analysis_and_shape_descriptors.html
    '''
    imgMoments = cv2.moments(img)
    xbar = imgMoments['m10']/imgMoments['m00']
    ybar = imgMoments['m01']/imgMoments['m00']
    return [xbar,ybar]

'''
def find_largest_contour(self,contours):
    contoursArea = []
    for cnt in contours:
        contoursArea.append(cv2.contourArea(cnt))
'''

class ColorTracker(Video):
    '''
    Subclass with methods for tracking mouse.
    '''
    def __init__(self,filename, colorLimits):
        '''
        This class works best with colors in HSV space.
        In OpenCV HSV ranges are (0-179, 0-255, 0-255)
        
        Use the following to figure out the H value for a BRG color:
        >> cv2.cvtColor(np.uint8([[[0,255,0]]]),cv2.COLOR_BGR2HSV)
        Note that OpenCV workss in BGR format (not RGB).

        colorLimits is a list where each item is two (H,S,V) lists defining range of each color.
        For example:
            hsvLimitsG  = [[45,  70,  70],
                           [75, 255, 255]]
            hsvLimitsR2 = [[170,  70,  70],
                           [179, 255, 255]]
            colorLimits = [hsvLimitsG,hsvLimitsR2]
        '''
        super(ColorTracker, self).__init__(filename)
        self.colorLimits = colorLimits
        self.nColors = len(self.colorLimits)
        self.colorRanges = []
        self.set_color_ranges(self.colorLimits)  # This defines self.colorRanges
        self.colorCenter = np.empty((self.nColors,2,self.nFrames))
        self.labels = {'colorCenter':['colors','coord','frames']}
        self.missed = np.empty((self.nColors,self.nFrames),dtype=bool) # When a color was not present
    def set_color_ranges(self, colorLimits):
        for theseColorLims in colorLimits:
            self.colorRanges.append(ColorRange(theseColorLims))
    def print_colors(self):
        for oneColorRange in self.colorRanges:
            print oneColorRange
    '''
    def OLD_process(self, minPixels=6, lastFrame=None, verboseInterval=100, showImage=False):
        colorMask = np.empty((self.nColors,self.frameSize[1],self.frameSize[0]),dtype=np.uint8)
        colorCenter = np.empty((self.nColors,2,self.nFrames))
        zeroFrame = np.zeros([self.frameSize[1],self.frameSize[0]],dtype=np.uint8)
        if lastFrame is None:
            lastFrame = self.nFrames
        for indf in range(lastFrame):
            if indf%verboseInterval==0:
                print 'Processing frame {0}/{1}'.format(self.get_current_frame(),self.nFrames)
            self.ret, self.frame = self.cap.read()
            for indColor,oneColRange in enumerate(self.colorRanges):
                colorMask[indColor,:,:] = cv2.inRange(self.frame, oneColRange.lower, oneColRange.upper)
                colorCenter[indColor,:,indf] = massCenter(colorMask[indColor,:,:],minPixels)
            if showImage:
                newimg = np.dstack((colorMask,zeroFrame))
                plt.imshow(newimg)
                plt.draw()
                #plt.waitforbuttonpress()
        self.colorCenter = colorCenter
        for indColor,oneColRange in enumerate(self.colorRanges):
            self.missed[indColor,:] = np.isnan(self.colorCenter[indColor,0,:])
        return colorCenter
    '''
    def process(self, minArea=25, lastFrame=None, verboseInterval=100, showImage=False):
        colorMask = np.empty((self.nColors,self.frameSize[1],self.frameSize[0]),dtype=np.uint8)
        # I need to initalize with zeros, because nFrames is not always accurate and we
        # may attempt to read inexistent frames.
        colorCenter = np.zeros((self.nColors,2,self.nFrames))
        zeroFrame = np.zeros([self.frameSize[1],self.frameSize[0]],dtype=np.uint8)
        if lastFrame is None:
            lastFrame = self.nFrames
        for indf in range(lastFrame):
            if indf%verboseInterval==0:
                print 'Processing frame {0}/{1}'.format(self.get_current_frame(),self.nFrames)
            self.ret, self.frame = self.cap.read()
            if not self.ret:
                break
            '''
            if not self.ret:
                blankFrame = np.zeros([self.frameSize[1],self.frameSize[0],3],dtype=np.uint8)
                self.frame = blankFrame  # If it cannot read frame, make it blank
            '''
            hsvImg = cv2.cvtColor(self.frame,cv2.COLOR_BGR2HSV)
            for indColor,oneColRange in enumerate(self.colorRanges):
                colorMask[indColor,:,:] = cv2.inRange(hsvImg, oneColRange.lower, oneColRange.upper)
                # -- Note that findCountours updates converts colorMask to contours --
                contours, hierarchy = cv2.findContours(colorMask[indColor,:,:], cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                if len(contours)>0:
                    contoursArea = [cv2.contourArea(cnt) for cnt in contours]
                    indLargestContour = np.argmax(contoursArea)
                    if contoursArea[indLargestContour]>minArea:
                        colorCenter[indColor,:,indf] = mass_center(contours[indLargestContour])
                    else:
                        colorCenter[indColor,:,indf] = [np.nan,np.nan]
                else:
                    colorCenter[indColor,:,indf] = [np.nan,np.nan]
                #colorCenter[indColor,:,indf] = massCenter(colorMask[indColor,:,:],minPixels)
            if indf%verboseInterval==0:
                if showImage:
                    plt.clf()
                    ax1 = plt.subplot(1,2,1)
                    plt.imshow(self.frame)
                    ax2 = plt.subplot(1,2,2, sharex=ax1, sharey=ax1)
                    combinedImg = np.zeros((self.frameSize[1],self.frameSize[0],3), 'uint8')
                    for ind in [0,1]:
                        combinedImg[:,:,ind] = 255*(colorMask[ind,:,:]>1)
                    plt.imshow(combinedImg)  #cmap='gray'
                    plt.title('Color: {}'.format(1))
                    plt.show()
                    plt.waitforbuttonpress()
        self.colorCenter = colorCenter
        for indColor,oneColRange in enumerate(self.colorRanges):
            self.missed[indColor,:] = np.isnan(self.colorCenter[indColor,0,:])
        return colorCenter
    def interpolate(self):
        '''Fill in NaN with interpolated values'''
        for indColor,oneColRange in enumerate(self.colorRanges):
            for coord in range(2):
                self.colorCenter[indColor,coord,:] = \
                    extrafuncs.interpolate_nan(self.colorCenter[indColor,coord,:])
        return self.colorCenter
    def OLD_show_mask(self,frameIndex,colorIndex):
        ax1 = plt.subplot(1,2,1)
        frame = self.show_frame(frameIndex)
        oneColRange = self.colorRanges[colorIndex]
        colorMask = cv2.inRange(self.frame, oneColRange.lower, oneColRange.upper)
        ax2 = plt.subplot(1,2,2, sharex=ax1, sharey=ax1)
        plt.imshow(colorMask,cmap='gray')
        plt.title('Color: {}'.format(colorIndex))
        plt.show()
        return colorMask
    def show_mask(self,frameIndex):
        ax1 = plt.subplot(1,2,1)
        frame = self.show_frame(frameIndex)
        hsvImg = cv2.cvtColor(self.frame,cv2.COLOR_BGR2HSV)
        colorMask = np.empty((self.nColors,self.frameSize[1],self.frameSize[0]),dtype=np.uint8)
        for indColor,oneColRange in enumerate(self.colorRanges):
                colorMask[indColor,:,:] = cv2.inRange(hsvImg, oneColRange.lower, oneColRange.upper)
        ax2 = plt.subplot(1,2,2, sharex=ax1, sharey=ax1)
        combinedImg = np.zeros((self.frameSize[1],self.frameSize[0],3), 'uint8')
        for ind in [0,1]:
            combinedImg[:,:,ind] = 255*(colorMask[ind,:,:]>1)
        plt.imshow(combinedImg)
        plt.title('Outlines')
        plt.show()
        return colorMask
       
    
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
        #self.intensity = np.empty((self.nRegions,self.nFrames))
        self.intensity = np.zeros((self.nRegions,self.nFrames))
    def set_coords(self,coords):
        for theseCoords in coords:
            self.regions.append(ImageRegion(theseCoords))
    def print_regions(self):
        for oneRegion in self.regions:
            print oneRegion
    def measure(self, verboseInterval=100):
        '''Measure average intensity in regions'''
        for indf in range(self.nFrames):
            if indf%verboseInterval==0:
                print 'Processing frame {0}/{1}'.format(self.get_current_frame(),self.nFrames)
            self.ret, self.frame = self.read()
            if not self.ret:
                break
            '''
            self.ret, self.frame = self.cap.read()
            if not self.ret:
                blankFrame = np.zeros([self.frameSize[1],self.frameSize[0],3],dtype=np.uint8)
                self.frame = blankFrame  # If it cannot read frame, make it blank
            '''
            gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            for indregion,oneregion in enumerate(self.regions):
                chunk = gray[slice(*oneregion.vrange), slice(*oneregion.hrange)]
                self.intensity[indregion,indf] = np.mean(chunk)
        return self.intensity
    
    
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
    CASE=6
    if CASE==1:
        filename = '/data/videos/d1pi013/d1pi013_20160519-5.mkv'
        vid = Video(filename)
        vid.show_frame(367)  # 397
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
        intensity = vid.measure()
        plt.clf()
        plt.plot(intensity.T)
        plt.show()
        #np.savez('/var/tmp/stimtrack.npz',stimIntensity=vid.intensity)
    if CASE==4:
        filename = '/data/videos/d1pi013/d1pi013_20160519-5.mkv'
        limitsG = [[40, 20, 150],
                   [90, 70, 255]]
        limitsR = [[70, 170, 110],
                   [150, 255, 150]]
        colorLimits = [limitsR,limitsG]
        vid = ColorTracker(filename,colorLimits)
        vid.print_colors()
        colorCenter = vid.process(showImage=False)
        plt.clf()
        plt.hold(1)
        plt.xlim([0,800]); plt.ylim([0,600])
        for indc in range(2):
            plt.plot(colorCenter[indc,0,:],colorCenter[ind,1,:],'.-')
            plt.draw()
        plt.show()
        #np.savez('/var/tmp/colortrack.npz',colorCenter=colorCenter)
    if CASE==5:
        colortrack = np.load('/var/tmp/colortrack.npz')
        colorCenter = colortrack['colorCenter']
        stimtrack = np.load('/var/tmp/stimtrack.npz')
        stimIntensity = stimtrack['stimIntensity']
        plt.clf()
        plt.hold(1)
        if 0:  # Plot detected position in 2D
            plt.xlim([0,800]); plt.ylim([0,600])
            plt.gca().invert_yaxis()
            for indc in range(2):
                plt.plot(colorCenter[indc,0,:],colorCenter[indc,1,:],'.-')
                plt.draw()
        else: # Plot detected coords in 1D
            for indc in range(2):
                ax1 = plt.subplot(3,1,1)
                plt.plot(colorCenter[indc,0,:],'.-')
                ax2 = plt.subplot(3,1,2,sharex=ax1)
                plt.plot(colorCenter[indc,1,:],'.-')
                ax3 = plt.subplot(3,1,3,sharex=ax1)
                plt.plot(stimIntensity.T,'.-')
            plt.draw()
        plt.show()
    if CASE==6:
        filename = '/data/videos/d1pi013/d1pi013_20160519-5.mkv'
        limitsG = [[40, 20, 150],
                   [90, 70, 255]]
        limitsR = [[70, 170, 110],
                   [150, 255, 150]]
        colorLimits = [limitsR,limitsG]
        vid = ColorTracker(filename,colorLimits)
        plt.clf()
        mask = vid.show_mask(398,1)
        #plt.axis((534.11450469000238, 601.4675131548845, 434.81957390146465, 374.89946737683084))
        '''
        plt.subplot(1,2,1)
        frame = vid.show_frame(367)  # 397
        oneColRange = vid.colorRanges[0]
        colorMask = cv2.inRange(frame, oneColRange.lower, oneColRange.upper)
        plt.subplot(1,2,2)
        plt.imshow(colorMask)
        plt.show()
        ###Make sure no new figure is created and plot mask
        '''

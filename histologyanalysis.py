'''
Tools for analyzing anatomical/histological data.
'''

'''
==  TO DO ==
* Fix hardcoded transform! (it should either be entered as a param, or just have more squares in grid)
* Maybe change the dir structure of images to have stackLabel_R and stackLabel_L as opposed to deeper directory levels.
* There should be two separate objects. One that holds the grid, one that provides a graphical interface.

'''

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import os
import json
from jaratoolbox import settings

GRIDCOLOR = [0,0.5,0.5]

def define_grid(corners, nRows=3, nCols=2):
    '''
    Find coordinates of corners for each square in a grid.
    '''
    topleft,bottomright = corners
    xvals = np.sort(np.linspace(topleft[0],bottomright[0],nCols+1))
    yvals = np.sort(np.linspace(topleft[1],bottomright[1],nRows+1))
    return (xvals,yvals)

def draw_grid(corners,nRows=3,nCols=2):
    '''
    Draw a grid of nRows and nCols starting at the coordinates specified in 'corners'.
    '''
    (xvals,yvals) = define_grid(corners,nRows,nCols)
    holdStatus = plt.ishold()
    plt.hold(True)
    plt.autoscale(False)
    for yval in yvals:
        plt.plot(xvals[[0,-1]],[yval,yval],color=GRIDCOLOR)
    for xval in xvals:
        plt.plot([xval,xval],yvals[[0,-1]],color=GRIDCOLOR)
    plt.hold(holdStatus)
    plt.draw()

class OverlayGrid(object):

    def __init__(self,nRows=3,nCols=2):
        '''
        This class allows defining a grid over an image using the mouse,
        and show that grid overlaid on another image.
        '''
        self.image = np.array([]) #mpimg.imread(imgfile)
        self.corners = []
        self.coords = []
        self.fig = None
        self.cid = None  # Connection ID for mouse clicks
        self.nRows = nRows
        self.nCols = nCols
        self.sliceNumber = []
        self.maxSliceInd = []
        self.stack = []
        self.kpid = None
        self.cid = None

    def set_shape(self,nRows,nCols):
        self.nRows = nRows
        self.nCols = nCols

    def show_image(self,img):
        self.fig = plt.gcf()
        self.fig.clf()
	cLims = [0,255]  # FIXME: color values are hard-coded
        plt.imshow(img, cmap = 'gray',vmin=cLims[0], vmax=cLims[1])
        plt.gca().set_aspect('equal', 'box')
        #plt.axis('equal')
        plt.show()

    def onclick(self,event):
        #ix, iy = event.xdata, event.ydata
        print '({0},{1})'.format(int(event.xdata), int(event.ydata))
        #global corners
        self.corners.append((event.xdata, event.ydata))
        if len(self.corners) == 2:
            self.fig.canvas.mpl_disconnect(self.cid)
            self.set_grid(self.corners)
            draw_grid(self.corners, nRows = self.nRows, nCols = self.nCols)
            print 'Done. Now you can apply this grid to another image using apply_grid()'
            print 'Press enter to continue'

    def on_key_press(self, event):
        '''
        Method to listen for keypresses and change the slice
        '''
        if event.key=='<' or event.key==',' or event.key=='left':
            if self.sliceNumber>0:
                self.sliceNumber-=1
            else:
                self.sliceNumber=self.maxSliceInd
            self.apply_grid(self.stack[self.sliceNumber])
            self.title_stack_slice()
        elif event.key=='>' or event.key=='.' or event.key=='right':
            if self.sliceNumber<self.maxSliceInd:
                self.sliceNumber+=1
            else:
                self.sliceNumber=0
            self.apply_grid(self.stack[self.sliceNumber])
            self.title_stack_slice()

    def title_stack_slice(self):
        plt.title("Slice {}\nPress < or > to navigate".format(self.sliceNumber))
        
    def enter_grid(self,imgfile):
        self.corners = []
        self.image = mpimg.imread(imgfile)
        self.fig = plt.gcf()
        self.show_image(self.image)
        print 'Click two points to define corners of grid.'
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        # FIXME: find if waiting for click can block execution of the rest.

    def set_grid(self,corners):
        self.corners = corners
        self.coords = define_grid(corners, self.nRows, self.nCols)

    def apply_grid(self,imgfile):
        self.image = mpimg.imread(imgfile)
        self.show_image(self.image)
        draw_grid(self.corners, self.nRows, self.nCols)

    def apply_to_stack(self, fnList):
        self.fig = plt.gcf()
        
        #Disconnect the event listener if one exists
        if self.kpid:
            self.fig.canvas.mpl_disconnect(self.kpid)
        
        self.stack = fnList
        self.maxSliceInd = len(fnList)-1
        self.sliceNumber = 0
        self.apply_grid(self.stack[self.sliceNumber])
        #plt.gca().set_aspect('equal', 'box')
        self.title_stack_slice()
        
        #Connect the event listener
        self.kpid = self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)

    def load_corners(self, filename):
        with open(filename, 'r') as f:
            self.corners = json.load(f)
            
    def save_corners(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.corners, f)

    def quantify(self,image):
        imShape = image.shape
        assert len(imShape)<3
        xvals,yvals = self.coords
        measured = np.empty((self.nRows,self.nCols))
        for indr in range(self.nRows):
            rowCoords = yvals[indr:indr+2].astype(int)
            for indc in range(self.nCols):
                colCoords = xvals[indc:indc+2].astype(int)
                imChunk = image[rowCoords[0]:rowCoords[1],
                                colCoords[0]:colCoords[1]]
                measured[indr,indc] = imChunk.mean()
        return measured

    def load_stack(self,fnList):
        stackList = []
        for imgFile in fnList:
            image = mpimg.imread(imgFile)
            if len(image.shape)>2:
                image = image[:,:,0]   # FIXME: I'm taking only first channel
            stackList.append(image)
        return np.array(stackList)

    def quantify_stack(self,imgStack):
        '''
        ARGS:
            stack: (nImages, height, width)
        '''
        nImages = imgStack.shape[0]
        measuredStack = np.empty((nImages, self.nRows, self.nCols))
        for indImg, oneImg in enumerate(imgStack):
            measuredStack[indImg] = self.quantify(oneImg)
        return measuredStack


# --------------------------------------------------------------------------------------------------


class BrainGrid(OverlayGrid):
    '''
    FIXME: After update, the docstrings are all wrong
    '''

    def __init__(self, animalName, stackLabel, side='', nRows = 3, nCols = 2, processedDirName = 'registered'):
        super(BrainGrid, self).__init__(nRows, nCols)
        self.animalName = animalName
        self.stackLabel = stackLabel
        self.side = side
        self.processedDirName = processedDirName

    def change_stack(self, stackLabel, side):
        self.stackLabel = stackLabel
        self.side = side

    def dir_structure(self, channelLabel):
        return os.path.join(settings.HISTOLOGY_PATH, self.animalName, self.stackLabel, self.side, self.processedDirName, channelLabel)

    def coord_file(self, coordFileName=None):
        '''
        Returns the full path to the coords file for a given animal, magnification, and grid side
        '''
        coordDir = os.path.join(settings.HISTOLOGY_PATH, self.animalName, 'coords')
        if self.side == '':
            sideInput = raw_input("Enter the side if necessary: ")
            coordFile = os.path.join(coordDir, 'coords_{}{}.json'.format(self.stackLabel, sideInput))
        else: 
            coordFile = os.path.join(coordDir, 'coords_{}{}.json'.format(self.stackLabel, self.side))
        #if not coordFileName: #FIXME: This was here to allow people to enter their own coord file name but was breaking things
            #coordFile = os.path.join(coordDir, 'coords_{}{}.json'.format(self.stackLabel, self.side))
        #else:
            #coordFile = os.path.join(coordDir, '{}.json'.format(coordFileName))
        return coordFile, coordDir

    def reference_slice_filename(self, refSliceInd):
        '''
        Return the full file path for a specified slice number
        
        This method is used to get the file path for a reference slice that can be used to define
        the grid coordinates if none exist. Must input the index of the reference slice (starts from zero). 
        This makes sense because the registered images are also numbered starting from zero. 
        
        Args:
            refSliceInd (int): The index of the slice to return. Starts from zero. 
        
        Returns: 
            refSlicePath (str): The full file path for the requested slice
        
        Example:
            bg = BrainGrid('anat027')  # Initialize a BrainGrid instance for a mouse
            refSlice = bg.reference_slice_filename(33)
            bg.enter_grid(refslice)   # Define grid via a graphical interface
        '''

        stack = self.filename_stack('b')
        refSlicePath = stack[refSliceInd]
        return refSlicePath

    def filename_stack(self, channelLabel):
        '''
        Return a list of image file paths to use as an image stack
        
        This method returns a list of image paths for one magnification and channel, 
        and for the 2.5x images, for one side. This stack can then be passed to the 
        apply_to_stack method, which will plot the grid on top of the stack images
        and allow the user to flip through the stack. 
        
        Args:
            channelLabel (str): The channel to use. Must be either 'r', 'g', or 'b'
        
        Returns: 
            stack (list): A list of file path strings for each of the images in the stack
        
        Example:
            bg = BrainGrid('anat027')  # Initialize a BrainGrid instance for a mouse
            stack = bg.filename_stack('1_25x', 'g')  # Green channel
            bg.apply_to_stack(stack) # Set the grid from the reference image onto all images of stack
        '''
        directory = self.dir_structure(channelLabel)
        stack = [os.path.join(directory, f) for f in sorted(os.listdir(directory)) if os.path.isfile(os.path.join(directory, f))]
        return stack
        
    def define_grid(self, refSliceInd):
        '''
        Define the grid coordinates by clicking on a reference slice
        
        This method is a wrapper that gets the file path for a reference image and 
        uses that image to set the grid initially. Use this method the first time
        you are analyzing a particular magnification/side, or if you need to change the 
        grid coordinates. This method always uses the brightfield channel
        
        Args:
            refSliceInd (int): The index of the slice to return. Starts from zero. 
        '''
        self.enter_grid(self.reference_slice_filename(refSliceInd))
        
    def convert_grid_coords(self):
        coordArray = np.array(self.corners)
        transform = np.array([ [348, -374], [146, -419] ]) # Hardcoded, determined empirically

        topright = coordArray[coordArray[:,0].argmax(), :] #Greater X
        bottomleft = coordArray[coordArray[:,1].argmax(), :] #Greater Y

        if self.side == 'left':
            topright = topright - transform[0, :]
            bottomleft = bottomleft - transform[1, :]
        elif self.side == 'right':
            pass #FIXME: implement this. Opposite sign for X? X should mirror but Y should not
    
        self.corners = np.array([topright, bottomleft])
        #self.draw_grid()
       
    def stack_grid(self, channelLabel):
        '''
        Apply the grid coordinates to all of the images for one condition
        
        This method is a wrapper that applys the current grid to all of the images
        for one magnification and channel, and for one side if working with the 2.5x
        images. Use this method either after initially defining the grid or after loading
        a grid from a file. 
        
        Args:
            magnification (str): The magnification level of the images to use. Must be either '1_25x' or '2_5x'
            channel (str): The channel to use. Must be either 'r', 'g', or 'b'
            side (str): Only required if magnification='2_5x'. Must be either 'left' or 'right'
        
        Example:
            #Initialize a BrainGrid instance for a mouse
            bg = BrainGrid('anat027')
        
            #Define a grid for the 1.25x images using reference slice 0033
            bg.define_grid('1_25x', 33)
        
            #Apply the grid to all of the green channel images
            bg.stack_grid('1_25x', 'g')

            #Apply the grid to all of the red channel images
            bg.stack_grid('1_25x', 'r')
        '''
        self.apply_to_stack(self.filename_stack(channelLabel))
        
    def save_mouse_coords(self, coordFileName=None):
        '''
        Save the coordinates for one magnification, one side
        
        This method saves the coords stored in self.corners as an ASCII file using the json library. 
        These coords can later be used if the experimenter wants to re-analyze some data without
        defining a new set of coords. 
        
        Args:
            magnification (str): The magnification level of the images to use. Must be either '1_25x' or '2_5x'
            side (str): Only required if magnification='2_5x'. Must be either 'left' or 'right'
        
        Example:
            #Initialize a BrainGrid instance for a mouse
            bg = BrainGrid('anat027')

            #The 1.25x images, green channel, slice 0033
            refSlice = bg.reference_slice_filename('1_25x', 'g', 33)
        
            #Use to set the grid on the left side of the reference image
            bg.set_grid(refslice)
        
            #Save the coords file with the side that you put the grid on
            bg.save_mouse_coords('1_25x', 'left')
        '''
        coordFile, coordDir = self.coord_file(coordFileName)
        if not os.path.exists(coordDir):
            os.makedirs(coordDir)
        self.save_coords(coordFile)
        
    def load_mouse_coords(self, coordFileName=None):
        '''
        Load the coordinates for one magnification, one side
        
        This method loads the coords from an ASCII file using the json library, and uses them
        to set the value of self.corners. These coords can later be used if the experimenter wants
        to re-analyze some data without defining a new set of coords. 
        
        Args:
            magnification (str): The magnification level of the images to use. Must be either '1_25x' or '2_5x'
            side (str): Only required if magnification='2_5x'. Must be either 'left' or 'right'
        
        Example:
            #Initialize a BrainGrid instance for a mouse
            bg = BrainGrid('anat027')

            #Load the left side grid coords for this mouse, 1.25x magnification images
            bg.load_mouse_coords('1_25x', 'left')
        
            #Apply the loaded coords to all of the green channel images
            bg.stack_grid('1_25x', 'g')
        '''
        coordFile, coordDir = self.coord_file(coordFileName)
        if not os.path.exists(coordFile):
            print "No coords for this set of images"
            pass
        self.load_coords(coordFile)
        

#if __name__=='__main__':
   # imgfile = '/mnt/jarahubdata/histology/anat002_MGB_jpg/b4-C1-01tdT_mirror_correct.jpg'
   # ogrid = OverlayGrid(nRows=3,nCols=2)
   # ogrid.set_grid(imgfile)
    

'''
imgfile2 = '/data/brainmix_data/test043_TL/p1-D4-01b.jpg'
ogrid.apply_grid(imgfile2)
'''

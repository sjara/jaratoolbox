'''
Tools for analyzing anatomical/histological data.
'''

'''
==  TO DO ==
* Fix hardcoded transform! (it should either be entered as a param, or just have more squares in grid)
* Maybe change the dir structure of images to have stackLabel_R and stackLabel_L as opposed to deeper directory levels.
* There should be two separate objects. One that holds the grid, one that provides a graphical interface.

'''

import os
import pandas
import json
import re
import PIL
import xml.etree.ElementTree as ETree
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from jaratoolbox import settings
try:
    import nrrd
except:
    print('Warning! Some methods require the module "nrrd", but it is not installed.')

    
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
        self.corners = []
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

    def enter_grid_corners(self,imgfile):
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
        xvals,yvals = self.corners
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

    def corners_file(self):
        '''
        Returns the full path to the corners file for a given animal, magnification, and grid side
        '''
        cornersDir = os.path.join(settings.HISTOLOGY_PATH, self.animalName, 'gridcorners')
        if self.side == '':
            sideInput = raw_input("Enter the side if necessary: ")
            cornersFile = os.path.join(cornersDir, 'corners_{}{}.json'.format(self.stackLabel, sideInput))
        else:
            cornersFile = os.path.join(cornersDir, 'corners_{}{}.json'.format(self.stackLabel, self.side))
        return cornersFile, cornersDir

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

    def choose_corners(self, refSliceInd):
        '''
        Define the grid coordinates by clicking on a reference slice

        This method is a wrapper that gets the file path for a reference image and
        uses that image to set the grid initially. Use this method the first time
        you are analyzing a particular magnification/side, or if you need to change the
        grid coordinates. This method always uses the brightfield channel

        Args:
            refSliceInd (int): The index of the slice to return. Starts from zero.
        '''
        self.enter_grid_corners(self.reference_slice_filename(refSliceInd))

    def convert_grid_corners(self):
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

    def overlay_grid_on_stack(self, channelLabel):
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

        '''
        self.apply_to_stack(self.filename_stack(channelLabel))

    def save_mouse_corners(self):
        '''
        Save the coordinates for one magnification, one side

        This method saves the corners stored in self.corners as an ASCII file using the json library.
        These corners can later be used if the experimenter wants to re-analyze some data without
        defining a new set of corners.

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

            #Save the corners file with the side that you put the grid on
            bg.save_mouse_corners('1_25x', 'left')
        '''
        cornersFile, cornersDir = self.corners_file()
        if not os.path.exists(cornersDir):
            os.makedirs(cornersDir)
        self.save_corners(cornersFile)

    def load_mouse_corners(self):
        '''
        Load the coordinates for one magnification, one side

        This method loads the corners from an ASCII file using the json library, and uses them
        to set the value of self.corners. These corners can later be used if the experimenter wants
        to re-analyze some data without defining a new set of corners.

        Args:
            magnification (str): The magnification level of the images to use. Must be either '1_25x' or '2_5x'
            side (str): Only required if magnification='2_5x'. Must be either 'left' or 'right'

        Example:
            #Initialize a BrainGrid instance for a mouse
            bg = BrainGrid('anat027')

            #Load the left side grid corners for this mouse, 1.25x magnification images
            bg.load_mouse_corners('1_25x', 'left')

            #Apply the loaded corners to all of the green channel images
            bg.stack_grid('1_25x', 'g')
        '''
        cornersFile, cornersDir = self.corners_file()
        if not os.path.exists(cornersFile):
            print "No corners for this set of images"
            pass
        self.load_corners(cornersFile)

class AllenAnnotation(object):
    def __init__(self):
        self.structureGraphFn =  os.path.join(settings.ALLEN_ATLAS_DIR, 'structure_graph.json')
        jsonData = open(self.structureGraphFn).read()
        data = json.loads(jsonData)
        self.structureGraph = data['msg']
        structureList = []
        self.structureDF = self.process_structure_graph(self.structureGraph)
        self.annotationFn =  os.path.join(settings.ALLEN_ATLAS_DIR, 'coronal_annotation_25.nrrd')
        annotationData = nrrd.read(self.annotationFn)
        self.annotationVol = annotationData[0]
    def process_structure_graph(self, structureGraph):
        structureList = []
        def process_structure_graph_internal(structureGraph):
            for structure in structureGraph:
                #Pop the children out to deal with them recursively
                children = structure.pop('children', None)
                # Add the structure info to the dataframe
                structureList.append(pandas.Series(structure))
                #Deal with the children
                process_structure_graph_internal(children)
        process_structure_graph_internal(structureGraph)
        df = pandas.DataFrame(structureList)
        return df
    def get_structure(self, coords):
        #coords needs to be a 3-TUPLE (x, y, z)
        structID = int(self.annotationVol[coords])
        if structID!=0:
            name = self.structureDF.query('id == @structID')['name'].values[0]
        else:
            name = 'Outside the brain'
        return structID, name
    def get_name(self, structID):
            name = self.structureDF.query('id==@structID')['name'].item()
            return structID, name
    def trace_parents(self, structID):
        #TODO: I don't know if the nested function approach will work in an obj
        '''Trace the lineage of a region back to the root of the structure graph'''
        parentTrace = []
        parentNames = []
        def trace_internal(structID):
            parentID = self.structureDF.query('id==@structID')['parent_structure_id']
            if not pandas.isnull(parentID.values[0]):
                parentID = int(parentID)
                parentTrace.append(parentID)
                parentNames.append(self.structureDF.query('id==@parentID')['name'].item())
                trace_internal(parentID)
        trace_internal(structID)
        return parentTrace, parentNames
    def get_structure_many_xy(self, xyArr, zSlice):
        names = []
        structIDs = []
        for indCell in range(xyArr.shape[1]):
            coords = (xyArr[0, indCell].astype(int), xyArr[1, indCell].astype(int), zSlice.astype(int))
            structID, name = self.get_structure(coords)
            names.append(name)
            structIDs.append(structID)
        return structIDs, names

class AllenAtlas(object):
    def __init__(self):
        atlasPath = os.path.join(settings.ALLEN_ATLAS_DIR, 'coronal_average_template_25.nrrd')
        atlasData = nrrd.read(atlasPath)
        self.atlas = atlasData[0]
        self.maxSlice = np.shape(self.atlas)[2]-1
        self.sliceNum=0
        self.fig=plt.figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.hold(True)
        self.show_slice(self.sliceNum)
        self.mpid=self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.mouseClickData=[]
        #Start the key press handler
        self.kpid = self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        #show the plot
        self.fig.show()
    def on_click(self, event):
        '''
        Method to record mouse clicks in the mouseClickData attribute
        and plot the points on the current axes
        '''
        self.mouseClickData.append([event.xdata, event.ydata])
        ymin, ymax = self.ax.get_ylim()
        xmin, xmax = self.ax.get_xlim()
        self.ax.plot(event.xdata, event.ydata, 'r+')
        print "[{}, {}, {}]".format(int(event.xdata), int(event.ydata), int(self.sliceNum))
        self.ax.set_ylim([ymin, ymax])
        self.ax.set_xlim([xmin, xmax])
        self.fig.canvas.draw()
    def on_key_press(self, event):
        '''
        Method to listen for keypresses and take action
        '''
        #Functions to cycle through the slices
        if event.key==",":
            if self.sliceNum>0:
                self.sliceNum-=1
            else:
                self.sliceNum=self.maxSlice
            self.show_slice(self.sliceNum)
        if event.key=="<":
            if self.sliceNum>10:
                self.sliceNum-=10
            else:
                self.sliceNum=self.maxSlice
            self.show_slice(self.sliceNum)
        elif event.key=='.':
            if self.sliceNum<self.maxSlice:
                self.sliceNum+=1
            else:
                self.sliceNum=0
            self.show_slice(self.sliceNum)
        elif event.key=='>':
            if self.sliceNum<self.maxSlice-10:
                self.sliceNum+=10
            else:
                self.sliceNum=0
            self.show_slice(self.sliceNum)
    def show_slice(self, sliceNum):
        '''
        Method to draw one slice from the atlas
        '''
        #Clear the plot and any saved mouse click data for the old dimension
        self.ax.cla()
        self.mouseClickData=[]
        #Draw the image
        self.ax.imshow(np.rot90(self.atlas[:,:,sliceNum], -1), 'gray')
        #Label the axes and draw
        plt.title('< or > to move through the stack\nSlice: {}'.format(sliceNum))
        self.fig.canvas.draw()


# ----- Coordinate transformations from Inkscape-assisted manual registration -----

def get_svg_transform(filename, sliceSize=[1388, 1040]):
    '''
    Get the transform of the second image from an SVG file with two images.

    filename: SVG file containing two images.
    sliceSize: original size [width,height] of the second image.

    Attribute 'transform' has format 'matrix(0.9,-0.1,0.3,0.9,0,0)'
    https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/transform
    '''
    tree = ETree.parse(filename)
    root=tree.getroot()
    images = root.findall('{http://www.w3.org/2000/svg}image')
    if len(images)!=2:
        raise ValueError('The SVG file must contain exactly 2 images')
    if (images[0].attrib['x']!='0') or (images[0].attrib['y']!='0'):
        raise ValueError('The first image (CCF) must be located at (0,0).')
    if images[1].attrib.has_key('transform'):
        transformString = images[1].attrib['transform']
        if transformString.startswith('matrix'):
            transformValueStrings = re.findall(r'-?\d+\.*\d*', transformString)
            transformValues = [float(x) for x in transformValueStrings]
        elif transformString.startswith('rotate'):
            transformValueString = re.findall(r'-?\d+\.*\d*', transformString)[0]
            theta = -np.pi*float(transformValueString)/180 # In radians (and negative)
            # -- Note that this is different from the SVG documentation (b & c swapped) --
            transformValues = [np.cos(theta), -np.sin(theta), np.sin(theta), np.cos(theta)]
    else:
        transformValues = [1,0,0,1,0,0]
    scaleWidth = float(images[1].attrib['width'])/float(sliceSize[0])
    scaleHeight = float(images[1].attrib['height'])/float(sliceSize[1])
    xPos = float(images[1].attrib['x'])
    yPos = float(images[1].attrib['y'])
    scale = np.array([[scaleWidth],[scaleHeight]])
    translate = np.array([[xPos],[yPos]])
    affine = np.reshape(transformValues[:4],(2,2), order='F')
    return (scale, translate, affine)

def apply_svg_transform(scale, translate, affine, coords):
    '''Apply transformation in the appropriate order.'''
    newCoords = scale*coords + translate
    newCoords = np.dot(affine, newCoords)
    return newCoords

def get_coords_from_fiji_csv(filename, pixelSize=1):
    '''
    Read the location of cells from a CSV file created with Fiji.
    Returns coordinates as float in an array of shape (2,nCells)
    Note that values are in Image coordinates (inverted Y), not Cartesian.

    First row of CSV file is " ,Area,Mean,Min,Max,X,Y"
    '''
    allData = np.loadtxt(filename, delimiter=',', skiprows=1)
    coords = allData[:,5:7]/pixelSize
    return coords.T

SVG_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns:xlink="http://www.w3.org/1999/xlink"
   version="1.1"
   id="svg2"
   width="{atlasWidth}"
   height="{atlasHeight}"
   viewBox="0 0 {atlasWidth} {atlasHeight}">
  <image
     xlink:href="{atlasImage}"
     y="0"
     x="0"
     id="image0"
     style="image-rendering:optimizeQuality"
     preserveAspectRatio="none"
     width="456"
     height="320" />
  <image
     xlink:href="{sliceImage}"
     width="{sliceWidth}"
     height="{sliceHeight}"
     preserveAspectRatio="none"
     style="opacity:0.5;image-rendering:optimizeQuality"
     id="image1"
     x="0"
     y="0" />
</svg>
'''

def save_svg_for_registration(filenameSVG, filenameAtlas, filenameSlice, verbose=True):
    '''Save SVG for manual registration'''
    atlasIm = PIL.Image.open(filenameAtlas)
    (atlasWidth,atlasHeight) = atlasIm.size
    sliceIm = PIL.Image.open(filenameSlice)
    (sliceWidth,sliceHeight) = sliceIm.size
    svgString = SVG_TEMPLATE.format(atlasImage=filenameAtlas, sliceImage=filenameSlice,
                                    atlasWidth=atlasWidth, atlasHeight=atlasHeight,
                                    sliceWidth=sliceWidth, sliceHeight=sliceHeight)
    fileSVG = open(filenameSVG, 'w')
    fileSVG.write(svgString)
    fileSVG.close()
    if verbose:
        print('Saved {}'.format(filenameSVG))
    return (atlasIm.size, sliceIm.size)







        
#if __name__=='__main__':
   # imgfile = '/mnt/jarahubdata/histology/anat002_MGB_jpg/b4-C1-01tdT_mirror_correct.jpg'
   # ogrid = OverlayGrid(nRows=3,nCols=2)
   # ogrid.set_grid(imgfile)


'''
imgfile2 = '/data/brainmix_data/test043_TL/p1-D4-01b.jpg'
ogrid.apply_grid(imgfile2)
'''

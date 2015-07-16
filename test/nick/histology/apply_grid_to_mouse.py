from jaratoolbox import histologyanalysis
reload(histologyanalysis)
import os
from jaratoolbox import settings

BASENAME1_25x = 'regwhole'
BASENAME2_5x = 'regMGN' #FIXME: This should change
#LOCAL_HISTOLOGY_DIR = '/mnt/jarahubdata/histology' #Use settings for this since it will change with each person

def dir_structure_1_25x(animalName, channel):
    '''
    Returns the image folder for the 1.25x images, given a mouse name and channel
    '''
    return os.path.join(settings.HISTOLOGY_PATH, animalName, '1.25', 'registered', '{}Channel'.format(channel))

def dir_structure_2_5x(animalName, channel, side):
    '''
    Returns the image folder for the 2.5x images, given a mouse name and channel
    '''
    return os.path.join(settings.HISTOLOGY_PATH, animalName, '2.5', side, 'registered', '{}Channel'.format(channel))

def coord_file(animalName, magnification, side):
    '''
    Returns the full path to the coords file for a given animal, magnification, and grid side
    '''
    coordDir = os.path.join(settings.HISTOLOGY_PATH, animalName, 'coords')
    coordFile = os.path.join(coordDir, 'coords_{}_{}.json'.format(magnification, side))
    return coordFile, coordDir


class BrainGrid(histologyanalysis.OverlayGrid):

    def __init__(self, animalName, nRows = 3, nCols = 2):

        super(BrainGrid, self).__init__(nRows, nCols)
        
        self.animalName = animalName
        self.baseName1_25x = '-'.join([self.animalName, BASENAME1_25x]) #The names of the images, without the channel, number, or file extension
        self.baseName2_5x = '-'.join([self.animalName, BASENAME2_5x])

    def reference_slice_filename(self, magnification, channel, refSliceInd, side = None):
        '''
        Return the full file path for a specified slice number
        
        This method is used to get the file path for a reference slice that can be used to define
        the grid coordinates if none exist. Must input the index of the reference slice (starts from zero). 
        This makes sense because the registered images are also numbered starting from zero. 
        
        Args:
            magnification (str): The magnification level of the images to use. Must be either '1_25x' or '2_5x'
            channel (str): The channel to use. Must be either 'r', 'g', or 'b'
            refSliceInd (int): The index of the slice to return. Starts from zero. 
            side (str): Only required if magnification='2_5x'. Must be either 'left' or 'right'
        
        Returns: 
            refSlicePath (str): The full file path for the requested slice
        
        Example:
            #Initialize a BrainGrid instance for a mouse
            bg = BrainGrid('anat027')

            #The 1.25x images, green channel, slice 0033
            refSlice = bg.reference_slice_filename('1_25x', 'g', 33)

            #The 2.5x images, brightfield channel, slice 0002, left side
            refSlice = bg.reference_slice_filename('2_5x', 'b', 2, 'left')
        
            #Use to set the grid on the reference image
            bg.set_grid(refslice)
        '''

        stack = self.filename_stack(magnification, channel, side)
        refSlicePath = stack[refSliceInd]
        return refSlicePath

    def filename_stack(self, magnification, channel, side = None):
        '''
        Return a list of image file paths to use as an image stack
        
        This method returns a list of image paths for one magnification and channel, 
        and for the 2.5x images, for one side. This stack can then be passed to the 
        apply_to_stack method, which will plot the grid on top of the stack images
        and allow the user to flip through the stack. 
        
        Args:
            magnification (str): The magnification level of the images to use. Must be either '1_25x' or '2_5x'
            channel (str): The channel to use. Must be either 'r', 'g', or 'b'
            side (str): Only required if magnification='2_5x'. Must be either 'left' or 'right'
        
        Returns: 
            stack (list): A list of file path strings for each of the images in the stack
        
        Example:
            #Initialize a BrainGrid instance for a mouse
            bg = BrainGrid('anat027')

            #The 1.25x images, green channel
            stack = bg.filename_stack('1_25x', 'g')

            #The 2.5x images, brightfield channel, left side
            stack = bg.reference_slice_filename('2_5x', 'b', 'left')
        
            #Use to set the grid on the reference image
            bg.apply_to_stack(stack)
        '''
        
        if magnification=='1_25x':
            directory = dir_structure_1_25x(self.animalName, channel)
            stack = [os.path.join(directory, f) for f in sorted(os.listdir(directory)) if f.startswith(self.baseName1_25x)]
            return stack

        elif magnification=='2_5x':
            directory = dir_structure_2_5x(self.animalName, channel, side)
            files = [os.path.join(directory, f) for f in sorted(os.listdir(directory)) if f.startswith(self.baseName2_5x)]
            return stack

        else:
            print "The only currently supported magnification vals are '1_25x' and '2_5x'"
            pass
        
    def define_grid(self, magnification, refSliceInd, side=None):
        '''
        Define the grid coordinates by clicking on a reference slice
        
        This method is a wrapper that gets the file path for a reference image and 
        uses that image to set the grid initially. Use this method the first time
        you are analyzing a particular magnification/side, or if you need to change the 
        grid coordinates. This method always uses the brightfield channel
        
        Args:
            magnification (str): The magnification level of the images to use. Must be either '1_25x' or '2_5x'
            refSliceInd (int): The index of the slice to return. Starts from zero. 
            side (str): Only required if magnification='2_5x'. Must be either 'left' or 'right'
        
        Example:
            #Initialize a BrainGrid instance for a mouse
            bg = BrainGrid('anat027')
        
            #Define a grid for the 1.25x images using reference slice 0033
            bg.define_grid('1_25x', 33)
        
            #Define a grid for the 2.5x images, left side, using reference slice 0002
            bg.define_grid('2_5x', 2, 'left')

        '''
        self.set_grid(self.reference_slice_filename(magnification, 'b', refSliceInd, side))
        
    def stack_grid(self, magnification, channel, side = None):
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
        self.apply_to_stack(self.filename_stack(magnification, channel, side))
        
    def save_mouse_coords(self, magnification, side):
        '''
        Save the coordinates for one magnification, one side
        
        This method saves the coords stored in self.coords as an ASCII file using the json library. 
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
        coordFile, coordDir = coord_file(self.animalName, magnification, side)
        if not os.path.exists(coordDir):
            os.makedirs(coordDir)
        self.save_coords(coordFile)
        
    def load_mouse_coords(self, magnification, side):
        '''
        Load the coordinates for one magnification, one side
        
        This method loads the coords from an ASCII file using the json library, and uses them
        to set the value of self.coords. These coords can later be used if the experimenter wants
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
        coordFile, coordDir = coord_file(self.animalName, magnification, side)
        if not os.path.exists(coordFile):
            print "No coords for this set of images"
            pass
        self.load_coords(coordFile)
        
        


    

    
        

        

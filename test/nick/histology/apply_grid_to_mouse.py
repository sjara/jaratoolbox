from jaratoolbox import histologyanalysis
reload(histologyanalysis)
import os
from jaratoolbox import settings

BASENAME1_25x = 'regwhole'
BASENAME2_5x = 'regMGN' #FIXME: This should change
#LOCAL_HISTOLOGY_DIR = '/mnt/jarahubdata/histology' #Use settings for this since it will change with each person

def dir_structure_1_25x(animalName, channel):
    return os.path.join(settings.HISTOLOGY_PATH, animalName, '1.25', 'registered', '{}Channel'.format(channel))

def dir_structure_2_5x(animalName, channel, side):
    return os.path.join(settings.HISTOLOGY_PATH, animalName, '2.5', side, 'registered', '{}Channel'.format(channel))

def coord_file(animalName, magnification, side):
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
        Must input the index of the reference slice (starts from zero). This makes sense because the 
        registered images are also numbered starting from zero. 
        '''
        stack = self.filename_stack(magnification, channel, side)
        return stack[refSliceInd]

    def filename_stack(self, magnification, channel, side = None):
        
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
        self.set_grid(self.reference_slice_filename(magnification, 'b', refSliceInd, side))
        
    def stack_grid(self, magnification, channel, side = None):
        self.apply_to_stack(self.filename_stack(magnification, channel, side))
        
    def save_mouse_coords(self, magnification, side):
        coordFile, coordDir = coord_file(self.animalName, magnification, side)
        if not os.path.exists(coordDir):
            os.makedirs(coordDir)
        self.save_coords(coordFile)
        
    def load_mouse_coords(self, magnification, side):
        coordFile, coordDir = coord_file(self.animalName, magnification, side)
        if not os.path.exists(coordFile):
            print "No coords for this set of images"
            pass
        self.load_coords(coordFile)
        
        


    

    
        

        

from jaratoolbox import histologyanalysis
import matplotlib.pyplot as plt
reload(histologyanalysis)

import os

mouse = 'anat027'

localHistologyDir = '/mnt/jarahubdata/histology/'

imageBaseName = '-'.join([mouse, 'regwhole'])

def image_filename(channel, imNumber, imageBaseName, localHistologyDir, mouse):
    baseName = '-'.join([imageBaseName, channel])
    fullImageName = ''.join([baseName, '{:04d}'.format(imNumber), '.jpg'])
    imageFolder = os.path.join(localHistologyDir, mouse, '1.25', 'registered', '{}Channel'.format(channel))
    fullImagePath = os.path.join(imageFolder, fullImageName)
    return fullImagePath

def overlay_filename(channel, imNumber, imageBaseName, localHistologyDir, mouse, side):
    baseName = '-'.join([imageBaseName, channel])
    overlayImageName = ''.join([baseName, '{:04d}'.format(imNumber), 'gridOverlay', '.jpg'])
    overlayFolder = os.path.join(localHistologyDir, mouse, '1.25', 'registered', '{}Channel'.format(channel), 'gridOverlay', side)
    if not os.path.exists(overlayFolder):
        print "Making directory {}".format(overlayFolder)
        os.makedirs(overlayFolder)
    overlayImagePath = os.path.join(overlayFolder, overlayImageName)
    return overlayImagePath
    
#print image_filename('b', 1, imageBaseName, localHistologyDir, mouse)
#print overlay_filename('b', 1, imageBaseName, localHistologyDir, mouse, 'right')

imgFile = image_filename('b', 33, imageBaseName, localHistologyDir, mouse)

ogrid = histologyanalysis.OverlayGrid(imgFile, nRows = 4, nCols = 3)
ogrid.set_grid()
    

def apply_to_stack(first, last):
    for i in range(first, last+1):

        for channel in ['b', 'g', 'r']:
            sliceName = image_filename(channel, i, imageBaseName, localHistologyDir, mouse)
            ogrid.apply_grid(sliceName)
            overlayFilename = overlay_filename(channel, i, imageBaseName, localHistologyDir, mouse, 'left')
            plt.savefig(overlayFilename, format = 'jpg')
        
        #plt.waitforbuttonpress()

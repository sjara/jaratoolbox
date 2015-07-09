'''
Tools for analyzing anatomical/histological data.
'''

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np

GRIDCOLOR = [0,0.5,0.5]

def draw_grid(corners,nRows=3,nCols=2):
    '''
    Draw a grid of nRows and nCols starting at the coordinates specified in 'corners'.
    '''
    topleft,bottomright = corners
    xvals = np.linspace(topleft[0],bottomright[0],nCols+1)
    yvals = np.linspace(topleft[1],bottomright[1],nRows+1)
    holdStatus = plt.ishold()
    plt.hold(True)
    for yval in yvals:
        plt.plot(xvals[[0,-1]],[yval,yval],color=GRIDCOLOR)
    for xval in xvals:
        plt.plot([xval,xval],yvals[[0,-1]],color=GRIDCOLOR)
    plt.hold(holdStatus)

class OverlayGrid(object):
    def __init__(self,imgfile,nRows=3,nCols=2):
        '''
        This class allows defining a grid over an image using the mouse,
        and show that grid overlaid on another image.
        '''
        self.origImg = mpimg.imread(imgfile)
        #self.otherimg = None
        self.coords = []
        self.fig = plt.gcf()
        self.cid = None  # Connection ID for mouse clicks
        self.show_image(self.origImg)
        self.nRows = nRows
        self.nCols = nCols
    def show_image(self,img):
        self.fig.clf()
        plt.imshow(img, cmap = 'gray')
        plt.axis('equal')
        plt.show()
    def onclick(self,event):
        #ix, iy = event.xdata, event.ydata
        print '({0},{1})'.format(int(event.xdata), int(event.ydata))
        #global coords
        self.coords.append((event.xdata, event.ydata))
        if len(self.coords) == 2:
            self.fig.canvas.mpl_disconnect(self.cid)
            draw_grid(self.coords, nRows = self.nRows, nCols = self.nCols)
            print 'Done. Now you can apply this grid to another image using apply_grid()'
            print 'Press enter to continue'
    def set_grid(self):
        self.coords = []
        print 'Click two points to define corners of grid.'
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
    def apply_grid(self,imgfile):
        newImg = mpimg.imread(imgfile)
        self.show_image(newImg)
        #FIXME: Not able to pass non-default numbers of rows and columns
        draw_grid(self.coords, nRows = self.nRows, nCols = self.nCols)

if __name__=='__main__':
    imgfile = '/mnt/jarahubdata/histology/anat002_MGB_jpg/b4-C1-01tdT_mirror_correct.jpg'
    ogrid = OverlayGrid(imgfile,nRows=3,nCols=2)
    ogrid.set_grid()

'''
imgfile2 = '/data/brainmix_data/test043_TL/p1-D4-01b.jpg'
ogrid.apply_grid(imgfile2)
'''

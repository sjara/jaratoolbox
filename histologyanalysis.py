'''
Tools for analyzing anatomical/histological data.
'''

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import json

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
    plt.autoscale(False)
    for yval in yvals:
        plt.plot(xvals[[0,-1]],[yval,yval],color=GRIDCOLOR)
    for xval in xvals:
        plt.plot([xval,xval],yvals[[0,-1]],color=GRIDCOLOR)
    plt.hold(holdStatus)

class OverlayGrid(object):

    def __init__(self,nRows=3,nCols=2):
        '''
        This class allows defining a grid over an image using the mouse,
        and show that grid overlaid on another image.
        '''
        self.origImg = []#mpimg.imread(imgfile)
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
        self.fig.clf()
        plt.imshow(img, cmap = 'gray')
        plt.gca().set_aspect('equal', 'box')
        #plt.axis('equal')
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

    def on_key_press(self, event):
        '''
        Method to listen for keypresses and change the slice
        '''

        if event.key=="<":
            if self.sliceNumber>0:
                self.sliceNumber-=1
            else:
                self.sliceNumber=self.maxSliceInd

            self.apply_grid(self.stack[self.sliceNumber])
            self.title_stack_slice()
            #plt.gca().set_aspect('equal', 'box')
                

        elif event.key=='>':
            if self.sliceNumber<self.maxSliceInd:
                self.sliceNumber+=1
            else:
                self.sliceNumber=0

            self.apply_grid(self.stack[self.sliceNumber])
            self.title_stack_slice()
            #plt.gca().set_aspect('equal', 'box')

    def title_stack_slice(self):
        plt.title("Slice {}\nPress < or > to navigate".format(self.sliceNumber))
        
    def set_grid(self,imgfile):
        self.coords = []
        self.origImg = mpimg.imread(imgfile)
        self.fig = plt.gcf()
        self.show_image(self.origImg)
        print 'Click two points to define corners of grid.'
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        # FIXME: find if waiting for click can block execution of the rest.

    def apply_grid(self,imgfile):
        newImg = mpimg.imread(imgfile)
        self.show_image(newImg)
        draw_grid(self.coords, self.nRows, self.nCols)

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

    def load_coords(self, filename):
        with open(filename, 'r') as f:
            self.coords = json.load(f)
            
    def save_coords(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.coords, f)
    


#if __name__=='__main__':
   # imgfile = '/mnt/jarahubdata/histology/anat002_MGB_jpg/b4-C1-01tdT_mirror_correct.jpg'
   # ogrid = OverlayGrid(nRows=3,nCols=2)
   # ogrid.set_grid(imgfile)
    

'''
imgfile2 = '/data/brainmix_data/test043_TL/p1-D4-01b.jpg'
ogrid.apply_grid(imgfile2)
'''

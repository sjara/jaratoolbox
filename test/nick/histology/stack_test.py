from jaratoolbox.test.nick.histology import histologyanalysis_v2
reload(histologyanalysis_v2)
import os

folder = '/home/nick/data/test_images'
imageList = [os.path.join(folder, f) for f in sorted(os.listdir(folder))]

ogrid = histologyanalysis_v2.OverlayGrid()

ogrid.set_grid(imageList[0])

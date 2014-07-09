'''
Additional function for modifying plots.
'''


import matplotlib.pyplot as plt
import numpy as np

def boxoff(ax,keep='left',yaxis=True):
    '''
    Hide axis lines, except left and bottom.
    You can specify to keep instead right and bottom with keep='right'
    '''
    ax.spines['top'].set_visible(False)
    if keep=='left':
        ax.spines['right'].set_visible(False)
    else:
        ax.spines['left'].set_visible(False)        
    xtlines = ax.get_xticklines()
    ytlines = ax.get_yticklines()
    for t in xtlines[1::2]+ytlines[1::2]:
        t.set_visible(False)
    if not yaxis:
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ytlines = ax.get_yticklines()
        for t in ytlines:
            t.set_visible(False)

def set_ticks_fontsize(ax,fontSize):
    '''
    Set fontsize of axis tick labels
    '''
    plt.setp(ax.get_xticklabels(),fontsize=fontSize)
    plt.setp(ax.get_yticklabels(),fontsize=fontSize)

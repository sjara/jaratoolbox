'''
For Daily Behavior Monitoring.
Loads behavior data from mounted jarahub/data/behavior for animals of interest, plot psychometric curve and dynamics data.
'''
import os
from shutil import copy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from jaratoolbox import behavioranalysis
reload(behavioranalysis)
from jaratoolbox import loadbehavior
reload(loadbehavior)
from jaratoolbox import settings

settings.BEHAVIOR_PATH = '/home/languo/data/mnt/jarahubdata'

subjects = ['adap007', 'adap009']
sessions = input("Enter sessions (in a list of strings ['','']) to check behavior performance:")

behavioranalysis.behavior_summary(subjects,sessions,trialslim=[0,1000],outputDir='/home/languo/data/behavior_reports')

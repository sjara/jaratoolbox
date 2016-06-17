import sys
from jaratoolbox.test.nick import soundtypes
from matplotlib import pyplot as plt


subjects = ['amod006', 'amod007', 'amod008', 'amod009', 'amod010']

if len(sys.argv)>1:
    sessions = sys.argv[1:]
    #sessions = input("Enter sessions (in a list of strings ['','']) to check behavior performance:")

soundtypes.sound_type_behavior_summary(subjects, sessions, '', trialslim=[0, 1200])

plt.show()

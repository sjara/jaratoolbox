#Channel numbers for the tetrodes
#Shanks from left to right, looking from the top
#Tetrodes from top to bottom, each shank
#Sites clockwise starting with the uppermost site

tetrodes=array([[4, 7, 5, 2], [3, 8, 6, 1], [12, 15, 13, 10], [11, 16, 14, 9], [20, 23, 21, 18], [19, 24, 22, 17], [28, 31, 29, 26], [27, 32, 30, 25]])

#The electrode a32 connector package. Electrode numbers from left to right, top to bottom (4x10 array)
#GND = -1
#REF=-2
#UNASSIGNED=-3
a32_electrode = array([
    [32, -1, -1, 11],
    [30, -3, -2, 9],
    [31, -3, -3, 7],
    [28, -3, -3, 5],
    [29, 26, 1, 3],
    [27, 24, 4, 2],
    [25, 20, 13, 6],
    [22, 19, 14, 8],
    [23, 18, 15, 10],
    [21, 17, 16, 12]
])

#The adaptor a32 package now. channel numbers from left to right, top to bottom. 4x10 array
#GND = -1
#REF=-2
#UNASSIGNED=-3
a32_adaptor = array([
    [1, -1, -1, 32],
    [2, -2, -2, 31],
    [3, -3, -3, 30],
    [4, -3, -3, 29],
    [5, 16, 17, 28],
    [6, 15, 18, 27],
    [7, 14, 19, 26],
    [8, 13, 20, 25],
    [9, 12, 21, 24],
    [10, 11, 22, 23]
])

#The omnetics connector on the adaptor (neuronexus label facing up)
#Not including the four stabilizing pins
#18x2 matrix, top row left to right, then bottom row left to right
#GND = -1
#REF=-2
om32_adaptor = array([
    [-1, 23, 25, 27, 29, 31, 19, 17, 21, 11, 15, 13, 1, 3, 5, 7, 9, -2],
    [-2, 24, 26, 28, 30, 32, 20, 18, 22, 12, 16, 14, 2, 4, 6, 8, 10, -1]
])


#The omnetics connector on the headstage (chip facing up)
#Not including the four stabilizing pins
#18x2 matrix, top row left to right, then bottom row left to right
#GND = -1
#REF=-2
om32_headstage = array([
    [-1, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, -2],
    [-2, 24, 25, 26, 27, 28, 29, 30, 31, 0, 1, 2, 3, 4, 5, 6, 7, -1]
])


#The channels for a single trode
# tet = tetrodes[1,:]


def convert_to_hs(tet):
    #The corresponding channels on the a32 adaptor
    tet_adaptor = [a32_adaptor[where(a32_electrode==x)] for x in tet]
    #The corresponding channels on the headstage
    tet_hs = [int(om32_headstage[where(om32_adaptor==x)]) for x in tet_adaptor]
    return tet_hs

#the headstage channels for each tetrode
def convert_electrode(tetrodeArray):
    for indTet, tet in enumerate(tetrodeArray):
        thisTet = convert_to_hs(tet)
        if indTet==0:
            tetConfig=thisTet
        else:
            tetConfig=vstack([tetConfig, thisTet])

    return tetConfig



# output (the headstage channels that correspond to each individual tetrode):
# [30, 27, 20, 21]
# [26, 22, 25, 17]
# [23, 16, 18, 24]
# [28, 31, 29, 19]
# [2, 8, 7, 0]
# [13, 14, 6, 15]
# [4, 11, 10, 1]
# [5, 12, 3, 9]


#Now we want to make a config file for openephys with this information

from xml.dom import minidom


## --- The loop to set each subchannel

channelArray = convert_electrode(tetrodes)

#Parse in the xml file
xmldoc = minidom.parse('/tmp/4TT_02_pinp')

#Find the spike detector node
processors = xmldoc.getElementsByTagName('PROCESSOR')
pnames = [processor.attributes['name'].value for processor in processors]
spikeDetectorIndex = pnames.index(u'Filters/Spike Detector')
sdet = processors[spikeDetectorIndex]

#Get the electrode nodes in the spike detector
electrodes = sdet.getElementsByTagName('ELECTRODE')

#Set the channel value for each channel of the electrode
for indElectrode, electrode in enumerate(electrodes):
    subchannels = electrode.getElementsByTagName('SUBCHANNEL')
    for indChannel, channel in enumerate(subchannels):
        chanVal = channelArray[indElectrode, indChannel]
        channel.attributes['ch']._set_value(str(chanVal))

#Check to make sure the values were set
for indElectrode, electrode in enumerate(electrodes):
    subchannels = electrode.getElementsByTagName('SUBCHANNEL')
    for indChannel, channel in enumerate(subchannels):
        print type(channel.attributes['ch'].value)

#Write the new config file out
xmldoc.writexml( open('/tmp/neuronexus_config', 'w'),
               indent="  ",
               addindent="  ",
               newl='\n')





'''
#Parse in an existing config file
xmldoc = minidom.parse('/tmp/4TT_02_pinp')
processors = xmldoc.getElementsByTagName('PROCESSOR')
pnames = [processor.attributes['name'].value for processor in processors]
spikeDetectorIndex = pnames.index(u'Filters/Spike Detector')
sdet = processors[spikeDetectorIndex]
electrodes = sdet.getElementsByTagName('ELECTRODE')

e0 = electrodes[0]

e0subchans = e0.getElementsByTagName('SUBCHANNEL')

subchan0 = e0subchans[0]

subchan0.attributes['ch']._set_value(5)


electrodes[0].getElementsByTagName('SUBCHANNEL')[0].attributes['ch'].value
'''

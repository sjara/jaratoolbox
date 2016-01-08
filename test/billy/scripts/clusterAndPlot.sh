
#rsync -a --progress --exclude '*.continuous' jarauser@jaraphys2:~/data/ephys/test055/ ~/data/ephys/test055/
#rsync -a --progress jarauser@jararig2:/var/tmp/data/santiago/test055/ ~/data/behavior/santiago/test055/
#rsync -a --progress --exclude '*.continuous' jarauser@jaraphys2:~/data/ephys/test017/ ~/data/ephys/test017/
#rsync -a --progress jarauser@jararig2:/var/tmp/data/santiago/test017/ ~/data/behavior/santiago/test017/
#python spikeAnalysis_test017.py
#python spikeAnalysis_test055.py
#python compareRasterAndHistogramClustersOneFreq.py
#python rasterHistPsyCurve.py


#rsync -a --progress --exclude '*.continuous' jarauser@jaraphys2:~/data/ephys/test089/ ~/data/ephys/test089/
#rsync -a --progress jarauser@jararig2:/var/tmp/data/santiago/test089/ ~/data/behavior/santiago/test089/
'''
python spikeAnalysis.py test089
rm ~/data/ephys/test089/*_kk/*.fet.*
python addModulationCheckSwitching.py test089 #must be run before switching report
python rasterHistSwitch.py test089
python raster_per_block.py test089
python rasterAllFreqSwitch.py test089
python rasterMovementAlignedBlocks test089
python SwitchingReport.py test089
python addMinTrialCheckSwitching.py test089
python addMinBehavePerformanceSwitch.py test089
python add_sound_response_stat.py test089
'''

#rsync -a --progress --exclude '*.continuous' jarauser@jaraphys2:~/data/ephys/test017/ ~/data/ephys/test017/
#rsync -a --progress jarauser@jararig2:/var/tmp/data/santiago/test017/ ~/data/behavior/santiago/test017/

#python spikeAnalysis.py test017
#rm ~/data/ephys/test017/*_kk/*.fet.*
#python rasterHistSwitch.py test017
#python raster_per_block.py test017
#python rasterAllFreqSwitch.py test017
#python rasterMovementAlignedBlocks test017
#python SwitchingReport.py test017
#python addMinTrialCheckSwitching.py test017
#python addMinBehavePerformanceSwitch.py test017
#python add_sound_response_stat.py test017


########THIS IS FOR TEST087 SWITCHING DATA###################################################
#rsync -a --progress --exclude '*.continuous' jarauser@jaraphys2:~/data/ephys/test087/ ~/data/ephys/test087/
#rsync -a --progress jarauser@jararig2:/var/tmp/data/santiago/test087/ ~/data/behavior/santiago/test087/
#python spikeAnalysis.py test087
#rm ~/data/ephys/test087/*_kk/*.fet.*
#python rasterHistSwitch.py test087
#python raster_per_block.py test087
#python rasterAllFreqSwitch.py test087
#python rasterMovementAlignedBlocks test087
#python SwitchingReport.py test087
#python addMinTrialCheckSwitching.py test087
#python addMinBehavePerformanceSwitch.py test087
#python add_sound_response_stat.py test087

########THIS IS FOR TEST087 PSYCHOMETRIC CURVE DATA###################################################
#rsync -a --progress --exclude '*.continuous' jarauser@jaraphys2:~/data/ephys/test087/ ~/data/ephys/test087/
#rsync -a --progress jarauser@jararig2:/var/tmp/data/santiago/test087/ ~/data/behavior/santiago/test087/
'''
python spikeAnalysis.py test087
rm ~/data/ephys/test087/*_kk/*.fet.*
python rasterHistPsyCurve.py test087
python PsyCurveReportCenterFreq.py test087
python addMinTrialCheckPsyCurve.py test087
python addMinBehavePerformancePsyCurve.py test087
python add_sound_response_stat.py test087
'''

#rsync -a --progress --exclude '*.continuous' jarauser@jaraphys2:~/data/ephys/test059/ ~/data/ephys/test059/
#rsync -a --progress jarauser@jararig2:/var/tmp/data/santiago/test059/ ~/data/behavior/santiago/test059/

#python spikeAnalysis.py test059
#rm ~/data/ephys/test059/*_kk/*.fet.*
#python rasterHistSwitch.py test059
#python raster_per_block.py test059
#python rasterAllFreqSwitch.py test059
#python rasterMovementAlignedBlocks test059
#python SwitchingReport.py test059
#python addMinTrialCheckSwitching.py test059
#python addMinBehavePerformanceSwitch.py test059
#python add_sound_response_stat.py test059


#rsync -a --progress --exclude '*.continuous' jarauser@jaraphys2:~/data/ephys/test055/ ~/data/ephys/test055/
#rsync -a --progress jarauser@jararig2:/var/tmp/data/santiago/test055/ ~/data/behavior/santiago/test055/
#python spikeAnalysis.py test055
#rm ~/data/ephys/test055/*_kk/*.fet.*
#python rasterHistPsyCurve.py test055
#python PsyCurveReportCenterFreq.py test055
#python addMinTrialCheckPsyCurve.py test055
#python addMinBehavePerformancePsyCurve.py test055
#python add_sound_response_stat.py test055

#rsync -a --progress --exclude '*.continuous' jarauser@jaraphys2:~/data/ephys/test053/ ~/data/ephys/test053/
#rsync -a --progress jarauser@jararig2:/var/tmp/data/santiago/test053/ ~/data/behavior/santiago/test053/
#python spikeAnalysis.py test053
#rm ~/data/ephys/test053/*_kk/*.fet.*
#python rasterHistPsyCurve.py test053
#python PsyCurveReportCenterFreq.py test053
#python addMinTrialCheckPsyCurve.py test053
#python addMinBehavePerformancePsyCurve.py test053
#python add_sound_response_stat.py test053

#rsync -a --progress --exclude '*.continuous' jarauser@jaraphys2:~/data/ephys/test086/ ~/data/ephys/test086/
#rsync -a --progress jarauser@jararig2:/var/tmp/data/santiago/test086/ ~/data/behavior/santiago/test086/
#python spikeAnalysis.py test086
#rm ~/data/ephys/test086/*_kk/*.fet.*
#python rasterHistPsyCurve.py test086
#python PsyCurveReportCenterFreq.py test086
#python addMinTrialCheckPsyCurve.py test086
#python addMinBehavePerformancePsyCurve.py test086
#python add_sound_response_stat.py test086



#rsync -a --progress --exclude '*.continuous' jarauser@jaraphys2:~/data/ephys/adap002/ ~/data/ephys/adap002/
#rsync -a --progress jarauser@jararig2:/var/tmp/data/santiago/adap002/ ~/data/behavior/santiago/adap002/
#python spikeAnalysis.py adap002
#rm ~/data/ephys/adap002/*_kk/*.fet.*
#python rasterHistPsyCurve.py adap002
#python PsyCurveReportCenterFreq.py adap002
#python addMinTrialCheckPsyCurve.py adap002
#python addMinBehavePerformancePsyCurve.py adap002
#python add_sound_response_stat.py adap002


rsync -a --progress --exclude '*.continuous' jarauser@jaraphys2:~/data/ephys/adap010/ ~/data/ephys/adap010/
rsync -a --progress jarauser@jararig2:/var/tmp/data/santiago/adap010/ ~/data/behavior/santiago/adap010/

#python spikeAnalysis.py adap010
rm ~/data/ephys/adap010/*_kk/*.fet.*
python addModulationCheckSwitching.py adap010 #must be run before switching report
python rasterHistSwitch.py adap010
python raster_per_block.py adap010
python rasterAllFreqSwitch.py adap010
python rasterMovementAlignedBlocks.py adap010
python SwitchingReport.py adap010
python addMinTrialCheckSwitching.py adap010
python addMinBehavePerformanceSwitch.py adap010
python add_sound_response_stat.py adap010


#rsync -a --progress --exclude '*.continuous' jarauser@jaraphys2:~/data/ephys/adap004/ ~/data/ephys/adap004/
#rsync -a --progress jarauser@jararig2:/var/tmp/data/santiago/adap004/ ~/data/behavior/santiago/adap004/
#python spikeAnalysis.py adap004
#rm ~/data/ephys/adap004/*_kk/*.fet.*
'''
python rasterHistPsyCurve.py adap004
python PsyCurveReportCenterFreq.py adap004
python addMinTrialCheckPsyCurve.py adap004
python addMinBehavePerformancePsyCurve.py adap004
python add_sound_response_stat.py adap004
'''

#bash add_process_cells.sh

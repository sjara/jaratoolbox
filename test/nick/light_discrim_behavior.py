from jaratoolbox import loadbehavior
import os
from jaratoolbox import behavioranalysis
from statsmodels.stats.proportion import proportion_confint


subjects = ['adap022', 'adap026', 'adap027', 'adap030']
sessions = ['20160612a', '20160613a', '20160614a', '20160615a', '20160616a']


#allPerf(subjects, sessions)
allPerf = zeros((len(subjects), len(sessions)))
upper = zeros((len(subjects), len(sessions)))
lower = zeros((len(subjects), len(sessions)))


for indSubject, subject in enumerate(subjects):
    for indSession, session in enumerate(sessions):
        bfile = loadbehavior.path_to_behavior_data(subject, 'lightDiscrim', session)
        bdata = loadbehavior.BehaviorData(bfile)

        valid = bdata['valid']
        correct = bdata['outcome'] == bdata.labels['outcome']['correct']

        validCorrect = (valid & correct)

        numValid = sum(valid)
        numCorrect = sum(validCorrect)

        allPerf[indSubject, indSession] = numCorrect/float(numValid)

        ci = proportion_confint(numCorrect, numValid)

        lower[indSubject, indSession] = ci[0]
        upper[indSubject, indSession] = ci[1]

figure()
clf()
for indSubject, subject in enumerate(subjects):
    subplot(len(subjects), 1, indSubject+1)
    thisPerf = allPerf[indSubject, :]
    plot(thisPerf, 'b-o')
    upperWhisker = array(upper[indSubject, :] - thisPerf)
    lowerWhisker = array(thisPerf - lower[indSubject, :])
    errorbar(range(len(thisPerf)), 100*thisPerf, yerr=[100*lowerWhisker, 100*upperWhisker])
    ylim([50, 100])
    xlim([-0.1, len(sessions)-0.9])
    title('{}'.format(subject))
    ylabel('% correct')
    axhline(90, color='0.7')
    axhline(75, color='0.7')


xlabel('session')









from jaratoolbox import loadbehavior
import os
from jaratoolbox import behavioranalysis
from statsmodels.stats.proportion import proportion_confint


subjects = ['adap022', 'adap026', 'adap027', 'adap030']
sessions = ['20160612a', '20160613a', '20160614a', '20160615a', '20160616a', '20160617a', '20160618a', '20160619a', '20160620a', '20160621a']


#allPerf(subjects, sessions)
allPerf = zeros((len(subjects), len(sessions)))
upper = zeros((len(subjects), len(sessions)))
lower = zeros((len(subjects), len(sessions)))

allPerfRightSide = zeros((len(subjects), len(sessions)))
allPerfLeftSide = zeros((len(subjects), len(sessions)))

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

        # import ipdb; ipdb.set_trace()

        ci = proportion_confint(numCorrect, numValid)

        lower[indSubject, indSession] = ci[0]
        upper[indSubject, indSession] = ci[1]

        rightTrials = bdata['rewardSide']==bdata.labels['rewardSide']['right']
        leftTrials = bdata['rewardSide']==bdata.labels['rewardSide']['left']

        correctRight = (validCorrect & rightTrials)
        correctLeft = (validCorrect & leftTrials)

        allPerfRightSide[indSubject, indSession] = sum(correctRight)/float(sum(rightTrials))
        allPerfLeftSide[indSubject, indSession] = sum(correctLeft)/float(sum(leftTrials))



figure()
clf()
for indSubject, subject in enumerate(subjects):

    # subplot2grid((len(subjects), 3), (indSubject, 0), colspan=1)
    # subplot2grid((len(subjects), 3), (indSubject, 1), colspan=2)

    subplot(len(subjects), 1, indSubject+1)
    thisPerf = allPerf[indSubject, :]
    plot(100*thisPerf, 'b-o')
    upperWhisker = array(upper[indSubject, :] - thisPerf)
    lowerWhisker = array(thisPerf - lower[indSubject, :])
    errorbar(range(len(thisPerf)), 100*thisPerf, yerr=[100*lowerWhisker, 100*upperWhisker], label='Overall')
    plot(100*allPerfLeftSide[indSubject, :], 'r-o', label='Left')
    plot(100*allPerfRightSide[indSubject, :], 'g-o', label='Right')
    ylim([-5, 105])
    xlim([-0.1, len(sessions)-0.9])
    title('{}'.format(subject))
    ylabel('% correct')
    axhline(100, color='0.7')
    axhline(50, color='0.7')
    axhline(0, color='0.7')

legend(loc=8)
xlabel('session')

savefig('/tmp/light_discrim_behav.png')









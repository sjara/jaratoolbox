from jaratoolbox import loadopenephys
from jaratoolbox import spikesorting
from jaratoolbox.test.nick import clustercutting
from matplotlib import pyplot as plt
import os
import numpy as np

import sklearn
import sklearn.manifold
import sklearn.neighbors
import sklearn.mixture


class KernelTSNEClassifier(object):

    def __init__(self, X, trainingSetSize=5000):
        self.data = X

        dataToUse = np.random.randint(len(X), size=trainingSetSize)
        self.trainingSet = self.data[dataToUse, :]

        self.euc = sklearn.neighbors.DistanceMetric.get_metric('euclidean')

    def train(self, sigma_scale=0.1, n_clusters=12):

        print("Calculating Pairwise Distances")

        X_dist = self.euc.pairwise(self.trainingSet)

        print("Embedding training set")
        model = sklearn.manifold.TSNE(n_components=2, verbose=10, n_iter=1000, metric='precomputed')
        self.Y_train = model.fit_transform(X_dist)

        print("Calculating Kernel")

        self.A, self.sig_nb = self.kmap_train(X_dist, self.Y_train, sigma_scale)

        print("Fitting GMM")
        self.fit_gmm(n_clusters)


    def predict_full_dataset(self, chunk=5000):

        for indItem, oneItem in enumerate(self.data):
            clusterLabel = self.predict(oneItem)
            print clusterLabel


    def predict(self, newData):

        print("Calculating distance between new data and training data")
        X_dist_ose = self.euc.pairwise(newData, self.trainingSet)
        Y_ose = self.kmap_test(X_dist_ose, self.A, self.sig_nb)
        clusterLabels = self.predict_cluster(Y_ose)
        return clusterLabels

    def fit_gmm(self, n_clusters):
        self.mixture = sklearn.mixture.GMM(n_components=n_clusters)
        self.mixture.fit(self.Y_train)

    def predict_cluster(self, Y_new):
        clusterLabels = self.mixture.predict(Y_new)
        return clusterLabels

    def kmap_train(self, X_dist, Y, sigma_scale):
        #Ported from KMap Toolbox by Barbara Hammer's group

        k_nb = 10 # Number of neighbors to use
        f_local =1 # 0 for global, 1 for local

        # sig_nb=determine_sigma(X_dist, k_nb, f_local);
        sig_nb = self.determine_sigma_from_X(self.trainingSet, k_nb, sigma_scale)
        sig_nb = sig_nb**2
        sig_nb = sig_nb * sigma_scale #Scale the sigma values

        #Compute the kernel
        kernel = np.exp(-1*(X_dist/sig_nb))

        #Divide each row by the row sum (use newaxis trick to get broadcasting to behave)
        kernel = kernel / np.sum(kernel, 1)[:,np.newaxis]

        A = np.dot(np.linalg.pinv(kernel), Y)

        return A, sig_nb

    @staticmethod
    def kmap_test(X_dist_ose, A, sig_nb):
        kernel_ose = np.exp(-1*(X_dist_ose/sig_nb))

        #Divide each row by the row sum (use newaxis trick to get broadcasting to behave)
        kernel_ose = kernel_ose / np.sum(kernel_ose, 1)[:,np.newaxis]

        Y_ose = np.dot(kernel_ose, A)

        return Y_ose

    @staticmethod
    def determine_sigma_from_X(X, k_nb, local=True):
        #Adapted from KMap Toolbox by Barbara Hammer's group
        #Just needs the raw vectors, not a distance matrix

        k = k_nb + 1 ##### We add 1 to the number of the neighbor to return because the first will always be zero (dist to self)

        nbrs = sklearn.neighbors.NearestNeighbors(n_neighbors=k, algorithm='auto').fit(X)
        distances, indices = nbrs.kneighbors(X)

        if local:
            return distances[:,-1] #Return distances to last (kth)
        else:
            return mean(distances[:,-1]) #Return average distance to the kth neighbor

if __name__=='__main__':
    animalName='pinp013'
    ephysLoc = '/home/nick/data/ephys/'
    ephysPath = os.path.join(ephysLoc, animalName)
    ephysFn='2016-05-27_14-13-26'
    tetrode=3
    spikesFn = os.path.join(ephysPath, ephysFn, 'Tetrode{}.spikes'.format(tetrode))
    dataSpikes = loadopenephys.DataSpikes(spikesFn)

    (numSpikes, numChans, numSamples) = shape(dataSpikes.samples)
    allWaves = dataSpikes.samples.reshape(numSpikes, numChans*numSamples)

    kernClass = KernelTSNEClassifier(allWaves)

    import timeit
    start_time = timeit.default_timer()

    kernClass.train()

    kernClass.predict_full_dataset()

    elapsed = timeit.default_timer() - start_time
    print 'ELAPSED TIME: {} mins'.format(elapsed/60)


    from sklearn.datasets import load_iris

    data = load_iris()

    kernClass = KernelTSNEClassifier(data.data, trainingSetSize=50)
    kernClass.train()
    kernClass.predict_full_dataset()


    X_dist = kernClass.euc.pairwise(data.data)

   model =  sklearn.manifold.TSNE(n_components=2, verbose=10, n_iter=1000, metric='precomputed')
    
   Y = model.fit_transform(X_dist)

   plot(Y[:,0], Y[:,1], '.')



from data import BwDataset


class NumpyBwDataset(BwDataset):
    """NumpyBwDataset class.

    This datastructure wraps arbitrary numpy.arrays for a
    deep learning application with BlueWhale.
    The main difference to an ordinary numpy.array is that
    NumpyBwDataset has a name attribute.

    Parameters
    -----------
    name : str
        Name of the dataset
    array : :class:`numpy.array`
        Numpy array.
    samplenames : list(str)
        Samplenames (optional). They are relevant if the dataset
        is used to hold labels for a deep learning applications.
        For instance, samplenames might correspond to category names.
    cachedir : str or None
        Directory in which the cachefiles are located. Default: None.
    """

    def __init__(self, name, array, samplenames=None, cachedir=None):

        self.data = array
        if samplenames:
            self.samplenames = samplenames

        self.cachedir = cachedir

        BwDataset.__init__(self, '{}'.format(name))

    def __repr__(self):
        return 'NumpyBwDataset("{}", <np.array>)'.format(self.name)

    def __len__(self):
        return len(self.data)

    @property
    def shape(self):
        __doc__ = super(NumpyBwDataset, self).__doc__  # noqa
        return self.data.shape

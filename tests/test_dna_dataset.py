import os

import matplotlib
import numpy as np
import pkg_resources
import pytest
from HTSeq import BED_Reader
from keras.layers import Input
from keras.models import Model

from janggu.data import Dna
from janggu.layers import Complement
from janggu.layers import Reverse
from janggu.utils import complement_permmatrix

matplotlib.use('AGG')

binsize = 200
flank = 150
stepsize = 50


def datalen(bed_file):
    binsizes = 0
    reader = BED_Reader(bed_file)
    for reg in reader:
        binsizes += (reg.iv.end - reg.iv.start - binsize + stepsize)//stepsize
    return binsizes


def test_dna_dims_order_1(tmpdir):
    os.environ['JANGGU_OUTPUT'] = tmpdir.strpath
    order = 1
    data_path = pkg_resources.resource_filename('janggu', 'resources/')
    bed_merged = os.path.join(data_path, 'sample.gtf')
    refgenome = os.path.join(data_path, 'sample_genome.fa')

    data = Dna.create_from_refgenome('train', refgenome=refgenome,
                                     regions=bed_merged,
                                     storage='ndarray',
                                     order=order)
    # for order 1
    assert len(data) == 100
    assert data.shape == (100, 200, 4, 1)
    # the correctness of the sequence extraction was also
    # validated using:
    # bedtools getfasta -fi sample_genome.fa -bed sample.bed
    # >chr1:15000-25000
    # ATTGTGGTGA...
    # this sequence is read from the forward strand
    np.testing.assert_equal(data[0][0, :10, :, 0],
                            np.asarray([[1, 0, 0, 0],  # A
                                        [0, 0, 0, 1],  # T
                                        [0, 0, 0, 1],  # T
                                        [0, 0, 1, 0],  # C
                                        [0, 0, 0, 1],  # T
                                        [0, 0, 1, 0],  # G
                                        [0, 0, 1, 0],  # G
                                        [0, 0, 0, 1],  # T
                                        [0, 0, 1, 0],  # G
                                        [1, 0, 0, 0]],  # A
                            dtype='int8'))

    # bedtools getfasta -fi sample_genome.fa -bed sample.bed
    # >chr2:15000-25000
    # ggggaagcaa...
    # this sequence is read from the reverse strand
    # so we have ...ttgcttcccc
    np.testing.assert_equal(data[50][0, -10:, :, 0],
                            np.asarray([[0, 0, 0, 1],  # T
                                        [0, 0, 0, 1],  # T
                                        [0, 0, 1, 0],  # G
                                        [0, 1, 0, 0],  # C
                                        [0, 0, 0, 1],  # T
                                        [0, 0, 0, 1],  # T
                                        [0, 1, 0, 0],  # C
                                        [0, 1, 0, 0],  # C
                                        [0, 1, 0, 0],  # C
                                        [0, 1, 0, 0]],  # C
                            dtype='int8'))


def test_dna_dims_order_2(tmpdir):
    os.environ['JANGGU_OUTPUT'] = tmpdir.strpath
    order = 2
    data_path = pkg_resources.resource_filename('janggu', 'resources/')
    bed_merged = os.path.join(data_path, 'sample.bed')
    refgenome = os.path.join(data_path, 'sample_genome.fa')

    data = Dna.create_from_refgenome('train', refgenome=refgenome,
                                     regions=bed_merged,
                                     storage='ndarray',
                                     order=order)
    # for order 1
    assert len(data) == 100
    assert data.shape == (100, 199, 16, 1)
    # the correctness of the sequence extraction was also
    # validated using:
    # >bedtools getfasta -fi sample_genome.fa -bed sample.bed
    # >chr1:15000-25000
    # ATTGTGGTGAC...
    np.testing.assert_equal(
        data[0][0, :10, :, 0],
        np.asarray([[0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # AT
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # TT
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],  # TG
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],  # GT
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],  # TG
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],  # GG
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],  # GT
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],  # TG
                    [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],  # GA
                    [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]],  # AC
                   dtype='int8'))

    # bedtools getfasta -fi sample_genome.fa -bed sample.bed
    # >chr2:15000-25000
    # ggggaagcaag...
    # this sequence is read from the reverse strand
    # so we have ...cttgcttcccc
    np.testing.assert_equal(
        data[50][0, -10:, :, 0],
        np.asarray([[0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],  # CT
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # TT
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],  # TG
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],  # GC
                    [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],  # CT
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # TT
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],  # TC
                    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # CC
                    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # CC
                    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]],  # CC
                   dtype='int8'))


def reverse_layer(order):
    data_path = pkg_resources.resource_filename('janggu', 'resources/')

    bed_file = os.path.join(data_path, 'sample.bed')

    refgenome = os.path.join(data_path, 'sample_genome.fa')

    data = Dna.create_from_refgenome('train', refgenome=refgenome,
                                     regions=bed_file,
                                     storage='ndarray',
                                     binsize=binsize,
                                     flank=flank,
                                     order=order)

    dna_in = Input(shape=data.shape[1:], name='dna')
    rdna_layer = Reverse()(dna_in)

    rmod = Model(dna_in, rdna_layer)

    # actual shape of DNA
    dna = data[0]
    np.testing.assert_equal(dna[:, ::-1, :, :], rmod.predict(dna))


def complement_layer(order):
    data_path = pkg_resources.resource_filename('janggu', 'resources/')

    bed_file = os.path.join(data_path, 'sample.bed')

    refgenome = os.path.join(data_path, 'sample_genome.fa')

    data = Dna.create_from_refgenome('train', refgenome=refgenome,
                                     regions=bed_file,
                                     storage='ndarray',
                                     binsize=binsize,
                                     flank=flank,
                                     order=order)

    dna_in = Input(shape=data.shape[1:], name='dna')
    cdna_layer = Complement()(dna_in)
    cmod = Model(dna_in, cdna_layer)

    # actual shape of DNA
    dna = data[0]

    cdna = cmod.predict(dna)
    ccdna = cmod.predict(cdna)

    with pytest.raises(Exception):
        np.testing.assert_equal(dna, cdna)
    np.testing.assert_equal(dna, ccdna)


def test_reverse_order_1(tmpdir):
    os.environ['JANGGU_OUTPUT'] = tmpdir.strpath
    reverse_layer(1)


def test_reverse_order_2(tmpdir):
    os.environ['JANGGU_OUTPUT'] = tmpdir.strpath
    reverse_layer(2)


def test_complement_order_1(tmpdir):
    os.environ['JANGGU_OUTPUT'] = tmpdir.strpath
    complement_layer(1)


def test_complement_order_2(tmpdir):
    os.environ['JANGGU_OUTPUT'] = tmpdir.strpath
    complement_layer(2)


def test_revcomp_rcmatrix(tmpdir):
    os.environ['JANGGU_OUTPUT'] = tmpdir.strpath

    rcmatrix = complement_permmatrix(1)

    np.testing.assert_equal(rcmatrix,
                            np.array([[0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0],
                                      [1, 0, 0, 0]]))

    rcmatrix = complement_permmatrix(2)

    np.testing.assert_equal(rcmatrix[0],
                            np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                      0, 0, 0, 1]))
    np.testing.assert_equal(rcmatrix[4],
                            np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                      0, 0, 1, 0]))
    np.testing.assert_equal(rcmatrix[8],
                            np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                      0, 1, 0, 0]))
    np.testing.assert_equal(rcmatrix[12],
                            np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                      1, 0, 0, 0]))

    np.testing.assert_equal(rcmatrix[1],
                            np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
                                      0, 0, 0, 0]))
    np.testing.assert_equal(rcmatrix[5],
                            np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0,
                                      0, 0, 0, 0]))
    np.testing.assert_equal(rcmatrix[9],
                            np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0,
                                      0, 0, 0, 0]))
    np.testing.assert_equal(rcmatrix[13],
                            np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0,
                                      0, 0, 0, 0]))


def test_rcmatrix_identity():

    for order in range(1, 4):

        rcmatrix = complement_permmatrix(order)

        np.testing.assert_equal(np.eye(pow(4, order)),
                                np.matmul(rcmatrix, rcmatrix))


def test_dna_dataset_sanity(tmpdir):
    os.environ['JANGGU_OUTPUT'] = tmpdir.strpath
    data_path = pkg_resources.resource_filename('janggu', 'resources/')
    bed_file = os.path.join(data_path, 'sample.bed')

    refgenome = os.path.join(data_path, 'sample_genome.fa')

    with pytest.raises(Exception):
        # name must be a string
        Dna.create_from_refgenome(1.23, refgenome='',
                                  storage='ndarray',
                                  regions=bed_file, order=1)
    with pytest.raises(Exception):
        Dna.create_from_refgenome('train', refgenome='',
                                  storage='ndarray',
                                  regions=bed_file, order=1)
    with pytest.raises(Exception):
        Dna.create_from_refgenome('train', refgenome='test',
                                  storage='ndarray',
                                  regions=bed_file, order=1)

    with pytest.raises(Exception):
        Dna.create_from_refgenome('train', refgenome=refgenome,
                                  storage='ndarray',
                                  regions=bed_file, order=0)
    with pytest.raises(Exception):
        Dna.create_from_refgenome('train', refgenome=refgenome,
                                  storage='ndarray',
                                  regions=bed_file, flank=-1)
    with pytest.raises(Exception):
        Dna.create_from_refgenome('train', refgenome=refgenome,
                                  storage='ndarray',
                                  regions=bed_file, binsize=0)
    with pytest.raises(Exception):
        Dna.create_from_refgenome('train', refgenome=refgenome,
                                  storage='ndarray',
                                  regions=bed_file, stepsize=0)

    with pytest.raises(Exception):
        Dna.create_from_refgenome('train', refgenome=refgenome,
                                  storage='step',
                                  regions=bed_file, order=1)

    assert not os.path.exists(os.path.join(tmpdir.strpath, 'train',
                                           'storage.h5'))

    Dna.create_from_refgenome('train', refgenome=refgenome,
                              storage='ndarray',
                              regions=None, order=1)
    Dna.create_from_refgenome('train', refgenome=refgenome,
                              storage='hdf5',
                              regions=bed_file, order=1)

    assert os.path.exists(os.path.join(tmpdir.strpath, 'datasets', 'train',
                                       'order1', 'storage.h5'))


def test_read_dna_from_fasta_order_1():

    data_path = pkg_resources.resource_filename('janggu', 'resources/')

    order = 1
    filename = os.path.join(data_path, 'sample.fa')
    data = Dna.create_from_fasta('train', fastafile=filename,
                                 order=order, cache=False)

    np.testing.assert_equal(len(data), 3897)
    np.testing.assert_equal(data.shape, (3897, 200, 4, 1))
    np.testing.assert_equal(
        data[0][0, :10, :, 0],
        np.asarray([[0, 1, 0, 0],
                    [1, 0, 0, 0],
                    [0, 1, 0, 0],
                    [1, 0, 0, 0],
                    [0, 0, 1, 0],
                    [0, 1, 0, 0],
                    [1, 0, 0, 0],
                    [0, 0, 1, 0],
                    [1, 0, 0, 0],
                    [0, 0, 1, 0]], dtype='int8'))


def test_read_dna_from_fasta_order_2():
    data_path = pkg_resources.resource_filename('janggu', 'resources/')

    order = 2
    filename = os.path.join(data_path, 'sample.fa')
    data = Dna.create_from_fasta('train', fastafile=filename,
                                 order=order, cache=False)

    np.testing.assert_equal(len(data), 3897)
    np.testing.assert_equal(data.shape, (3897, 199, 16, 1))
    np.testing.assert_equal(
        data[0][0, :10, :, 0],
        np.asarray([[0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]], dtype='int8'))

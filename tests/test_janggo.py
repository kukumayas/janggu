import json
import os

import numpy as np
import pkg_resources
import pytest
from keras.layers import Dense
from keras.layers import Flatten
from keras.layers import Input

from janggo import Janggo
from janggo import inputlayer
from janggo import janggo_fit_generator
from janggo import janggo_predict_generator
from janggo import outputconv
from janggo import outputdense
from janggo.cli import main
from janggo.data import CoverageDataset
from janggo.data import DnaDataset
from janggo.data import NumpyDataset
from janggo.data import TabDataset
from janggo.data import input_props
from janggo.data import output_props
from janggo.evaluation import EvaluatorList
from janggo.evaluation import ScoreEvaluator
from janggo.evaluation import accuracy
from janggo.evaluation import auprc
from janggo.evaluation import auroc
from janggo.evaluation import f1_score
from janggo.layers import Complement
from janggo.layers import Reverse


def test_main():
    """Basic main test"""
    main([])


def test_janggo_instance_dense(tmpdir):
    """Test Janggo creation by shape and name. """
    data_path = pkg_resources.resource_filename('janggo', 'resources/')
    bed_file = os.path.join(data_path, 'regions.bed')

    csvfile = os.path.join(data_path, 'ctcf_sample.csv')

    refgenome = os.path.join(data_path, 'genome.fa')

    dna = DnaDataset.create_from_refgenome('dna', refgenome=refgenome,
                                           storage='ndarray',
                                           regions=bed_file, order=1)

    ctcf = TabDataset('ctcf', filename=csvfile)

    @inputlayer
    @outputdense
    def _cnn_model(inputs, inp, oup, params):
        layer = inputs['.']
        layer = Complement(1)(layer)
        layer = Reverse()(layer)
        layer = Flatten()(layer)
        output = Dense(params[0])(layer)
        return inputs, output

    with pytest.raises(Exception):
        # due to No input name . defined
        bwm = Janggo.create('dna_ctcf_HepG2-cnn',
                            (_cnn_model, (2,)),
                            inputp=input_props(dna),
                            outputp=output_props(ctcf, 'sigmoid'),
                            outputdir=tmpdir.strpath)

    @inputlayer
    @outputdense
    def _cnn_model(inputs, inp, oup, params):
        layer = inputs[list()]
        layer = Complement(1)(layer)
        layer = Reverse()(layer)
        layer = Flatten()(layer)
        output = Dense(params[0])(layer)
        return inputs, output

    with pytest.raises(Exception):
        # due to Wrong type for indexing
        bwm = Janggo.create('dna_ctcf_HepG2-cnn',
                            (_cnn_model, (2,)),
                            inputp=input_props(dna),
                            outputp=output_props(ctcf, 'sigmoid'),
                            outputdir=tmpdir.strpath)

    @inputlayer
    @outputdense
    def _cnn_model(inputs, inp, oup, params):
        layer = inputs()[0]
        layer = Complement(1)(layer)
        layer = Reverse()(layer)
        layer = Flatten()(layer)
        output = Dense(params[0])(layer)
        return inputs, output

    with pytest.raises(Exception):
        # name with dot not allowed. could be mistaken for a file-ending
        bwm = Janggo.create('dna_ctcf_HepG2.cnn',
                            (_cnn_model, (2,)),
                            inputp=input_props(dna),
                            outputp=output_props(ctcf, 'sigmoid'),
                            outputdir=tmpdir.strpath)
    with pytest.raises(Exception):
        # name with must be string
        bwm = Janggo.create(12342134,
                            (_cnn_model, (2,)),
                            inputp=input_props(dna),
                            outputp=output_props(ctcf, 'sigmoid'),
                            outputdir=tmpdir.strpath)

    bwm = Janggo.create('dna_ctcf_HepG2-cnn',
                        (_cnn_model, (2,)),
                        inputp=input_props(dna),
                        outputp=output_props(ctcf, 'sigmoid'),
                        outputdir=tmpdir.strpath)

    @inputlayer
    @outputdense
    def _cnn_model(inputs, inp, oup, params):
        layer = inputs[0]
        layer = Complement(1)(layer)
        layer = Reverse()(layer)
        layer = Flatten()(layer)
        output = Dense(params[0])(layer)
        return inputs, output
    bwm = Janggo.create('dna_ctcf_HepG2-cnn',
                        (_cnn_model, (2,)),
                        inputp=input_props(dna),
                        outputp=output_props(ctcf, 'sigmoid'),
                        outputdir=tmpdir.strpath)

    @inputlayer
    @outputdense
    def _cnn_model(inputs, inp, oup, params):
        layer = inputs['dna']
        layer = Complement(1)(layer)
        layer = Reverse()(layer)
        layer = Flatten()(layer)
        output = Dense(params[0])(layer)
        return inputs, output
    bwm = Janggo.create('dna_ctcf_HepG2-cnn',
                        (_cnn_model, (2,)),
                        inputp=input_props(dna),
                        outputp=output_props(ctcf, 'sigmoid'),
                        outputdir=tmpdir.strpath)
    bwm.compile(optimizer='adadelta', loss='binary_crossentropy')
    storage = bwm._storage_path(bwm.name, outputdir=tmpdir.strpath)

    bwm.save()
    bwm.summary()

    assert os.path.exists(storage)

    Janggo.create_by_name('dna_ctcf_HepG2-cnn', outputdir=tmpdir.strpath)


def test_janggo_instance_conv(tmpdir):
    """Test Janggo creation by shape and name. """
    data_path = pkg_resources.resource_filename('janggo', 'resources/')
    bed_file = os.path.join(data_path, 'regions.bed')

    posfile = os.path.join(data_path, 'positive.bed')

    refgenome = os.path.join(data_path, 'genome.fa')

    dna = DnaDataset.create_from_refgenome('dna', refgenome=refgenome,
                                           storage='ndarray',
                                           regions=bed_file, order=1)

    ctcf = CoverageDataset.create_from_bed(
        "positives",
        bedfiles=posfile,
        regions=bed_file,
        binsize=200, stepsize=50,
        resolution=50,
        flank=0,
        dimmode='all',
        storage='ndarray')

    @inputlayer
    @outputconv
    def _cnn_model(inputs, inp, oup, params):
        with inputs.use('dna') as inlayer:
            layer = inlayer
        layer = Complement(1)(layer)
        layer = Reverse()(layer)
        return inputs, layer

    bwm = Janggo.create('dna_ctcf_HepG2-cnn',
                        (_cnn_model, (2,)),
                        inputp=input_props(dna),
                        outputp=output_props(ctcf, 'sigmoid'),
                        outputdir=tmpdir.strpath)

    bwm.compile(optimizer='adadelta', loss='binary_crossentropy')
    storage = bwm._storage_path(bwm.name, outputdir=tmpdir.strpath)

    bwm.save()
    bwm.summary()

    assert os.path.exists(storage)

    Janggo.create_by_name('dna_ctcf_HepG2-cnn', outputdir=tmpdir.strpath)


def test_janggo_train_predict_option1(tmpdir):
    """Train, predict and evaluate on dummy data.

    create: by_shape
    Input args: Dataset
    generators: NO
    """

    inputs = NumpyDataset("X", np.random.random((1000, 100)))
    outputs = NumpyDataset('y', np.random.randint(2, size=(1000, 1)),
                           samplenames=['random'])

    @inputlayer
    @outputdense
    def test_model(inputs, inp, oup, params):
        return inputs, inputs[0]

    bwm = Janggo.create('nptest',
                        (test_model, None),
                        inputp=input_props(inputs),
                        outputp=output_props(outputs, 'sigmoid'),
                        outputdir=tmpdir.strpath)

    bwm.compile(optimizer='adadelta', loss='binary_crossentropy')

    storage = bwm._storage_path(bwm.name, outputdir=tmpdir.strpath)
    assert not os.path.exists(storage)

    bwm.fit(inputs, outputs, epochs=2, batch_size=32)

    assert os.path.exists(storage)

    pred = bwm.predict(inputs)
    np.testing.assert_equal(len(pred[:, np.newaxis]), len(inputs))
    np.testing.assert_equal(pred.shape, outputs.shape)
    bwm.evaluate(inputs, outputs)


def test_janggo_train_predict_option2(tmpdir):
    """Train, predict and evaluate on dummy data.

    create: NO
    Input args: list(Dataset)
    generators: NO
    """

    inputs = NumpyDataset("x", np.random.random((1000, 100)))
    outputs = NumpyDataset('y', np.random.randint(2, size=(1000, 1)),
                           samplenames=['random'])

    def _model(path):
        inputs = Input((100,), name='x')
        output = Dense(1, activation='sigmoid', name='y')(inputs)
        model = Janggo(inputs=inputs, outputs=output, name='test',
                       outputdir=path)
        model.compile(optimizer='adadelta', loss='binary_crossentropy',
                      metrics=['accuracy'])
        return model

    bwm = _model(tmpdir.strpath)

    storage = bwm._storage_path(bwm.name, outputdir=tmpdir.strpath)
    assert not os.path.exists(storage)

    bwm.fit([inputs], [outputs], epochs=2, batch_size=32)

    assert os.path.exists(storage)

    pred = bwm.predict([inputs])
    np.testing.assert_equal(len(pred[:, np.newaxis]), len(inputs))
    np.testing.assert_equal(pred.shape, outputs.shape)
    bwm.evaluate([inputs], [outputs])


def test_janggo_train_predict_option3(tmpdir):
    """Train, predict and evaluate on dummy data.

    Only works without generators and without evaluators.

    create: NO
    Input args: list(np.array)
    generators: NO
    """

    inputs = np.random.random((1000, 100))
    outputs = np.random.randint(2, size=(1000, 1))

    def _model(path):
        inputs = Input((100,), name='x')
        output = Dense(1, activation='sigmoid')(inputs)
        model = Janggo(inputs=inputs, outputs=output, name='test',
                       outputdir=path)
        model.compile(optimizer='adadelta', loss='binary_crossentropy',
                      metrics=['accuracy'])
        return model

    bwm = _model(tmpdir.strpath)

    storage = bwm._storage_path(bwm.name, outputdir=tmpdir.strpath)
    assert not os.path.exists(storage)

    bwm.fit([inputs], [outputs], epochs=2, batch_size=32)
    with pytest.raises(TypeError):
        bwm.fit([inputs], [outputs], epochs=2, batch_size=32,
                generator=janggo_fit_generator)
    assert os.path.exists(storage)

    pred = bwm.predict([inputs])
    with pytest.raises(TypeError):
        bwm.predict([inputs], batch_size=32,
                    generator=janggo_predict_generator)
    np.testing.assert_equal(len(pred[:, np.newaxis]), len(inputs))
    np.testing.assert_equal(pred.shape, outputs.shape)
    bwm.evaluate([inputs], [outputs])
    with pytest.raises(TypeError):
        bwm.evaluate([inputs], [outputs], batch_size=32,
                     generator=janggo_fit_generator)


def test_janggo_train_predict_option4(tmpdir):
    """Train, predict and evaluate on dummy data.

    Only works without generators and without evaluators.

    create: NO
    Input args: np.array
    generators: YES
    """

    inputs = np.random.random((1000, 100))
    outputs = np.random.randint(2, size=(1000, 1))

    def _model(path):
        inputs = Input((100,), name='x')
        output = Dense(1, activation='sigmoid')(inputs)
        model = Janggo(inputs=inputs, outputs=output, name='test',
                       outputdir=path)
        model.compile(optimizer='adadelta', loss='binary_crossentropy',
                      metrics=['accuracy'])
        return model

    bwm = _model(tmpdir.strpath)

    storage = bwm._storage_path(bwm.name, outputdir=tmpdir.strpath)
    assert not os.path.exists(storage)

    bwm.fit(inputs, outputs, epochs=2, batch_size=32)
    with pytest.raises(TypeError):
        bwm.fit(inputs, outputs, epochs=2, batch_size=32,
                generator=janggo_fit_generator)

    assert os.path.exists(storage)

    pred = bwm.predict(inputs)
    with pytest.raises(TypeError):
        bwm.predict(inputs, batch_size=32,
                    generator=janggo_predict_generator)
    np.testing.assert_equal(len(pred[:, np.newaxis]), len(inputs))
    np.testing.assert_equal(pred.shape, outputs.shape)
    bwm.evaluate(inputs, outputs)
    with pytest.raises(TypeError):
        bwm.evaluate(inputs, outputs, batch_size=32,
                     generator=janggo_fit_generator)


def test_janggo_train_predict_option5(tmpdir):
    """Train, predict and evaluate on dummy data.

    create: NO
    Input args: list(Dataset)
    generators: YES
    """

    inputs = NumpyDataset("x", np.random.random((1000, 100)))
    outputs = NumpyDataset('y', np.random.randint(2, size=(1000, 1)),
                           samplenames=['random'])

    def _model(path):
        inputs = Input((100,), name='x')
        output = Dense(1, name='y', activation='sigmoid')(inputs)
        model = Janggo(inputs=inputs, outputs=output, name='test_model',
                       outputdir=path)
        model.compile(optimizer='adadelta', loss='binary_crossentropy',
                      metrics=['accuracy'])
        return model

    bwm = _model(tmpdir.strpath)

    storage = bwm._storage_path(bwm.name, outputdir=tmpdir.strpath)
    assert not os.path.exists(storage)

    bwm.fit([inputs], [outputs], epochs=2, batch_size=32,
            generator=janggo_fit_generator,
            use_multiprocessing=False)

    assert os.path.exists(storage)

    pred = bwm.predict([inputs], generator=janggo_predict_generator,
                       use_multiprocessing=False)
    np.testing.assert_equal(len(pred[:, np.newaxis]), len(inputs))
    np.testing.assert_equal(pred.shape, outputs.shape)
    bwm.evaluate([inputs], [outputs], generator=janggo_fit_generator,
                 use_multiprocessing=False)

    auc_eval = ScoreEvaluator('auROC', auroc)
    prc_eval = ScoreEvaluator('auPRC', auprc)
    acc_eval = ScoreEvaluator('accuracy', accuracy)
    f1_eval = ScoreEvaluator('F1', f1_score)

    evaluators = EvaluatorList([auc_eval, prc_eval, acc_eval,
                                f1_eval], path=tmpdir.strpath)
    evaluators.evaluate([inputs], outputs, datatags=['validation_set'])

    for file_ in ["auROC.json", "auPRC.json", "accuracy.json", "F1.json"]:
        with open(os.path.join(tmpdir.strpath, "evaluation",
                               file_), 'r') as f:
            # there must be an entry for the model 'nptest'
            assert 'test_model' in json.load(f)


def test_janggo_train_predict_option6(tmpdir):
    """Train, predict and evaluate on dummy data.

    create: NO
    Input args: Dataset
    generators: YES
    """

    inputs = NumpyDataset("x", np.random.random((1000, 100)))
    outputs = NumpyDataset('y', np.random.randint(2, size=(1000, 1)),
                           samplenames=['random'])

    @inputlayer
    @outputdense
    def _model(inputs, inp, oup, params):
        return inputs, inputs[0]

    bwm = Janggo.create('nptest',
                        (_model, None),
                        inputp=input_props(inputs),
                        outputp=output_props(outputs, 'sigmoid'),
                        outputdir=tmpdir.strpath)

    bwm.compile(optimizer='adadelta', loss='binary_crossentropy')

    storage = bwm._storage_path(bwm.name, outputdir=tmpdir.strpath)
    assert not os.path.exists(storage)

    bwm.fit(inputs, outputs, epochs=2, batch_size=32,
            generator=janggo_fit_generator,
            use_multiprocessing=False)

    assert os.path.exists(storage)

    pred = bwm.predict(inputs, generator=janggo_predict_generator,
                       use_multiprocessing=False)
    np.testing.assert_equal(len(pred[:, np.newaxis]), len(inputs))
    np.testing.assert_equal(pred.shape, outputs.shape)
    bwm.evaluate(inputs, outputs, generator=janggo_fit_generator,
                 use_multiprocessing=False)

    auc_eval = ScoreEvaluator('auROC', auroc)
    prc_eval = ScoreEvaluator('auPRC', auprc)
    acc_eval = ScoreEvaluator('accuracy', accuracy)
    f1_eval = ScoreEvaluator('F1', f1_score)

    evaluators = EvaluatorList([auc_eval, prc_eval, acc_eval,
                                f1_eval], path=tmpdir.strpath,
                               model_filter='ptest')

    # first I create fake inputs to provoke dimension
    inputs_wrong_dim = NumpyDataset("x", np.random.random((1000, 50)))
    evaluators.evaluate(inputs_wrong_dim, outputs, datatags=['validation_set'])

    for file_ in ["auROC.json", "auPRC.json", "accuracy.json", "F1.json"]:
        with open(os.path.join(tmpdir.strpath, "evaluation",
                               file_), 'r') as f:
            # the content must be empty at this point, because
            # of mismatching dims. No evaluations were ran.
            assert not json.load(f)

    evaluators.evaluate(inputs, outputs, datatags=['validation_set'])
    evaluators.dump()
    for file_ in ["auROC.json", "auPRC.json", "accuracy.json", "F1.json"]:
        with open(os.path.join(tmpdir.strpath, "evaluation",
                               file_), 'r') as f:
            # there must be an entry for the model 'nptest'
            assert 'nptest' in json.load(f)

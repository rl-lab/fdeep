#!/usr/bin/env python3
"""Generate a test model for frugally-deep.
"""

import numbers
import sys

import numpy as np

import keras
from keras.models import Model, load_model, Sequential
from keras.layers import Input, Dense, Dropout, Flatten, Activation
from keras.layers import Conv1D, ZeroPadding1D, Cropping1D
from keras.layers import Conv2D, ZeroPadding2D, Cropping2D
from keras.layers import MaxPooling1D, AveragePooling1D, UpSampling1D
from keras.layers import MaxPooling2D, AveragePooling2D, UpSampling2D
from keras.layers import GlobalAveragePooling1D, GlobalMaxPooling1D
from keras.layers import GlobalAveragePooling2D, GlobalMaxPooling2D
from keras.layers import SeparableConv2D, DepthwiseConv2D
from keras.layers import LeakyReLU, ELU, PReLU
from keras.layers import BatchNormalization, Concatenate
from keras import backend as K

__author__ = "Tobias Hermann"
__copyright__ = "Copyright 2017, Tobias Hermann"
__license__ = "MIT"
__maintainer__ = "Tobias Hermann, https://github.com/Dobiasd/frugally-deep"
__email__ = "editgym@gmail.com"


def replace_none_with(value, shape):
    """Replace every None with a fixed value."""
    return tuple(list(map(lambda x: x if x is not None else value, shape)))


def get_shape_for_random_data(data_size, shape):
    """Include size of data to generate into shape."""
    if len(shape) == 5:
        return (data_size, shape[0], shape[1], shape[2], shape[3], shape[4])
    if len(shape) == 4:
        return (data_size, shape[0], shape[1], shape[2], shape[3])
    if len(shape) == 3:
        return (data_size, shape[0], shape[1], shape[2])
    if len(shape) == 2:
        return (data_size, shape[0], shape[1])
    if len(shape) == 1:
        return (data_size, shape[0])
    assert False


def generate_random_data(data_size, shape):
    """Random data for training."""
    return np.random.random(
        size=get_shape_for_random_data(data_size, replace_none_with(42, shape)))


def generate_input_data(data_size, input_shapes):
    """Random input data for training."""
    return [generate_random_data(data_size, input_shape)
            for input_shape in input_shapes]


def generate_output_data(data_size, outputs):
    """Random output data for training."""
    return [generate_random_data(data_size, output.shape[1:])
            for output in outputs]


def get_test_model_small():
    """Returns a minimalist test model."""
    input_shapes = [
        (17, 4),
        (16, 18, 3),
        (8,),
        (8,),
        (2, 3, 5),
        (2, 3, 5),
        (32, 32, 3),
        (2, 3, 4, 5),
        (2, 3, 4, 5, 6),
    ]

    inputs = [Input(shape=s) for s in input_shapes]

    outputs = []

    outputs.append(Dense(3)(inputs[2]))
    outputs.append(Dense(3)(inputs[0]))
    outputs.append(Dense(3)(inputs[1]))
    outputs.append(Dense(3)(inputs[7]))

    outputs.append(Flatten()(inputs[0]))
    outputs.append(Flatten()(inputs[1]))
    outputs.append(Flatten()(inputs[7]))
    outputs.append(Flatten()(inputs[8]))

    outputs.append(Activation('sigmoid')(inputs[7]))
    outputs.append(Activation('sigmoid')(inputs[8]))

    # same as axis=-1
    outputs.append(Concatenate()([inputs[4], inputs[5]]))
    outputs.append(Concatenate(axis=3)([inputs[4], inputs[5]]))
    # axis=0 does not make sense, since dimension 0 is the batch dimension
    outputs.append(Concatenate(axis=1)([inputs[4], inputs[5]]))
    outputs.append(Concatenate(axis=2)([inputs[4], inputs[5]]))

    outputs.append(PReLU()(inputs[0]))
    outputs.append(PReLU()(inputs[1]))
    outputs.append(PReLU()(inputs[2]))
    outputs.append(PReLU(shared_axes=[1, 2])(inputs[1]))
    outputs.append(PReLU(shared_axes=[1, 3])(inputs[1]))
    outputs.append(PReLU(shared_axes=[2, 3])(inputs[1]))
    outputs.append(PReLU(shared_axes=[1, 2, 3])(inputs[1]))
    outputs.append(PReLU(shared_axes=[1])(inputs[1]))
    outputs.append(PReLU(shared_axes=[2])(inputs[1]))
    outputs.append(PReLU(shared_axes=[3])(inputs[1]))

    outputs.append(PReLU()(Conv2D(8, (3, 3), padding='same',
                                  activation='elu')(inputs[6])))

    outputs.append(GlobalMaxPooling2D()(inputs[1]))
    outputs.append(MaxPooling2D()(inputs[1]))
    outputs.append(AveragePooling1D()(inputs[0]))

    outputs.append(Conv1D(2, 3)(inputs[0]))

    outputs.append(BatchNormalization()(inputs[0]))
    outputs.append(BatchNormalization(center=False)(inputs[0]))
    outputs.append(BatchNormalization(scale=False)(inputs[0]))

    outputs.append(Conv2D(2, (3, 3), use_bias=True)(inputs[1]))
    outputs.append(Conv2D(2, (3, 3), use_bias=False)(inputs[1]))
    outputs.append(SeparableConv2D(2, (3, 3), use_bias=True)(inputs[1]))
    outputs.append(SeparableConv2D(2, (3, 3), use_bias=False)(inputs[1]))
    outputs.append(DepthwiseConv2D(2, (3, 3), use_bias=True)(inputs[1]))
    outputs.append(DepthwiseConv2D(2, (3, 3), use_bias=False)(inputs[1]))

    model = Model(inputs=inputs, outputs=outputs, name='test_model_small')
    model.compile(loss='mse', optimizer='nadam')

    # fit to dummy data
    training_data_size = 1
    data_in = generate_input_data(training_data_size, input_shapes)
    initial_data_out = model.predict(data_in)
    data_out = generate_output_data(training_data_size, initial_data_out)
    model.fit(data_in, data_out, epochs=10)
    return model


def get_test_model_variable():
    """Returns a small model for variably shaped input tensors."""

    input_shapes = [
        (None, None, 1),
        (None, None, 3),
        (None, 4),
    ]

    inputs = [Input(shape=s) for s in input_shapes]

    outputs = []

    # same as axis=-1
    outputs.append(Concatenate()([inputs[0], inputs[1]]))
    outputs.append(Conv2D(8, (3, 3), padding='same', activation='elu')(inputs[0]))
    outputs.append(Conv2D(8, (3, 3), padding='same', activation='relu')(inputs[1]))
    outputs.append(GlobalMaxPooling2D()(inputs[0]))
    outputs.append(MaxPooling2D()(inputs[1]))
    outputs.append(AveragePooling1D()(inputs[2]))

    outputs.append(PReLU(shared_axes=[1, 2])(inputs[0]))
    outputs.append(PReLU(shared_axes=[1, 2])(inputs[1]))
    outputs.append(PReLU(shared_axes=[1, 2, 3])(inputs[1]))
    outputs.append(PReLU(shared_axes=[1])(inputs[2]))

    model = Model(inputs=inputs, outputs=outputs, name='test_model_variable')
    model.compile(loss='mse', optimizer='nadam')

    # fit to dummy data
    training_data_size = 1
    data_in = generate_input_data(training_data_size, input_shapes)
    initial_data_out = model.predict(data_in)
    data_out = generate_output_data(training_data_size, initial_data_out)
    model.fit(data_in, data_out, epochs=10)
    return model


def get_test_model_sequential():
    """Returns a typical (VGG-like) sequential test model."""
    model = Sequential()
    model.add(Conv2D(8, (3, 3), activation='relu', input_shape=(32, 32, 3)))
    model.add(Conv2D(8, (3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))

    model.add(Conv2D(16, (3, 3), activation='elu'))
    model.add(Conv2D(16, (3, 3)))
    model.add(ELU())

    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))

    model.add(Flatten())
    model.add(Dense(64, activation='sigmoid'))
    model.add(Dropout(0.5))
    model.add(Dense(10, activation='softmax'))

    model.compile(loss='categorical_crossentropy', optimizer='sgd')

    # fit to dummy data
    training_data_size = 1
    data_in = [np.random.random(size=(training_data_size, 32, 32, 3))]
    data_out = [np.random.random(size=(training_data_size, 10))]
    model.fit(data_in, data_out, epochs=10)
    return model


def get_test_model_full():
    """Returns a maximally complex test model,
    using all supported layer types with different parameter combination.
    """
    input_shapes = [
        (26, 28, 3),
        (4, 4, 3),
        (4, 4, 3),
        (4,),
        (2, 3),
        (27, 29, 1),
        (17, 1),
        (17, 4),
        (2, 3),
        (2, 3, 4, 5),
        (2, 3, 4, 5, 6),
    ]

    inputs = [Input(shape=s) for s in input_shapes]

    outputs = []

    outputs.append(Flatten()(inputs[3]))
    outputs.append(Flatten()(inputs[4]))
    outputs.append(Flatten()(inputs[5]))
    outputs.append(Flatten()(inputs[9]))
    outputs.append(Flatten()(inputs[10]))

    for inp in inputs[6:8]:
        for padding in ['valid', 'same']:
            for s in range(1, 6):
                for out_channels in [1, 2]:
                    for d in range(1, 4):
                        outputs.append(
                            Conv1D(out_channels, s, padding=padding,
                                   dilation_rate=d)(inp))
        for padding_size in range(0, 5):
            outputs.append(ZeroPadding1D(padding_size)(inp))
        for crop_left in range(0, 2):
            for crop_right in range(0, 2):
                outputs.append(Cropping1D((crop_left, crop_right))(inp))
        for upsampling_factor in range(1, 5):
            outputs.append(UpSampling1D(upsampling_factor)(inp))
        for padding in ['valid', 'same']:
            for pool_factor in range(1, 6):
                for s in range(1, 4):
                    outputs.append(
                        MaxPooling1D(pool_factor, strides=s,
                                     padding=padding)(inp))
                    outputs.append(
                        AveragePooling1D(pool_factor, strides=s,
                                         padding=padding)(inp))
        outputs.append(GlobalMaxPooling1D()(inp))
        outputs.append(GlobalAveragePooling1D()(inp))

    for inp in [inputs[0], inputs[5]]:
        for padding in ['valid', 'same']:
            for h in range(1, 6):
                for out_channels in [1, 2]:
                    for d in range(1, 4):
                        outputs.append(
                            Conv2D(out_channels, (h, 1), padding=padding,
                                   dilation_rate=(d, 1))(inp))
                        outputs.append(
                            SeparableConv2D(out_channels, (h, 1), padding=padding,
                                   dilation_rate=(d, 1))(inp))
                    for sy in range(1, 4):
                        outputs.append(
                            Conv2D(out_channels, (h, 1), strides=(1, sy),
                                   padding=padding)(inp))
                        outputs.append(
                            SeparableConv2D(out_channels, (h, 1),
                                            strides=(sy, sy),
                                            padding=padding)(inp))
                for sy in range(1, 4):
                    outputs.append(
                        DepthwiseConv2D((h, 1),
                                        strides=(sy, sy),
                                        padding=padding)(inp))
                    outputs.append(
                        MaxPooling2D((h, 1), strides=(1, sy),
                                     padding=padding)(inp))
            for w in range(1, 6):
                for out_channels in [1, 2]:
                    for d in range(1, 4) if sy == 1 else [1]:
                        outputs.append(
                            Conv2D(out_channels, (1, w), padding=padding,
                                   dilation_rate=(1, d))(inp))
                        outputs.append(
                            SeparableConv2D(out_channels, (1, w), padding=padding,
                                   dilation_rate=(1, d))(inp))
                    for sx in range(1, 4):
                        outputs.append(
                            Conv2D(out_channels, (1, w), strides=(sx, 1),
                                   padding=padding)(inp))
                        outputs.append(
                            SeparableConv2D(out_channels, (1, w),
                                            strides=(sx, sx),
                                            padding=padding)(inp))
                for sx in range(1, 4):
                    outputs.append(
                        DepthwiseConv2D((1, w),
                                        strides=(sy, sy),
                                        padding=padding)(inp))
                    outputs.append(
                        MaxPooling2D((1, w), strides=(1, sx),
                                     padding=padding)(inp))
    outputs.append(ZeroPadding2D(2)(inputs[0]))
    outputs.append(ZeroPadding2D((2, 3))(inputs[0]))
    outputs.append(ZeroPadding2D(((1, 2), (3, 4)))(inputs[0]))
    outputs.append(Cropping2D(2)(inputs[0]))
    outputs.append(Cropping2D((2, 3))(inputs[0]))
    outputs.append(Cropping2D(((1, 2), (3, 4)))(inputs[0]))
    for y in range(1, 3):
        for x in range(1, 3):
            outputs.append(UpSampling2D(size=(y, x))(inputs[0]))
    outputs.append(GlobalAveragePooling2D()(inputs[0]))
    outputs.append(GlobalMaxPooling2D()(inputs[0]))
    outputs.append(AveragePooling2D((2, 2))(inputs[0]))
    outputs.append(MaxPooling2D((2, 2))(inputs[0]))
    outputs.append(UpSampling2D((2, 2))(inputs[0]))
    outputs.append(Dropout(0.5)(inputs[0]))

    # same as axis=-1
    outputs.append(Concatenate()([inputs[1], inputs[2]]))
    outputs.append(Concatenate(axis=3)([inputs[1], inputs[2]]))
    # axis=0 does not make sense, since dimension 0 is the batch dimension
    outputs.append(Concatenate(axis=1)([inputs[1], inputs[2]]))
    outputs.append(Concatenate(axis=2)([inputs[1], inputs[2]]))

    outputs.append(BatchNormalization()(inputs[0]))
    outputs.append(BatchNormalization(center=False)(inputs[0]))
    outputs.append(BatchNormalization(scale=False)(inputs[0]))

    outputs.append(Conv2D(2, (3, 3), use_bias=True)(inputs[0]))
    outputs.append(Conv2D(2, (3, 3), use_bias=False)(inputs[0]))
    outputs.append(SeparableConv2D(2, (3, 3), use_bias=True)(inputs[0]))
    outputs.append(SeparableConv2D(2, (3, 3), use_bias=False)(inputs[0]))
    outputs.append(DepthwiseConv2D(2, (3, 3), use_bias=True)(inputs[0]))
    outputs.append(DepthwiseConv2D(2, (3, 3), use_bias=False)(inputs[0]))

    outputs.append(Dense(2, use_bias=True)(inputs[3]))
    outputs.append(Dense(2, use_bias=False)(inputs[3]))

    shared_conv = Conv2D(1, (1, 1),
                         padding='valid', name='shared_conv', activation='relu')

    up_scale_2 = UpSampling2D((2, 2))
    x1 = shared_conv(up_scale_2(inputs[1]))  # (1, 8, 8)
    x2 = shared_conv(up_scale_2(inputs[2]))  # (1, 8, 8)
    x3 = Conv2D(1, (1, 1), padding='valid')(up_scale_2(inputs[2]))  # (1, 8, 8)
    x = Concatenate()([x1, x2, x3])  # (3, 8, 8)
    outputs.append(x)

    x = Conv2D(3, (1, 1), padding='same', use_bias=False)(x)  # (3, 8, 8)
    outputs.append(x)
    x = Dropout(0.5)(x)
    outputs.append(x)
    x = Concatenate()([
        MaxPooling2D((2, 2))(x),
        AveragePooling2D((2, 2))(x)])  # (6, 4, 4)
    outputs.append(x)

    x = Flatten()(x)  # (1, 1, 96)
    x = Dense(4, use_bias=False)(x)
    outputs.append(x)
    x = Dense(3)(x)  # (1, 1, 3)
    outputs.append(x)

    outputs.append(keras.layers.Add()([inputs[4], inputs[8], inputs[8]]))
    outputs.append(keras.layers.Subtract()([inputs[4], inputs[8]]))
    outputs.append(keras.layers.Multiply()([inputs[4], inputs[8], inputs[8]]))
    outputs.append(keras.layers.Average()([inputs[4], inputs[8], inputs[8]]))
    outputs.append(keras.layers.Maximum()([inputs[4], inputs[8], inputs[8]]))
    outputs.append(Concatenate()([inputs[4], inputs[8], inputs[8]]))

    intermediate_input_shape = (3,)
    intermediate_in = Input(intermediate_input_shape)
    intermediate_x = intermediate_in
    intermediate_x = Dense(8)(intermediate_x)
    intermediate_x = Dense(5)(intermediate_x)
    intermediate_model = Model(
        inputs=[intermediate_in], outputs=[intermediate_x],
        name='intermediate_model')
    intermediate_model.compile(loss='mse', optimizer='nadam')

    x = intermediate_model(x)  # (1, 1, 5)

    intermediate_model_2 = Sequential()
    intermediate_model_2.add(Dense(7, input_shape=(5,)))
    intermediate_model_2.add(Dense(5))
    intermediate_model_2.compile(optimizer='rmsprop',
                                 loss='categorical_crossentropy')

    x = intermediate_model_2(x)  # (1, 1, 5)

    x = Dense(3)(x)  # (1, 1, 3)

    shared_activation = Activation('tanh')

    outputs = outputs + [
        Activation('tanh')(inputs[3]),
        Activation('hard_sigmoid')(inputs[3]),
        Activation('selu')(inputs[3]),
        Activation('sigmoid')(inputs[3]),
        Activation('softplus')(inputs[3]),
        Activation('softmax')(inputs[3]),
        Activation('relu')(inputs[3]),
        LeakyReLU()(inputs[3]),
        ELU()(inputs[3]),
        PReLU()(inputs[2]),
        PReLU()(inputs[3]),
        PReLU()(inputs[4]),
        shared_activation(inputs[3]),
        Activation('linear')(inputs[4]),
        Activation('linear')(inputs[1]),
        x,
        shared_activation(x),
    ]

    print('Model has {} outputs.'.format(len(outputs)))

    model = Model(inputs=inputs, outputs=outputs, name='test_model_full')
    model.compile(loss='mse', optimizer='nadam')

    # fit to dummy data
    training_data_size = 1
    batch_size = 1
    epochs = 10
    data_in = generate_input_data(training_data_size, input_shapes)
    initial_data_out = model.predict(data_in)
    data_out = generate_output_data(training_data_size, initial_data_out)
    model.fit(data_in, data_out, epochs=epochs, batch_size=batch_size)
    return model


def main():
    """Generate different test models and save them to the given directory."""
    if len(sys.argv) != 3:
        print('usage: [model name] [destination file path]')
        sys.exit(1)
    else:
        model_name = sys.argv[1]
        dest_path = sys.argv[2]

        get_model_functions = {
            'small': get_test_model_small,
            'variable': get_test_model_variable,
            'sequential': get_test_model_sequential,
            'full': get_test_model_full
        }

        if not model_name in get_model_functions:
            print('unknown model name: ', model_name)
            sys.exit(2)

        assert K.backend() == "tensorflow"
        assert K.floatx() == "float32"
        assert K.image_data_format() == 'channels_last'

        np.random.seed(0)

        model_func = get_model_functions[model_name]
        model = model_func()
        model.save(dest_path, include_optimizer=False)

        # Make sure models can be loaded again,
        # see https://github.com/fchollet/keras/issues/7682
        model = load_model(dest_path)
        print(model.summary())

if __name__ == "__main__":
    main()

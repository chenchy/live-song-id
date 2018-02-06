import numpy as np

import keras
keras.backend.set_image_data_format("channels_first")

from keras.models import Sequential
from keras.layers import Conv2D


def build_model(pca_matrix, query_shape, delta=16):
    """Generate the convolution model.
        pca_matrix: 3D array (each 2D subarray is a kernel)
        query_shape: tuple
        batch_size: int
        delta: int
    """
    num_pca, pca_width, pca_height = pca_matrix.shape
    query_width, query_height = query_shape
    assert pca_height == query_height, (pca_height, query_height)

    pca_ker = np.moveaxis(pca_matrix, 0, -1)
    pca_ker = pca_ker.reshape(pca_ker.shape[:2] + (1,) + pca_ker.shape[2:])
    def pca_ker_init(shape, dtype=None):
        assert pca_ker.shape == shape, (pca_ker.shape, shape)
        return pca_ker

    delta_vec = np.zeros(delta+1)
    delta_vec[0] = 1
    delta_vec[-1] = -1

    delta_width, = delta_vec.shape
    delta_matrix = delta_vec.reshape((delta_width, 1))

    delta_ker = np.stack([delta_matrix for i in range(num_pca)], axis=-1)
    delta_ker = delta_ker.reshape(delta_ker.shape + (1,))
    def delta_ker_init(shape, dtype=None):
        assert delta_ker.shape == shape, (delta_ker.shape, shape)
        return delta_ker

    return Sequential([
        Conv2D(
            input_shape=(1, query_width, query_height),
            filters=num_pca,
            kernel_size=(pca_width, pca_height),
            kernel_initializer=pca_ker_init,
            use_bias=False,
            padding="valid",
        ),
        Conv2D(
            filters=1,
            kernel_size=(delta_width, 1),
            kernel_initializer=delta_ker_init,
            use_bias=False,
            padding="valid",
        ),
    ])


def run_model(model, queries_matrix, threshold=0):
    """Run the convolution model.
        model: result of build_model
        queries_matrix: 3D array (each 2D subarray is a query)
        batch_size: int
        threshold: float
    """
    batch_size, query_width, query_height = queries_matrix.shape

    conv_result = model.predict(
        queries_matrix.reshape((batch_size, 1, query_width, query_height)),
        batch_size=batch_size,
    )

    assert conv_result.shape[:2] == (batch_size, 1), (conv_result.shape[:2], (batch_size, 1))
    assert conv_result.shape[3:] == (1,), (conv_result.shape[3:], (1,))
    conv_result = conv_result.reshape((batch_size, conv_result.shape[2]))

    return np.where(conv_result > threshold, 1, 0)


if __name__ == "__main__":
    delta = 1
    num_pca = 5
    pca_time = 4
    pca_height = 10
    query_time = 8
    batch_size = 6

    pca_matrix = np.ones((num_pca, pca_time, pca_height))
    query_shape = (query_time, pca_height)
    queries_matrix = np.ones((batch_size, query_time, pca_height))

    model = build_model(pca_matrix, query_shape, delta)
    result = run_model(model, queries_matrix)

    assert result.shape[0] == batch_size
    print(result.shape)

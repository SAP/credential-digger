import logging
import os

import numpy as np
# In order not to raise tensorflow warnings, we need to set this environment
# variable before importing the `tensorflow` package
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
import tensorflow.keras.preprocessing.text
import tensorflow_hub as hub
import tensorflow_text


def build_embedding_model():
    """ Build model by stacking up a preprocessing layer
    and an encoding layer.

    Returns
    -------
    tf.keras.Model
         The embedding model, taking a list of strings as input,
         and outputting embeddings for each token of the input strings
    """
    # Links for the pre-trained TensorFlow Hub preprocessing
    # and encoding layers
    tfhub_preprocessing = 'https://tfhub.dev/tensorflow/' \
                          'bert_en_uncased_preprocess/3'
    tfhub_encoder = 'https://tfhub.dev/tensorflow/small_bert/' \
                    'bert_en_uncased_L-2_H-128_A-2/1'
    # Define model input type and name
    inputs = tf.keras.layers.Input(shape=(), dtype=tf.string, name='snippet')
    # Define preprocessing layer
    preprocessing_layer = hub.KerasLayer(tfhub_preprocessing,
                                         name='preprocessing')
    # Define encoding layer
    encoder = hub.KerasLayer(tfhub_encoder,
                             trainable=True, name='BERT_encoder')
    # Stack up the three layers
    outputs = encoder(preprocessing_layer(inputs))
    # Retrieve token embeddings i.e. the 'sequence_output' values
    model_outputs = outputs['sequence_output']
    # Return model
    return tf.keras.Model(inputs, model_outputs)


def compute_snippet_embedding(snippet, model):
    """ Compute snippet embedding.

    Parameters
    ----------
    snippet: str
        The snippet to get the embedding of
    model: tf.keras.Model
        The built embedding model

    Returns
    -------
    list
        The 128 element embedding for the input snippet
    """
    # Preprocess snippet
    preprocessed_snippet = snippet.replace('\'', '"')
    # Compute snippet's token embeddings
    small_bert_result = tf.squeeze(model(tf.constant([preprocessed_snippet])))
    small_bert_embeddings = small_bert_result.numpy()
    # Compute snippet's embedding as mean of token embeddings
    snippet_embedding = np.mean(small_bert_embeddings, axis=0)
    return snippet_embedding.tolist()


def compute_similarity(embedding_1, embedding_2):
    """ Compute the cosine similarity of two snippets' embeddings.

    Parameters
    ----------
    embedding_1: list
        First snippet embedding
    embedding_2: list
        Second snippet embedding

    Returns
    -------
    float
        The cosine similariy: value between 0 and 1.
        The greater the value, the more similar the snippets
    """
    # The cosine similarity is computed using the dot product
    # of the two embedding vectors over the product of their norms
    arr_1 = np.array(embedding_1)
    arr_2 = np.array(embedding_2)
    cos_sim = np.dot(arr_1, arr_2) / (np.linalg.norm(arr_1) *
                                      np.linalg.norm(arr_2))
    return cos_sim

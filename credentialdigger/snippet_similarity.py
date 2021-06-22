import logging
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_text
import tensorflow.keras.preprocessing.text

logging.getLogger('tensorflow').setLevel(logging.ERROR)


def build_embedding_model():
    """ Build model by stacking up a preprocessing layer
    and an encoding layer.

    Returns
    -------
    tf.keras.Model
         The embedding model, taking a list of strings as input,
         and outputting embeddings for each token of the input strings
    """

    # Links for the pre-trained TensorFlow Hub preprocessing and encoding
    # layers
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
    np.array
        The 128 element embedding for the input snippet
    """

    # Compute snippet's token embeddings
    small_bert_result = tf.squeeze(model(tf.constant([snippet])))
    small_bert_embeddings = small_bert_result.numpy()
    # Compute snippet's embedding as the mean of the token embeddings
    snippet_embedding = np.mean(small_bert_embeddings, axis=0)
    return snippet_embedding


def compute_similarity(emb_1, emb_2):
    """ Compute the cosine similarity of two snippets' embeddings.

    Parameters
    ----------
    emb_1: np.array
        first snippet embedding
    emb_2: np.array
        second snippet embedding

    Returns
    -------
    double
        The cosine similariy: value between 0 and 1.
        The greater the value, the more similar the snippets
    """

    # The cosine similarity is computed using the dot product of the two
    # embedding vectors over the product of their norms
    cos_sim = np.dot(emb_1, emb_2) / (np.linalg.norm(emb_1) *
                                      np.linalg.norm(emb_2))
    return cos_sim

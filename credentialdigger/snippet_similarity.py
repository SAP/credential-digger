import tensorflow as tf
import tensorflow_text
import logging
import tensorflow_hub as hub
import tensorflow.keras.preprocessing.text
import numpy as np

logging.getLogger('tensorflow').setLevel(logging.ERROR)


def build_embedding_model():
    tfhub_handle_preprocess = 'https://tfhub.dev/tensorflow/' \
                              'bert_en_uncased_preprocess/3'
    tfhub_handle_encoder = 'https://tfhub.dev/tensorflow/small_bert/' \
                           'bert_en_uncased_L-2_H-128_A-2/1'

    text_input = tf.keras.layers.Input(shape=(), dtype=tf.string, name='text')
    preprocessing_layer = hub.KerasLayer(tfhub_handle_preprocess,
                                         name='preprocessing')
    encoder_inputs = preprocessing_layer(text_input)
    encoder = hub.KerasLayer(tfhub_handle_encoder,
                             trainable=True, name='BERT_encoder')
    outputs = encoder(encoder_inputs)

    return tf.keras.Model(text_input, outputs['sequence_output'])


def compute_snippet_embedding(snippet, model):
    small_bert_result = tf.squeeze(model(tf.constant(snippet)))
    small_bert_embeddings = small_bert_result.numpy()
    snippet_embedding = np.mean(small_bert_embeddings, axis=0)
    return snippet_embedding


def compute_similarity(emb_1, emb_2):
    cos_sim = np.dot(emb_1, emb_2) / (np.linalg.norm(emb_1) *
                                      np.linalg.norm(emb_2))
    return cos_sim

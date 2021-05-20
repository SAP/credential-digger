import tensorflow as tf
import tensorflow_text
import logging
import tensorflow_hub as hub
import tensorflow.keras.preprocessing.text
import numpy as np

logging.getLogger('tensorflow').setLevel(logging.ERROR)


def build_embedding_model():
    bert_model_name = 'small_bert/bert_en_uncased_L-2_H-128_A-2'
    map_name_to_handle = {'small_bert/bert_en_uncased_L-2_H-128_A-2':
                          'https://tfhub.dev/tensorflow/small_bert/'
                          'bert_en_uncased_L-2_H-128_A-2/1'}
    map_model_to_preprocess = {'small_bert/bert_en_uncased_L-2_H-128_A-2':
                               'https://tfhub.dev/tensorflow/'
                               'bert_en_uncased_preprocess/3'}
    tfhub_handle_encoder = map_name_to_handle[bert_model_name]
    tfhub_handle_preprocess = map_model_to_preprocess[bert_model_name]

    text_input = tf.keras.layers.Input(shape=(), dtype=tf.string, name='text')
    preprocessing_layer = hub.KerasLayer(tfhub_handle_preprocess,
                                         name='preprocessing')
    encoder_inputs = preprocessing_layer(text_input)
    encoder = hub.KerasLayer(tfhub_handle_encoder,
                             trainable=True, name='BERT_encoder')
    outputs = encoder(encoder_inputs)

    return tf.keras.Model(text_input, outputs['sequence_output'])


def compute_snippet_embedding(snippet, model):
    bert_raw_result = tf.squeeze(model(tf.constant(snippet)))
    small_bert_embeddings = bert_raw_result.numpy()
    snippet_embedding = np.mean(small_bert_embeddings, axis=0)
    return snippet_embedding


def compute_similarity(snippet_embedd_1, snippet_embedd_2):
    cos_sim = np.dot(snippet_embedd_1, snippet_embedd_2) / \
            (np.linalg.norm(snippet_embedd_1) *
            np.linalg.norm(snippet_embedd_2))
    return cos_sim

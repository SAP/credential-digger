from collections import Counter

import numpy as np

KEYWORDS = ['do', 'else-if', 'if', 'else', 'switch', 'for',
            'while', 'func', 'return', 'async']


def word_unigram_tf(snippet):
    """ Compute the list of words with their associated occurences in a given
    snippet.

    Parameters
    ----------
    snippet: string
        The snippet to be analyzed

    Returns
    -------
    dict
        The word unigram occurences (sorted)
    """
    term_frequency = {}
    # Extract words from the snippet
    words = []
    word = ''
    for c in list(str(snippet)):
        if c.isalnum():
            word += c
        else:
            words.append(word)
            word = ''
    words = list(filter(None, words))

    # Count occurrences of words
    term_frequency = Counter(words)
    # Return sorted counter
    return dict(term_frequency.most_common())


def compute_vector(snippet, corpus_word_unigram):
    """ Compute the vector of stylometry features.

    Parameters
    ----------
    snippet: string
        A corpus of code, to compute the a code-stylometry vector
    corpus_word_unigram: dict
        The corpus of word occurences in all the selected extracts

    Returns
    -------
    `numpy.array`
        The stylometry vector
    """
    word_unigram_snippet = word_unigram_tf(snippet)
    word_tokens = len(corpus_word_unigram)
    file_length = len(snippet)

    word_occ = _word_occurences(corpus_word_unigram, word_unigram_snippet)

    # Parameters
    key_words_occurences, key_words_used = _keyword_occurences(
        snippet, file_length)
    num_tokens = _num_tokens(word_tokens, file_length)
    num_comments_results = _num_comments(snippet) / file_length
    num_literals = _num_literals(snippet, file_length)
    avg_line_length = _avg_line_length(snippet)
    std_line_length = _std_line_length(snippet)
    num_space = _num_space(snippet, file_length)
    white_space_ratio = _white_space_ratio(snippet, num_space, file_length)
    special_characters = _compute_special_characters(snippet, file_length)

    return np.array(word_occ + [
        key_words_occurences,
        key_words_used,
        num_tokens,
        num_literals,
        num_comments_results,
        avg_line_length,
        std_line_length,
        num_space,
        white_space_ratio
    ] + special_characters)


def _keyword_occurences(snippet, file_length):
    """ Compute the occurences of defined keywords.

    Parameters
    ----------
    snippet: string
        The snippet to be analyzed
    file_length: int
        The lenght of the file in characters

    Returns
    -------
    dict
        The occurences of keywords
    """
    occurences = 0
    keywords_used = 0
    for kw in KEYWORDS:
        occurences += snippet.count(kw)
        keywords_used += 1
    return (np.log(occurences + 1) / file_length,
            np.log(keywords_used + 1) / file_length)


def _num_tokens(word_tokens, file_length):
    return word_tokens / file_length


def _num_comments(snippet):
    return np.log(snippet.count('//') + snippet.count('#') + 1)


def _num_literals(snippet, file_length):
    return len([c for c in snippet if c.isalnum()]) / file_length


def _avg_line_length(snippet):
    return np.mean([len(c) for c in snippet.split('\n')])


def _std_line_length(snippet):
    return np.std([len(c) for c in snippet.split('\n')])


def _num_space(snippet, file_length):
    return np.log(snippet.count(' ') + 1) / file_length


def _white_space_ratio(snippet, num_space, file_length):
    return np.log(snippet.count('\n') + snippet.count(' ') + 1) / (
        file_length - num_space)


def _compute_special_characters(snippet, file_length):
    return [
        np.log(snippet.count('_') + 1) / file_length,
        np.log(snippet.count('=') + 1) / file_length,
        np.log(snippet.count(':') + 1) / file_length,
        np.log(snippet.count('(') + 1) / file_length,
        np.log(snippet.count(')') + 1) / file_length,
        np.log(snippet.count('{') + 1) / file_length,
        np.log(snippet.count('}') + 1) / file_length,
        np.log(snippet.count('$') + 1) / file_length
    ]


def _word_occurences(corpus_word_unigram, word_unigram_snippet):
    output = []
    other = 0
    for key in corpus_word_unigram:
        if key in word_unigram_snippet:
            output.append(word_unigram_snippet[key])
        else:
            output.append(0)
            other += corpus_word_unigram[key]
    output.append(other)
    return output

def create_ngram_set(input_list, ngram_value=2):
    """
    Extract a set of n-grams from a list of integers.

    >>> create_ngram_set([1, 4, 9, 4, 1, 4], ngram_value=2)
    {(4, 9), (4, 1), (1, 4), (9, 4)}

    >>> create_ngram_set([1, 4, 9, 4, 1, 4], ngram_value=3)
    [(1, 4, 9), (4, 9, 4), (9, 4, 1), (4, 1, 4)]
    """
    return set(zip(*[input_list[i:] for i in range(ngram_value)]))


def preprocess_keras_input(input, char_ngrams=3, word_ngrams=2):
    word_pairs = create_ngram_set(input, word_ngrams)
    ngrams = []
    for tpl in word_pairs:
        tpl_str = "<"
        for wrd in tpl:
            tpl_str += str(wrd) + " "
        tpl_str = tpl_str[:-1]
        tpl_str += ">"
        ngrams.append(tpl_str)
    for word in input:
        word = "<" + str(word) + ">"
        ngrams.append(word)
        chars = list(word)
        grams = create_ngram_set(chars, char_ngrams)
        for gram in grams:
            ngrams.append(''.join(gram))
    return ngrams
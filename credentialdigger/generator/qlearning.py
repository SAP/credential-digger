import copy
import random

import numpy as np
from rich.progress import Progress
from sklearn.metrics.pairwise import cosine_similarity

from .stylometry import compute_vector, word_unigram_tf
from .transform import (build_dummy_dict, choose_applicable_transformation,
                        generate_data, get_all_applicable_transformations,
                        get_patterns, get_transformation_id,
                        run_transformation)


def compute_dataset(corpus, actions_n, states_n, alpha, gamma, epochs_basis=50,
                    extract_max_length=150):
    """ Compute a training dataset for the SnippetModel using Q-Learning.

    The process is the following.
    For each index from 0 to num of patterns:
    - select a random extract
    - remove this extract from the corpus
    - truncate the extract, if it is too long
    - update the epochs (higher for more complex patterns)
    - call _optimal_transformation
    - generate a fake extract and add it to the dataset

    Parameters
    ----------
    corpus: list
        The corpus of a repository
    actions_n: int
        The number of actions in the Q-table
    states_n: int
        The number of states in the Q-table
    alpha: float
        The alpha parameter in the reward function
    gamma: float
        The gamma parameter in the reward function
    epochs_basis: int, optional
        The base number of epochs (default `50`)
    extract_max_length: int, optional
        The maximum length of extracts for being processed (default `150`)

    Returns
    -------
    list
        List of dictionaries. Each dictionary is a modified pattern, that
        contains the transformed pattern itself, together with a key-value
        couple.
    """
    # The word unigram dict of a corpus, containing the occurences of
    # individual words
    corpus_word_unigram = word_unigram_tf('\n'.join(corpus))
    args = {
        'actions_n': actions_n,
        'states_n': states_n,
        'alpha': alpha,
        'gamma': gamma,
        'epochs': 1,
        'corpus_word_unigram': corpus_word_unigram
    }

    # Number of patterns
    all_patterns = get_patterns()

    # The number of extracts must be greater (or equal) than the number of
    # patterns, otherwise we don't have enough data for the Q-Learning
    if len(all_patterns) > len(corpus):
        raise ValueError('There are too many patterns for this corpus.')

    dataset = []

    with Progress() as progress:
        patterns_count = len(all_patterns)
        qlearn_task = progress.add_task('Apply Q-learning to patterns...',
                                        total=patterns_count)
        # Apply Q-learning for each pattern
        for pattern_index in range(patterns_count):
            # Select a random extract and remove it from the corpus
            reference_extract = corpus.pop(random.randrange(len(corpus)))
            # Cut extracts too long
            reference_extract = reference_extract[:extract_max_length]

            # Increase epochs for more complex patterns
            epochs = int(epochs_basis *
                         (1 + (pattern_index / patterns_count)))
            # Update epochs in args
            args['epochs'] = epochs

            # Compute the optimal modifications to the basic patterns
            final_transformation, modification_dict = _optimal_transformation(
                reference_extract, all_patterns[pattern_index], args)

            # Generate the dataset, with optimal transformations
            for i in range(epochs):
                dataset += generate_data(all_patterns[pattern_index],
                                         modification_dict)
            progress.update(qlearn_task, advance=1)
    return dataset


def _optimal_transformation(reference_extract, reference_pattern, args):
    """ Compute the Q-learning algorithm.

    Parameters
    ----------
    reference_extract: string
        An extract from the corpus, where we will insert the pattern
    reference_pattern: dict
        The pattern used for the transformations
    arguments: dict
        Parameters to be used for the Q-Learning

    Returns
    -------
    string
        The pattern after a certain number of transformations
    dict
        The dictionary containing the values used to replace the keywords in
        the pattern
    """
    # Initialize the Q-table
    Q = np.zeros([args['states_n'], args['actions_n']])
    # Compute the stylometry of the extract
    reference_stylometry = compute_vector(reference_extract,
                                          args['corpus_word_unigram'])

    # List of parameters used for training
    parameters = {
        'reference_extract': reference_extract,
        'corpus_unigram': args['corpus_word_unigram'],
        'alpha': args['alpha'],
        'gamma': args['gamma']
    }

    for epoch in range(args['epochs']):
        # Iterate each state, according to the Q-learning algorithm
        for i in range(args['states_n'] - 1):
            # Get the scores
            Q_i = _choose_action(reference_pattern,
                                 reference_stylometry,
                                 Q[i],
                                 Q[i + 1],
                                 parameters)
            # Update the Q-table with this action score
            Q[i] = Q_i

    # Normalization: not necessary but easier to interpret if we look at
    # the Q-table
    normalized_Q = Q / np.max(Q)

    #
    # Generate a new clean dummy dict
    dummy_dict = build_dummy_dict(reference_pattern)
    # for each row in the Q-table (i.e., a state)
    for state in normalized_Q:
        # Execute the action producing the maximum reward
        # Passing dummy_dict as argument, ensure that it will change due to
        # shallow copy
        result = run_transformation(np.argmax(state),
                                    reference_pattern,
                                    dummy_dict)

    # Return information on how to modify the pattern
    # i.e., return the modified pattern and its dictionary of values
    return result, dummy_dict


def _choose_action(reference_pattern, reference_stylometry,
                   Q_i, Q_next_step, args):
    """ Choose the most optimized transformations according to the Q-values.

    Parameters
    ----------
    reference_pattern: dict
        The pattern under transformation
    reference_stylometry: `numpy.array`
        The stylometry of the original extract
    Q_i: `numpy.array`
        The Q-values of the current state
    Q_next_step: `numpy.array`
        The Q-values of the next state
    args: dict
        Parameters to be used for the reward functions

    Returns
    -------
    `numpy.array`
        The updated Q-values
    """
    # Find an applicable transformation
    transformation = choose_applicable_transformation(reference_pattern)

    # Build dummy dict
    dummy_dict = build_dummy_dict(reference_pattern)
    # Run the transformation
    result = transformation(reference_pattern, dummy_dict)
    # The tranformation may change the dummy_dict. Since there is a shallow
    # copy at invocation time, the changes will be reflected in the actual
    # instance of the dummy_dict

    # Compute reward of the transformation
    reward = _compute_reward(result, reference_stylometry, args)

    # Calculate the possible next maximum reward
    next_max_reward = _max_reward_next_step(
        reference_pattern, dummy_dict, reference_stylometry, Q_next_step, args)

    # Update Q-value for this transformation
    # Get the index of the transformation
    # idx = index of the transformation chosen (eg: identity has idx=1)
    idx = get_transformation_id(transformation)
    if idx == -1:
        raise IndexError('Transformation not found')
    # Update the Q_i array
    Q_i[idx] = (1 - args['alpha']) * Q_i[0] + args['alpha'] * (
        reward + args['gamma'] + next_max_reward)

    return Q_i


def _max_reward_next_step(pattern, dummy_dict, reference_stylometry,
                          Q_next_step, args):
    """ Compute the maximum reward of all potential next step actions.

    After finding all the transformations applicable to the current pattern, we
    run each of them using the same dummy dict. For each transformed pattern
    produced by the transformations, we calculate its reward. Finally, we
    return the max reward found with this process.

    Parameters
    ----------
    pattern: dict
        The pattern under transformation
    dummy_dict: dict
        The values replacing the keywords of the pattern
    reference_stylometry: `numpy.array`
        The stylometry of the original extract
    Q_next_step: `numpy.array`
        The array of the next step Q-values
    args: dict
        Parameters to be used for the reward function

    Returns
    -------
    float
        The maximum possible reward for the next step
    """
    reward = []
    # Get all the transformations applicable to this pattern
    all_transformations = get_all_applicable_transformations(pattern)
    # Calculate the reward for each of them
    for idx, transformation in enumerate(all_transformations):
        # Since most of the transformations modify the dummy_dict, we need
        # to run them on a deepcopy of the original one
        trans_pattern = transformation(pattern, copy.deepcopy(dummy_dict))
        rew_value = _compute_reward(trans_pattern, reference_stylometry, args)
        reward.append(Q_next_step[idx] + rew_value)

    # Return max reward
    return max(reward)


def _compute_reward(transformed_pattern, reference_stylometry, args):
    """ Compute the reward produced by a pattern transformation.

    Parameters
    ----------
    transformed_pattern: string
        The transformed pattern to insert
    reference_stylometry: `numpy.array`
        The stylometry of the original extract
    args: dict
        Dictionary of arguments (included the corpus_unigram)

    Returns
    -------
    float
        The similarity between the reference stylometry and the computed
        stylometry
    """
    # Inject the transformed pattern into the extract
    modified_snippet = _insert_into_extract(args['reference_extract'],
                                            transformed_pattern)
    extract_modified_stylography = compute_vector(
        modified_snippet, args['corpus_unigram'])

    sim = cosine_similarity(reference_stylometry.reshape(1, -1),
                            extract_modified_stylography.reshape(1, -1))[0][0]
    return sim


def _insert_into_extract(extract, transformed_pattern):
    """ Insert a transformed pattern into an extract (at a random position).

    Parameters
    ----------
    extract: string
        The extract
    transformed_pattern: string
        The transformed pattern

    Returns
    -------
    string
        The extract containing also the transformed pattern (randomly inserted)
    """
    extract_splitted = extract.split('\n')
    extract_splitted.insert(random.randint(0, len(extract_splitted) - 1),
                            transformed_pattern)
    return '\n'.join(extract_splitted)

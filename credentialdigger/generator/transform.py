import json
import logging
import random
from pathlib import Path

import pkg_resources

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

OPTIONS = {'function': [3, 4], 'method': [5, 6], 'object': [7, 8], 'type': [9]}


def build_dummy_dict(pattern):
    """ Build a dummy dictionary for a pattern.

    The process used to build the dummy dict is the following.
    1- Given the keys in the pattern dictionary, find only relevant keywords
    (function, method, ...). The relevant keywords, are the same ones that
    appear as keys in OPTIONS.
    2- Load fake values from the local file containing the dataset for the
    current keyword
    3- In the dummy dict, assign the median value to the key

    Parameters
    ----------
    pattern: dict
        The pattern to be transformed

    Returns
    -------
    dict:
        A dictionary of mock values for this pattern, filled with median values
        for each keyword

    Example
    -------
    >>> pattern = {'id': N, 'key': 'key',
                   'function_1': 'X', 'type_1': 'Y', 'type_2': 'Z'}
    >>> dummy = build_dummy_dict(pattern)
    >>> print(dummy)
    >>> {'function_1': 'median_function',
         'type_1': 'median_type',
         'type_2': 'median_type',
         'key': 'median_key'}
    """
    dummy = {}
    generator = Path(pkg_resources.resource_filename('credentialdigger',
                                                     'generator'))
    for key in pattern:
        # Get keyword (keys are in the form keyword_N, e.g., type_2)
        keyword = key.split('_')[0]
        if keyword not in OPTIONS:
            continue
        # Not very efficient
        # The same file may be read and loaded many times
        with open(generator / 'pattern_data' / ('%s_names.txt' % keyword),
                  'r') as f:
            values = f.read().splitlines()
        values.sort(key=lambda s: len(s))
        # Assign the median value
        dummy[key] = values[(len(values) + 1) // 2]

    # There is always a key="key". Inizialize it with the median value, too.
    with open(generator / 'pattern_data' / 'key_names.txt', 'r') as f:
        values = f.read().splitlines()
    dummy['key'] = values[(len(values) + 1) // 2]

    # # The password value is always random
    # with open('pattern_data/password_values.txt', 'r') as f:
    #     values = f.read().splitlines()
    # dummy['value'] = random.choice(values)

    return dummy


def run_transformation(tid, pattern, dummy_dict=None):
    """ Run the transformation with id `tid` over the pattern, using values
    from the dummy_dict.

    Parameters
    ----------
    tid: int
        The id of the transformation to be executed
    pattern: dict
        The pattern to be transformed
    dummy_dict: dict, optional
        A dictionary of mock values for this pattern. If not defined, a new
        default dummy_dict is genereated using the `build_dummy_dict` method

    Returns
    -------
    str
        A transformed pattern
    """
    if dummy_dict is None:
        dummy_dict = {}

    # Ensure the transformation can be run on this pattern
    supported = _find_possible_transformations(pattern)
    if tid not in supported:
        raise ValueError('Wrong transformation chosen with id=%s' % tid)
    # Get the transformation to be run
    action = TRANSFORMATIONS[tid]
    # Build a dummy dict if not passed as argument)
    if not dummy_dict:
        dummy_dict = build_dummy_dict(pattern)
    # Call function
    transformed_pattern = action(pattern, dummy_dict)
    return transformed_pattern


def choose_applicable_transformation(pattern):
    """ Choose a transformation to be applied to the pattern.

    Each pattern has a subset of actions (i.e., transformations) that are
    applicable. Since not all the actions are applicable to a pattern, we need
    to first find a pool of candidates, and then choose randomly one from this
    pool.

    Parameters
    ----------
    pattern: dict
        The pattern to be transformed

    Returns
    -------
    function
        A transformation function
    """
    possibilities = _find_possible_transformations(list(pattern.keys()))
    return TRANSFORMATIONS[random.choice(possibilities)]


def _find_possible_transformations(pattern_keys):
    """ Find the transformations applicable to a pattern.

    Parameters
    ----------
    pattern_keys: list
        The keywords of the pattern to be transformed

    Returns
    -------
    list
        A list of transformation ids (integers) applicable to the pattern
    """
    # The first 3 transformations are applicable to all the patterns
    # (i.e., identity and key transformations)
    possibilities = [0, 1, 2]

    # Get transformations applicable to this pattern
    for key in pattern_keys:
        # Keys are in the form key_number (e.g., function_1)
        # Remove underscore and number to get the keyword
        possibilities.extend(OPTIONS.get(key.split('_')[0], []))

    # Return possibilities without duplicates
    return list(set(possibilities))


def get_all_applicable_transformations(pattern):
    """ Find the transformations applicable to a pattern.

    Parameters
    ----------
    pattern: dict
        The pattern to be transformed

    Returns
    -------
    list
        A list of transformations (functions) applicable to the pattern
    """
    possibilities = _find_possible_transformations(list(pattern.keys()))
    return list(map(lambda n: TRANSFORMATIONS[n], possibilities))


def get_patterns():
    """ Get all the patterns.

    The patterns are loaded from the local file `patterns.json`.

    Returns
    -------
    list
        A list of patterns (dictionaries)
    """
    generator = Path(pkg_resources.resource_filename('credentialdigger',
                                                     'generator'))
    with open(generator / 'pattern_data' / 'patterns.json') as json_file:
        patterns = json.load(json_file)
    return patterns


def get_transformation_id(action):
    """ Get the id of a transformation.

    Parameters
    ----------
    action: function
        The transformation function

    Returns
    -------
    int
        The id of the action (-1 if not found)
    """
    for index, trans in TRANSFORMATIONS.items():
        if trans == action:
            return index
    return -1


##########################################
# #         TRANSFORMATIONS            # #
##########################################

def identity(pattern, dummy_dict):
    """ Identity transformation.

    Parameters
    ----------
    pattern: dict
        The pattern to be transformed
    dummy_dict: dict
        A dictionary of mock values for this pattern

    Returns
    -------
    str:
        The transformed pattern
    """
    return _inject_values(pattern, dummy_dict)


def longer_key(pattern, dummy_dict):
    """ Pick a longer key.

    Pick a random key name from the pattern, and change its value to a
    value greater than the actual one (the key names are taken from the
    dataset).

    Parameters
    ----------
    pattern: dict
        The pattern to be transformed
    dummy_dict: dict
        A dictionary of mock values for this pattern

    Returns
    -------
    str:
        The transformed pattern
    """
    # Get all possible key values from the dataset
    generator = Path(pkg_resources.resource_filename('credentialdigger',
                                                     'generator'))
    with open(generator / 'pattern_data' / 'key_names.txt', 'r') as f:
        values = f.read().splitlines()
    values.sort(key=lambda s: len(s))

    # There is just one key in the dummy dict. Change its value to a greater
    # one.
    try:
        i = values.index(dummy_dict['key'])
    except ValueError:
        # This error should never occur, since every value of the dummy_dict
        # should appear in the dataset
        # Reset to the median value
        i = len(values) // 2
    # Change the value
    dummy_dict['key'] = values[min(i + 1, len(values) - 1)]

    # Return transformed pattern
    return _inject_values(pattern, dummy_dict)


def smaller_key(pattern, dummy_dict):
    """ Pick a smaller key.

    Pick a random key name from the pattern, and change its value to a
    value smaller than the median (the key names are taken from the
    dataset).

    Parameters
    ----------
    pattern: dict
        The pattern to be transformed
    dummy_dict: dict
        A dictionary of mock values for this pattern

    Returns
    -------
    str:
        The transformed pattern
    """
    # Get all possible key values from the dataset
    generator = Path(pkg_resources.resource_filename('credentialdigger',
                                                     'generator'))
    with open(generator / 'pattern_data' / 'key_names.txt', 'r') as f:
        values = f.read().splitlines()
    values.sort(key=lambda s: len(s))

    # There is just one key in the dummy dict. Change its value to a smaller
    # one.
    try:
        i = values.index(dummy_dict['key'])
    except ValueError:
        # This error should never occur, since every value of the dummy_dict
        # should appear in the dataset
        # Reset to the median value
        i = len(values) // 2
    # Change the value
    dummy_dict['key'] = values[max(i - 1, 0)]

    # Return transformed pattern
    return _inject_values(pattern, dummy_dict)


def longer_function(pattern, dummy_dict):
    """ Pick a longer function.

    Pick a random function name from the pattern, and change its value to a
    value greater than the median (the function names are taken from the
    dataset).

    Parameters
    ----------
    pattern: dict
        The pattern to be transformed
    dummy_dict: dict
        A dictionary of mock values for this pattern

    Returns
    -------
    str:
        The transformed pattern
    """
    # Choose a random function from the pattern and change its value in the
    # dummy dict
    # Functions can be found as function_N in the keys of pattern
    candidate_functions = list(filter(lambda k: k.split('_')[0] == 'function',
                                      pattern))

    # Get all possible function values from the dataset
    generator = Path(pkg_resources.resource_filename('credentialdigger',
                                                     'generator'))
    with open(generator / 'pattern_data' / 'function_names.txt', 'r') as f:
        values = f.read().splitlines()
    values.sort(key=lambda s: len(s))

    # Choose a random key and change its value in the dummy_dict to a greater
    # one
    to_change = random.choice(candidate_functions)
    try:
        i = values.index(dummy_dict[to_change])
    except ValueError:
        # This error should never occur, since every value of the dummy_dict
        # should appear in the dataset
        # Reset to the median value
        i = len(values) // 2
    # Change the value
    dummy_dict[to_change] = values[min(i + 1, len(values) - 1)]

    # Return transformed pattern
    return _inject_values(pattern, dummy_dict)


def smaller_function(pattern, dummy_dict):
    """ Pick a smaller function.

    Pick a random function name from the pattern, and change its value to a
    value smaller than the median (the function names are taken from the
    dataset).

    Parameters
    ----------
    pattern: dict
        The pattern to be transformed
    dummy_dict: dict
        A dictionary of mock values for this pattern

    Returns
    -------
    str:
        The transformed pattern
    """
    # Choose a random function from the pattern and change its value in the
    # dummy dict
    # Functions can be found as function_N in the keys of pattern
    candidate_functions = list(filter(lambda k: k.split('_')[0] == 'function',
                                      pattern))

    # Get all possible function values from the dataset
    generator = Path(pkg_resources.resource_filename('credentialdigger',
                                                     'generator'))
    with open(generator / 'pattern_data' / 'function_names.txt', 'r') as f:
        values = f.read().splitlines()
    values.sort(key=lambda s: len(s))

    # Choose a random key and change its value in the dummy_dict to a smaller
    # one
    to_change = random.choice(candidate_functions)
    try:
        i = values.index(dummy_dict[to_change])
    except ValueError:
        # This error should never occur, since every value of the dummy_dict
        # should appear in the dataset
        # Reset to the median value
        i = len(values) // 2
    # Change the value
    dummy_dict[to_change] = values[max(i - 1, 0)]

    # Return transformed pattern
    return _inject_values(pattern, dummy_dict)


def longer_method(pattern, dummy_dict):
    """ Pick a longer method.

    Pick a random method name from the pattern, and change its value to a
    value greater than the median (the method names are taken from the
    dataset).

    Parameters
    ----------
    pattern: dict
        The pattern to be transformed
    dummy_dict: dict
        A dictionary of mock values for this pattern

    Returns
    -------
    str:
        The transformed pattern
    """
    # Choose a random method from the pattern and change its value in the
    # dummy dict
    # Methods can be found as method_n in the keys of pattern
    candidate_method = list(filter(lambda k: k.split('_')[0] == 'method',
                                   pattern))

    # Get all possible method values from the dataset
    generator = Path(pkg_resources.resource_filename('credentialdigger',
                                                     'generator'))
    with open(generator / 'pattern_data' / 'method_names.txt', 'r') as f:
        values = f.read().splitlines()
    values.sort(key=lambda s: len(s))

    # Choose a random key and change its value in the dummy_dict to a greater
    # one
    to_change = random.choice(candidate_method)
    try:
        i = values.index(dummy_dict[to_change])
    except ValueError:
        # This error should never occur, since every value of the dummy_dict
        # should appear in the dataset
        # Reset to the median value
        i = len(values) // 2
    # Change the value
    dummy_dict[to_change] = values[min(i + 1, len(values) - 1)]

    # Return transformed pattern
    return _inject_values(pattern, dummy_dict)


def smaller_method(pattern, dummy_dict):
    """ Pick a smaller method.

    Pick a random method name from the pattern, and change its value to a
    value smaller than the median (the method names are taken from the
    dataset).

    Parameters
    ----------
    pattern: dict
        The pattern to be transformed
    dummy_dict: dict
        A dictionary of mock values for this pattern

    Returns
    -------
    str:
        The transformed pattern
    """
    # Choose a random method from the pattern and change its value in the
    # dummy dict
    # Methods can be found as method_n in the keys of pattern
    candidate_method = list(filter(lambda k: k.split('_')[0] == 'method',
                                   pattern))

    # Get all possible method values from the dataset
    generator = Path(pkg_resources.resource_filename('credentialdigger',
                                                     'generator'))
    with open(generator / 'pattern_data' / 'method_names.txt', 'r') as f:
        values = f.read().splitlines()
    values.sort(key=lambda s: len(s))

    # Choose a random key and change its value in the dummy_dict to a smaller
    # one
    to_change = random.choice(candidate_method)
    try:
        i = values.index(dummy_dict[to_change])
    except ValueError:
        # This error should never occur, since every value of the dummy_dict
        # should appear in the dataset
        # Reset to the median value
        i = len(values) // 2
    # Change the value
    dummy_dict[to_change] = values[max(i - 1, 0)]

    # Return transformed pattern
    return _inject_values(pattern, dummy_dict)


def longer_object(pattern, dummy_dict):
    """ Pick a longer object.

    Pick a random object name from the pattern, and change its value to a
    value greater than the median (the object names are taken from the
    dataset).

    Parameters
    ----------
    pattern: dict
        The pattern to be transformed
    dummy_dict: dict
        A dictionary of mock values for this pattern

    Returns
    -------
    str:
        The transformed pattern
    """
    # Choose a random object from the pattern and change its value in the
    # dummy dict
    # Objects can be found as object_n in the keys of pattern
    candidate_object = list(filter(lambda k: k.split('_')[0] == 'object',
                                   pattern))

    # Get all possible object values from the dataset
    generator = Path(pkg_resources.resource_filename('credentialdigger',
                                                     'generator'))
    with open(generator / 'pattern_data' / 'object_names.txt', 'r') as f:
        values = f.read().splitlines()
    values.sort(key=lambda s: len(s))

    # Choose a random key and change its value in the dummy_dict to a greater
    # one
    to_change = random.choice(candidate_object)
    try:
        i = values.index(dummy_dict[to_change])
    except ValueError:
        # This error should never occur, since every value of the dummy_dict
        # should appear in the dataset
        # Reset to the median value
        i = len(values) // 2
    # Change the value
    dummy_dict[to_change] = values[min(i + 1, len(values) - 1)]

    # Return transformed pattern
    return _inject_values(pattern, dummy_dict)


def smaller_object(pattern, dummy_dict):
    """ Pick a smaller object.

    Pick a random object name from the pattern, and change its value to a
    value smaller than the median (the object names are taken from the
    dataset).

    Parameters
    ----------
    pattern: dict
        The pattern to be transformed
    dummy_dict: dict
        A dictionary of mock values for this pattern

    Returns
    -------
    str:
        The transformed pattern
    """
    # Choose a random object from the pattern and change its value in the
    # dummy dict
    # Objects can be found as object_n in the keys of pattern
    candidate_object = list(filter(lambda k: k.split('_')[0] == 'object',
                                   pattern))

    # Get all possible object values from the dataset
    generator = Path(pkg_resources.resource_filename('credentialdigger',
                                                     'generator'))
    with open(generator / 'pattern_data' / 'object_names.txt', 'r') as f:
        values = f.read().splitlines()
    values.sort(key=lambda s: len(s))

    # Choose a random key and change its value in the dummy_dict to a smaller
    # one
    to_change = random.choice(candidate_object)
    try:
        i = values.index(dummy_dict[to_change])
    except ValueError:
        # This error should never occur, since every value of the dummy_dict
        # should appear in the dataset
        # Reset to the median value
        i = len(values) // 2
    # Change the value
    dummy_dict[to_change] = values[max(i - 1, 0)]

    # Return transformed pattern
    return _inject_values(pattern, dummy_dict)


def change_type(pattern, dummy_dict):
    """ Change the object type.

    Parameters
    ----------
    pattern: dict
        The pattern to be transformed
    dummy_dict: dict
        A dictionary of mock values for this pattern

    Returns
    -------
    str:
        The transformed pattern
    """
    # Choose a random key from the pattern and change its value in the
    # dummy dict
    # Keys can be found as key_N in the keys of pattern
    candidate_keys = list(filter(lambda k: k.split('_')[0] == 'type',
                                 pattern))

    # Get all possible type values from the dataset
    generator = Path(pkg_resources.resource_filename('credentialdigger',
                                                     'generator'))
    with open(generator / 'pattern_data' / 'type_names.txt', 'r') as f:
        values = f.read().splitlines()
    values.sort(key=lambda s: len(s))

    # Remove actual type and choose randomly among the remaining ones
    to_change = random.choice(candidate_keys)
    try:
        values.remove(dummy_dict[to_change])
    except ValueError:
        # The actual dummy value is not supported by our dataset
        # This should never happen, so we can skip this exception
        pass
    dummy_dict[to_change] = random.choice(values)

    # Return transformed pattern
    return _inject_values(pattern, dummy_dict)


def _inject_values(pattern_dict, dummy_dict):
    """ Fill a pattern with random fake values.

    Only keywords (i.e., function, method, object, type) and key are considered
    for the injection. Indeed, the value is considered only at the end of the
    transformation phase.

    Parameters
    ----------
    pattern: dict
        The pattern to be transformed
    dummy_dict: dict
        A dictionary of mock values for this pattern

    Returns
    -------
    string
        The modified pattern
    """
    # Get the pattern
    pattern = pattern_dict['pattern']

    # Replace keywords appearing in OPTIONS
    replace_items = filter(lambda k: k.split('_')[0] in OPTIONS,
                           pattern_dict)
    # Replace parameters (inject fake values)
    for key in replace_items:
        pattern = pattern.replace(pattern_dict[key], dummy_dict[key])

    # Replace the key
    pattern = pattern.replace(pattern_dict['key'], dummy_dict['key'])

    # Return transformed pattern
    return pattern


##########################################
# #          END TRANSFORMATIONS       # #
##########################################


def generate_data(pattern, transformation_dict, multiplier=50):
    """ Generate training under contrainsts found in the Q-learning
    training.

    Parameters
    ----------
    pattern: dict
        The pattern to be transformed
    dummy_dict: dict
        A dictionary of mock values for this pattern
    multiplier: int, optional
        Define how many password to inject into the same transformed pattern
        (default `50`)

    Returns
    -------
    list
        List of variation based on modified-under-constraints pattern
    """
    generator = Path(pkg_resources.resource_filename('credentialdigger',
                                                     'generator'))
    # For each item in the tranformation dict, get the a window of possible
    # values, and replace the current one with a random value picked from the
    # dataset, respecting the window
    # There is space to improve efficiency since the same dataset may be loaded
    # multiple times
    for key in transformation_dict:
        if key == 'value':
            # We will choose the value in the next step
            continue
        try:
            # Load dataset
            with open(generator / 'pattern_data' / ('%s_names.txt' % key.split(
                    '_')[0]), 'r') as f:
                values = f.read().splitlines()
            values.sort(key=lambda s: len(s))
            # Get window
            i = values.index(transformation_dict[key])
            # Pick a random element and substitute the current one
            transformation_dict[key] = random.choice(
                values[max(0, i - 3): min(len(values) - 1, i + 3)])
        except FileNotFoundError:
            # Dataset not existing for this key
            logger.warning(f'No dataset available for key {key}. '
                           'Skip this value.')
        except ValueError:
            # Value not found in dataset. Choose randomly in the whole dataset
            transformation_dict[key] = random.choice(values)

    # Inject keywords
    injected_pattern = _inject_values(pattern, transformation_dict)

    # Add value placeholder to the transformation dict
    transformation_dict['value'] = 'value'
    # Initialization of patterns list

    final_pattern = []

    # Compute the pattern
    # Load passwords
    with open(generator / 'pattern_data' / 'password_values.txt', 'r') as f:
        password_values = f.read().splitlines()
    password_values.sort(key=lambda s: len(s))
    # Inject passwords
    for i in range(multiplier):
        # Choose a random password
        dummy_password = random.choice(password_values)
        injected_pattern_with_value = injected_pattern.replace(
            transformation_dict['value'], dummy_password)
        # Update transformation dict
        # transformation_dict['value'] = dummy_password

        # Add pattern
        data = {
            'text': injected_pattern_with_value,
            'key': transformation_dict['key'],
            'value': dummy_password
        }
        final_pattern.append(data)

    return final_pattern


TRANSFORMATIONS = {0: identity,
                   1: longer_key,
                   2: smaller_key,
                   3: longer_function,
                   4: smaller_function,
                   5: longer_method,
                   6: smaller_method,
                   7: longer_object,
                   8: smaller_object,
                   9: change_type,
                   }

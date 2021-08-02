import re
import tensorflow as tf


class PathModel():

    def analyze(self, discoveries):
        file_paths = [d['file_name'] for d in discoveries]
        unique_paths = list(set(file_paths))
        path_dict = {}
        for path in unique_paths:
            if re.search(r'test|example|demo', path):
                path_dict[path] = 1
            else:
                path_dict[path] = 0
        n_false_positives = 0
        for d in discoveries:
            if path_dict[d['file_name']] == 1:
                d['state'] = 'false_positive'
                n_false_positives += 1
        return discoveries, n_false_positives


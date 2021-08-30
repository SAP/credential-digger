import json
import logging
import random
import re
import shutil
import tempfile
from collections import Counter
from pathlib import Path

import pandas as pd
import pkg_resources
import string_utils
from git import Repo as GitRepo
from rich.progress import Progress

from .qlearning import compute_dataset
from .training import create_snippet_model

EXCLUDED_NAMES = set(['changelog', 'codeowners', 'contribute',
                      'docker-compose', 'dockerfile', 'jenkinsfile', 'license',
                      'makefile', 'package', 'package-lock'])
EXCLUDED_EXTS = set(['bin', 'csv', 'gz', 'jpg', 'md', 'pdf', 'png', 'rst',
                     'svg', 'txt', 'yml', 'zip'])

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ExtractorGenerator:

    def generate_leak_snippets(self, repo_url, num_extracts=30):
        """ Generate the extractor model adapted to a repository.

        Parameters
        ----------
        repo_url: str
            The url of the repository
        num_extracts: int, optional
            The maximum number of extracts needed (default `30`)

        Returns
        -------
        str
            The name of the model folder
        str
            The name of the binary for the extractor model
        """
        # Generate the corpus for the repo
        corpus = self.build_corpus(repo_url, num_extracts)
        try:
            return self.train_model(corpus, repo_url)
        except FileExistsError:
            logger.warning('Model for this developer already created. '
                           'Do not generate a new one.')
            # Return the existing one
            return self._search_model_extractor(repo_url)

    def _clone_git_repo(self, git_url):
        """ Clone git repository. """
        project_path = tempfile.mkdtemp()
        GitRepo.clone_from(git_url, project_path)
        return project_path

    def _get_relevant_files(self, local_repo_path):
        """ Sort the files of this repository according to their relevance. The
        relevance of a file is calculated as the number of commits which
        changed it.

        Parameters
        ----------
        local_repo_path: str
            The local path of the repo (cloned from github)

        Returns
        -------
        list
            A list of file names, sorted by relevance
        """
        r = GitRepo(local_repo_path)
        all_commits = r.git.log('--name-only', '--pretty=format:').split()
        counted_commits = Counter(all_commits)
        # Sort the files according to the number of commits they appear in
        sorted_commits = sorted(counted_commits.items(),
                                key=lambda x: x[1],
                                reverse=True)
        # Return the file names sorted per commits number
        return list(zip(*sorted_commits))[0]

    def _search_model_extractor(self, repo_url):
        """ Find the existing extractor binary.

        If the model for this developer has already been generated, then we
        should find it in the `models_data` folder (i.e., the default folder
        for the ML models).

        Parameters
        ----------
        repo_url: str
            The url of the repository

        Returns
        -------
        str
            The name of the model folder
        str
            The name of the binary for the extractor model
        """
        # Find model folder
        # The model name is the name of the author of the repository
        model_name = 'snippet_model_%s' % repo_url.split('/')[-2]
        # It is stored in the models_data folder
        models_data = Path(pkg_resources.resource_filename('credentialdigger',
                                                           'models_data'))
        dev_model = models_data / model_name

        # Find extractor binary
        # Get name and version from the metafile
        with open(dev_model / 'meta.json', 'r') as f:
            meta = json.loads(f.read())
        inner_folder = dev_model / ('%s-%s' % (meta['name'], meta['version']))
        # There should be only one binary in the inner folder
        extractor_file = list(inner_folder.glob('**/*.bin'))[0]

        return dev_model.name, extractor_file.name

    def build_corpus(self, repo_url, num_extracts):
        """ Build the corpus for this repo.

        Parameters
        ----------
        repo_url: str
            The url of the repository
        num_extracts: int
            The maximum number of extracts needed

        Returns
        -------
        list
            A list of strings (i.e., the extracts)
        """
        # Clone the repo from Github (the scanner deletes it when it finishes
        # its tasks)
        repo_path = self._clone_git_repo(repo_url)
        # Get the ranking of the files of this repo
        ranking = self._get_relevant_files(repo_path)

        # Build the corpus
        repo_local_path = Path(repo_path)
        corpus = []
        fi = 0
        while fi < len(ranking) and len(corpus) < num_extracts:
            current = repo_local_path / ranking[fi]
            # Some files cannot be used to produce extracts
            pp = Path(current).name
            if pp[0] == '.' or pp.split('.')[-1] in EXCLUDED_EXTS or \
                    pp.split('.')[0].lower() in EXCLUDED_NAMES:
                fi += 1
                continue
            try:
                with open(current, 'r') as f:
                    # Extend the corpus with the extracts found in this file
                    corpus.extend(self._get_extracts(f.read()))
            except UnicodeDecodeError:
                # If the read raises this exception, then either the language
                # uses a different charset or the file may be a csv (or a
                # binary). In both cases, skip it.
                # print('Skip file %s (encoding error)' % current)
                pass
            except FileNotFoundError:
                # If the read raises this exception, then the file has been
                # deleted from the repository. In this case, ignore it (since
                # for the generator we only need the stylometry of the
                # developer, the content is not important).
                # print('Skip file %s (deleted)' % current)
                pass

            fi += 1

        # Delete local repo folder
        shutil.rmtree(repo_path)

        return corpus

    def _get_extracts(self, code):
        """ Use the code to produce extracts.
        Parameters
        ----------
        code: str
            The content of a file

        Returns
        -------
        list
            A list of extracts (i.e., a list of strings)
        """
        rows = code.split('\n')
        extracts = []
        # If the code is shorter than 10 lines, we ignore this file
        if 10 <= len(rows) < 15:
            # If the code is 10 to 15 lines, we use the whole file as corpus
            extracts.append(code)
        elif len(rows) >= 15:
            # If the code is longer than 15 lines, we split it into multiple
            # extracts of lenght generated randomly (10 to 15 lines each)
            while len(rows) > 10:
                # Generate an extract using the first r rows, with r a random
                # number between 10 and 20
                r = random.randint(10, 20)
                extracts.append('\n'.join(rows[:r]))
                # Remove the first r rows
                rows = rows[r + 1:]
        return extracts

    def train_model(self, corpus, repo_url, training_data_size=75000,
                    actions_n=12, states_n=13, alpha=0.5, gamma=0.85,
                    epochs_basis=50, extract_max_length=150):
        """ Train the snippet model according to the user stylometry.

        Parameters
        ----------
        corpus: list
            A corpus of code, i.e., a list of excerpts of a repository
        repo_url: str
            The url of the repository
        training_data_size: int, optional
            The size of the training dataset (default `75000`)
        actions_n: int, optional
            The number of actions in the Q-table (default `12`)
        states_n: int, optional
            The number of states in the Q-table (default `13`)
        alpha: float, optional
            The alpha parameter in the reward function (default `0.5`)
        gamma: float, optional
            The gamma parameter in the reward function (default `0.85`)
        epochs_basis: int, optional
            The base number of epochs (default `50`)
        extract_max_length: int, optional
            The maximum length of extracts for being processed (default `150`)

        Returns
        -------
        str
            The name of the model folder
        str
            The name of the binary for the extractor model
        """
        # Compute dataset with qlearning algorithm
        raw_df = compute_dataset(corpus, actions_n, states_n, alpha, gamma,
                                 epochs_basis, extract_max_length)

        # Load dataframe
        df = pd.DataFrame(data=raw_df).sample(n=training_data_size,
                                              replace=False)

        # Preprocess data before training
        df = self._preprocess_training_model(df)

        # Create the model
        return create_snippet_model(df, repo_url)

    def _preprocess_training_model(self, data):
        """ Pre-process the data for the model.

        Parameters
        ----------
        data: `pandas.DataFrame`
            The training dataset

        Returns
        -------
        `pandas.DataFrame`
            Pre-processed dataframe
        """
        def _pre_process(raw_data):
            """ Pre-process raw data. """
            pattern = re.compile(
                r"((?<=')\w\d.*?(?=')|(?<=\")\w\d.*?(?=\")|[\w\d]+)")
            words = re.findall(pattern, raw_data)
            return ' '.join(list(map(string_utils.snake_case_to_camel, words)))

        data_list = []
        # Preprocess the dataset with naming convention, etc.
        with Progress() as progress:
            preprocess_task = progress.add_task('Pre-processing dataset...',
                                                total=data.shape[0])
            for idx, row in data.iterrows():
                row_data = {}
                for column in ['text', 'key', 'value']:
                    row_data[column] = _pre_process(row[column])
                data_list.append(row_data)
                progress.update(preprocess_task, advance=1)
        return pd.DataFrame(data=data_list)

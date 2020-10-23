[![REUSE status](https://api.reuse.software/badge/github.com/SAP/credential-digger)](https://api.reuse.software/info/github.com/SAP/credential-digger)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/SAP/credential-digger?logo=github)
![PyPI](https://img.shields.io/pypi/v/credentialdigger?logo=pypi)

![Logo](https://raw.githubusercontent.com/SAP/credential-digger/main/github_assets/Logo-CD-Mint_48.png)

# Credential Digger

Credential Digger is a GitHub scanning tool that identifies hardcoded credentials (Passwords, API Keys, Secret Keys, Tokens, personal information, etc), filtering the false positive data through machine learning models.

-  [Requirements](#requirements)
-  [Install](#install)
-  [Quick launch with UI](#quick-launch)
-  [Advanced Install](#advanced-install)
	-  [Install from source](#install-from-source)
  	-  [Download machine learning models](#download-machine-learning-models)
	-  [Configure the regular expressions Scanner](#configure-the-regular-expressions-scanner)
-  [Usage](#usage)
	-  [Scan a repository](#scan-a-repository)
	-  [Fine-tuning](#fine-tuning)
-  [Wiki](#wiki)
-  [News](#news)


## Requirements

Credential Digger supports Python >= 3.6 and < 3.8, and works only with LINUX systems.

[Docker](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) are needed if you want run an image of Credential Digger as a container, as discussed [here](#quick-launch).

## Install

You can either install the module using `pip` or [build it from the source](#install-from-source)

```bash
pip install credentialdigger
```
_Please make sure to add the [scanning rules](https://github.com/SAP/credential-digger/wiki/Rules) to the database before scanning a repo._

#### _Scan your first repo for leaks_
```bash
python -m credentialdigger scan https://github.com/user/repo --sqlite /path/to/data.db
```

## Quick Launch

To have a ready-to-use instance of Credential Digger, with the UI:

```bash
git clone https://github.com/SAP/credential-digger.git
cd credential-digger
cp .env.sample .env
sudo docker-compose up --build
```

The UI is available at http://localhost:5000/

The docker container for Credential Digger uses a local sqlite database.

### Quick Install with an external database

Another ready-to-use instance of Credential Digger with the UI, but using a dockerized postgres database instead of a local sqlite one:

```bash
git clone https://github.com/SAP/credential-digger.git
cd credential-digger
cp .env.sample .env
vim .env  # set credentials for postgres
sudo docker-compose -f docker-compose.postgres.yml up --build
```

Differently from the sqlite version, here we need to configure the `.env` file with the credentials for postgres (by modifying POSTGRES_USER, POSTGRES_PASSWORD and POSTGRES_DB).

Most advanced users may also wish to use an external postgres database instead of the dockerized one we provide in our `docker-compose.postgres.yml`.

## Advanced Install

First, you need to install the regular expression matching library [Hyperscan](https://github.com/intel/hyperscan), where you can find the complete installation process for all platforms [here](http://intel.github.io/hyperscan/dev-reference/getting_started.html). Be sure to have `build-essential` and `python3-dev` too.

```bash
sudo apt install libhyperscan-dev
sudo apt install build-essential
sudo apt install python3-dev
```


### Install from source

Configure a virtual environment for Python 3 (optional) and clone the main branch

```bash
virtualenv --system-site-packages -p python3 ./venv
source ./venv/bin/activate

git clone https://github.com/SAP/credential-digger.git
cd credential-digger
```

Install the requirements from `requirements.txt` file and install the library:

```bash
pip install -r requirements.txt
python setup.py install
```

### Download machine learning models

Credential Digger leverages machine learning models to filter false positives, especially in the identification of passwords:

- Path Model: Identify the test files, documentation, or example files containing fake credentials (e.g., unit tests)

- Snippet Model: Identify the portion of code used to authenticate with passwords, and distinguish between real and dummy passwords.


Download the binaries:

```bash
export path_model=https://github.com/SAP/credential-digger/releases/download/PM-v1.0.1/path_model-1.0.1.tar.gz
export snippet_model=https://github.com/SAP/credential-digger/releases/download/SM-v1.0.0/snippet_model-1.0.0.tar.gz

python -m credentialdigger download path_model
python -m credentialdigger download snippet_model
```
>  **WARNING**: If you build the code from scratch (i.e., you don't install the client via
pip), don't run the download command from the installation folder of
_credentialdigger_ in order to avoid errors in linking.

>  **WARNING**: We provide the pre-trained models, but we do not guarantee the efficiency of these models. If you want more accurate machine learning models, you can train your own models (just replace the binaries by your own models) or use the fine-tuning option.


### Configure the regular expressions Scanner

One of the core components of Credential Digger is the regular expression scanner. You can choose the regular expressions rules you want (just follow the template [here](https://github.com/SAP/credential-digger/blob/main/ui/backend/rules.yml)). We provide a list of patterns in the `rules.yml` file, that are included in the UI.

When following the advanced user steps, you need to set your own rules. In a Python terminal:

```python
from credentialdigger import SqliteClient

c = SqliteClient(path='/path/to/data.db')

c.add_rules_from_file('/path/to/rules.yml')
```

>  **WARNING**: These instructions are valid for the `SqliteClient`.

## Usage

When using docker-compose, use the UI available at http://localhost:5000/

When installing _credentialdigger_ from pip or from source, you can instantiate the client and scan a repository. 

Instantiate a client:

```python
from credentialdigger import SqliteClient

c = SqliteClient(path='/path/to/data.db')
```

### Scan a repository

```python
new_discoveries = c.scan(repo_url='https://github.com/user/repo',
                         models=['PathModel', 'SnippetModel'],
                         debug=True)
```

>  **WARNING**: Make sure you added rules before scanning a repository.

>  **WARNING**: Make sure you download the models before using them in a scan.

Please refer to the [Wiki](https://github.com/SAP/credential-digger/wiki) for further information on the arguments.

### CLI - Command Line Interface

Credential Digger also offers a simple CLI to scan a repository. The CLI supports both sqlite and postgres databases. In case of postgres, the user needs to export the credentials (the same appearing in the `.env` file) as environment variables. In case of sqlite, the path of the db must be passed as argument.
```bash
# Scan using SqliteClient
python -m credentialdigger scan https://github.com/user/repo --sqlite cdigger.db

# Scan using PgClient
export POSTGRES_USER=...
export ...
python -m credentialdigger scan https://github.com/user/repo
```

Since rules are needed to scan a repository, the CLI also offers the possibility to add rules from a file.
```bash
# Add the rules to the database
python -m credentialdigger add_rules /path/to/rules.yml --sqlite cdigger.db
```

### Fine-tuning

Credential Digger offers the possibility to fine-tune the snippet model, by retraining a model on each repository scanned.
If you want to activate this option, set `generate_snippet_extractor=True`. You need to donwload the snippet model before using the fine-tuning option.


## Wiki

For further information, please refer to the [Wiki](https://github.com/SAP/credential-digger/wiki)


## News

-  [Credential Digger announcement](https://blogs.sap.com/2020/06/23/credential-digger-using-machine-learning-to-identify-hardcoded-credentials-in-github)
-  [Credential Digger is now supporting Keras machine learning models](https://github.com/SAP/credential-digger/tree/keras_models)

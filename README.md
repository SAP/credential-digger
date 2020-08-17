![Logo](https://raw.githubusercontent.com/SAP/credential-digger/master/github_assets/Logo-CD-Mint_48.png)

# Credential Digger

Credential Digger is a GitHub scanning tool that identifies hardcoded credentials (Passwords, API Keys, Secret Keys, Tokens, personal information, etc), filtering the false positive data through machine learning models.

-  [Requirements](#requirements)
-  [Quick Install](#quick-install)
-  [Install](#advanced-install)
	-  [Install using pip](#install-using-pip)
	-  [Install from source](#install-from-source)
	-  [Build the database](#build-the-database)
  -  [Download machine learning models](#download-machine-learning-models)
-  [Configure the regular expressions Scanner](#configure-the-regular-expressions-scanner)
-  [Usage](#usage)
	-  [Scan a repository](#scan-a-repository)
	-  [Fine-tuning](#fine-tuning)
-  [Wiki](#wiki)
-  [News](#news)


## Requirements

Credential Digger supports Python 3.6, and works only with LINUX systems.

You need to have [Docker](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/)


## Quick Install

To have a ready-to-use instance of Credential Digger, with the UI :

```bash
cp .env.sample .env
vim .env
sudo docker-compose up --build
```

The UI is available at http://localhost:5000/

>  **WARNING**: The UI does not support the machine learning models for the moment. If you want to use the models, please follow the advanced install.


## Advanced Install

First, you need to install the regular expression matching library [Hyperscan](https://github.com/intel/hyperscan), where you can find the complete installation process for all platforms [here](http://intel.github.io/hyperscan/dev-reference/getting_started.html). Be sure to have `build-essential` and `python3-dev` too.

```bash
sudo apt install libhyperscan-dev
sudo apt install build-essential
sudo apt install python3-dev
```

### Install using pip

You can either install from using `pip` or building from the source

```bash
pip install credentialdigger
```

### Install from source

Configure a virtual environment for Python 3 (optional) and clone the master branch

```bash
virtualenv --system-site-packages -p python3 ./venv
source ./venv/bin/activate

git clone https://github.com//SAP/credential-digger.git
cd credential-digger
```

Install the requirements from the requirement file `requirements.txt` file and build:

```bash
pip install -r requirements.txt
python setup.py install
```

### Build the database

Build the database: configure the `.env` file with your own credentials (by modifying POSTGRES_USER, POSTGRES_PASSWORD and POSTGRES_DB). The database is available at http://localhost:5432/.


```bash
cp .env.sample .env
vim .env # Insert real credentials
sudo docker-compose up --build postgres
```

### Download machine learning models

Credential Digger leverages machine learning models to filter false positives, especially in the identification of passwords :

- Path Model: Identify the test files, documentation, or example files containing fake credentials (e.g, unit tests)

- Snippet Model: Identify the portion of code used to authenticate with passwords, and distinguish between real and dummy passwords.


Download the binaries:

```bash
export path_model=https://github.com/SAP/credential-digger/releases/download/PM-v1.0.1/path_model-1.0.1.tar.gz
export snippet_model=https://github.com/SAP/credential-digger/releases/download/SM-v1.0.0/snippet_model-1.0.0.tar.gz
```

```bash
python -m credentialdigger download path_model
python -m credentialdigger download snippet_model
```
>  **WARNING**: If you build the code from scratch (i.e., you don't install the client via
pip), don't run the download command from the installation folder of
_credentialdigger_ in order to avoid errors in linking.

>  **WARNING**: We provide the pre-trained models, but we do not guarantee the efficiency of these models. If you want more accurate machine learning models, you can train your own models (just replace the binaries by your own models) or use the fine-tuning option.


## Configure the regular expressions Scanner

One of the core components of Credential Digger is the regular expression scanner. You can choose the regular expressions rules you want (just follow the template [here](https://github.com/SAP/credential-digger/blob/master/resources/rules.yml)). We provide a list of patterns in the `rules.yml` file. In a Python terminal:

```python
from credentialdigger.cli import Client

c = Client(dbname='MYDB',
           dbuser='POSTGRES_USER',
           dbpassword='POSTGRES_PASSWORD',
           dbhost='localhost',
           dbport=5432)

c.add_rules_from_file('credentialdigger/resources/rules.yml')
```


## Usage

To instantiate a client connected to the database:

```python
from credentialdigger.cli import Client

c = Client(dbname='MYDB',
           dbuser='POSTGRES_USER',
           dbpassword='POSTGRES_PASSWORD',
           dbhost='localhost',
           dbport=5432)
```

### Scan a repository

```python
new_discoveries = c.scan(repo_url='https://github.com/user/repo',
                         models=['PathModel', 'SnippetModel'],
                         verbose=True)
```

Please refer to the [Wiki](https://github.com/SAP/credential-digger/wiki) for further information on the arguments.


### Fine-tuning

Credential Digger offers the possibility to fine-tune the snippet model, by retraining a model on each repository scanned. If you want to activate this option, set `generate_snippet_extractor=True`.


## Wiki

For further information, please refer to the [Wiki](https://github.com/SAP/credential-digger/wiki)


## News

-  [Credential Digger announcement](https://blogs.sap.com/2020/06/23/credential-digger-using-machine-learning-to-identify-hardcoded-credentials-in-github)
-  [Credential Digger is now supporting Keras machine learning models](https://github.com/SAP/credential-digger/tree/keras_models)

[![REUSE status](https://api.reuse.software/badge/github.com/SAP/credential-digger)](https://api.reuse.software/info/github.com/SAP/credential-digger)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/SAP/credential-digger?logo=github)
![PyPI](https://img.shields.io/pypi/v/credentialdigger?logo=pypi)

![Logo](https://raw.githubusercontent.com/SAP/credential-digger/main/github_assets/Logo-CD-Mint_48.png)

# Credential Digger

Credential Digger is a GitHub scanning tool that identifies hardcoded credentials (Passwords, API Keys, Secret Keys, Tokens, personal information, etc), filtering the false positive data through machine learning models.


[![Watch the video](https://img.youtube.com/vi/1qz8lYPrtMo/0.jpg)](https://www.youtube.com/watch?v=1qz8lYPrtMo)



-  [Why](#why)
-  [Requirements](#requirements)
-  [How to run](#how-to-run)
    - [Install dependencies](#install-dependencies)
    - [Add rules](#add-rules)
    - [Install machine learning models](#install-machine-learning-models)
    - [Scan a repository](#scan-a-repository)
-  [Docker container](#docker-container)
-  [Advanced install](#advanced-install)
    - [Build from source](#build-from-source)
    - [External postgres database](#external-postgres-database)
-  [Python library usage](#python-library-usage)
    - [Add rules](#add-rules)
    - [Scan a repository](#scan-a-repository)
        - [Fine-tuning](#fine-tuning)
-  [CLI - Command Line Interface](#cli-command-line-interface)
-  [Wiki](#wiki)
-  [Contributing](#contributing)
-  [News](#news)


## Why
In data protection, one of the most critical threats is represented by hardcoded (or plaintext) credentials in open-source projects. Several tools are already available to detect leaks in open-source platforms, but the diversity of credentials (depending on multiple factors such as the programming language, code development conventions, or developers' personal habits) is a bottleneck for the effectiveness of these tools. Their lack of precision leads to a very high number of pieces of code incorrectly detected as leaked secrets. Data wrongly detected as a leak is called _false positive_ data, and compose the huge majority of the data detected by currently available tools.

The goal of Credential Digger is to reduce the amount of false positive data on the output of the scanning phase by leveraging machine learning models.

![Architecture](https://raw.githubusercontent.com/SAP/credential-digger/main/tutorials/img/architecture.png)


For the complete description of the approach of Credential Digger, [you can read this publication](https://jam4.sapjam.com/groups/KxkEs5HqefZnmgxTYUSSov/documents/pDwaPu8XwYHnxgWwJZP94L/slide_viewer).

```
@InProceedings {lrnto-icissp21,
    author = {S. Lounici and M. Rosa and C. M. Negri and S. Trabelsi and M. Önen},
    booktitle = {Proc. of the 8th The International Conference on Information Systems Security and Privacy  (ICISSP)},
    title = {Optimizing Leak Detection in Open-Source Platforms with Machine Learning Techniques},
    month = {February},
    day = {11-13},
    year = {2021}
}
```

## Requirements

Credential Digger supports Python >= 3.6 and < 3.9, and works only with LINUX systems (currently, it has been tested on Ubuntu). [With some hacks](https://github.com/SAP/credential-digger/wiki/MacOS-support), it can be installed also on MacOS.
In case you don't meet these requirements, you may consider running a [Docker container](#docker) (that also includes a user interface).


## How to run

### Install dependencies

First, you need to install the regular expression matching library [Hyperscan](https://github.com/intel/hyperscan). Be sure to have `build-essential` and `python3-dev` too.

```bash
sudo apt install -y libhyperscan-dev build-essential python3-dev
```

Then, you can install Credential Digger module using `pip`.

```bash
pip install credentialdigger
```

### Add rules

One of the core components of Credential Digger is the regular expression scanner. You can choose the regular expressions rules you want (just follow the template [here](https://github.com/SAP/credential-digger/blob/main/ui/backend/rules.yml)). We provide a list of patterns in the `rules.yml` file, that are included in the UI.

**Before the very first scan, you need to add the rules that will be used by the scanner.** This step is only needed once.

```bash
python -m credentialdigger add_rules --sqlite /path/to/data.db /path/to/rules.yaml
```

### Install machine learning models

Credential Digger leverages machine learning models to filter false positives, especially in the identification of passwords:

- Path Model: A lot of fake credentials reside in example files such as documentation, examples or test files, since it is very common for developers to provide test code for their projects. The Path Model analyzes the path of each discovery and classifies it as false positive when needed.

- Snippet Model: Identify the portion of code used to authenticate with passwords, and distinguish between real and dummy passwords. This model is composed of a pre-processing step (Extractor) and a classification step (Classifier).


To install the models, you first need to export them as environment variables, and them download them:

```bash
export path_model=https://github.com/SAP/credential-digger/releases/download/PM-v1.0.1/path_model-1.0.1.tar.gz
export snippet_model=https://github.com/SAP/credential-digger/releases/download/SM-v1.0.0/snippet_model-1.0.0.tar.gz

python -m credentialdigger download path_model
python -m credentialdigger download snippet_model
```
>  **WARNING**: Don't run the download command from the installation folder of _credentialdigger_ in order to avoid errors in linking.

>  **WARNING**: We provide the pre-trained models, but we do not guarantee the efficiency of these models. If you want more accurate machine learning models, you can train your own models (just replace the binaries with your own models) or use the [fine-tuning option](#fine-tuning).


### Scan a repository

After adding the rules, you can scan a repository:

```bash
python -m credentialdigger scan https://github.com/user/repo --sqlite /path/to/data.db
```

Machine learning models are not mandatory, but highly recommended in order to reduce the manual effort of reviewing the result of a scan:

```bash
python -m credentialdigger scan https://github.com/user/repo --sqlite /path/to/data.db --models PathModel SnippetModel
```


## Docker container

To have a ready-to-use instance of Credential Digger, with a user interface, you can build the docker container. 
This option requires the installation of [Docker](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/).

```bash
git clone https://github.com/SAP/credential-digger.git
cd credential-digger
cp .env.sample .env
sudo docker-compose up --build
```

The UI is available at [http://localhost:5000/](http://localhost:5000/)


## Advanced Install

Credential Digger is modular, and offers a wide choice of components and adaptations.

### Build from source

After installing the [dependencies](#install-dependencies) listed above, you can install Credential Digger as follows.

Configure a virtual environment for Python 3 (optional) and clone the main branch of the project:

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

Then, you can add the rules, install the machine learning libraries, and scan a repository as described above.

### External postgres database

Another ready-to-use instance of Credential Digger with the UI, but using a dockerized postgres database instead of a local sqlite one:

```bash
git clone https://github.com/SAP/credential-digger.git
cd credential-digger
cp .env.sample .env
vim .env  # set credentials for postgres
sudo docker-compose -f docker-compose.postgres.yml up --build
```

> **WARNING**: Differently from the sqlite version, here we need to configure the `.env` file with the credentials for postgres (by modifying `POSTGRES_USER`, `POSTGRES_PASSWORD` and `POSTGRES_DB`).

Most advanced users may also wish to use an external postgres database instead of the dockerized one we provide in our `docker-compose.postgres.yml`.





## Python library usage

When installing _credentialdigger_ from pip (or from source), you can instantiate the client and scan a repository.

Instantiate the client proper for the chosen database:

```python
# Using a Sqlite database
from credentialdigger import SqliteClient
c = SqliteClient(path='/path/to/data.db')

# Using a postgres database
from credentialdigger import PgClient
c = PgClient(dbname='my_db_name',
             dbuser='my_user',
             dbpassword='my_password',
             dbhost='localhost_or_ip',
             dbport=5432)
```

### Add rules

Add rules before launching your first scan.

```python
c.add_rules_from_file('/path/to/rules.yml')
```

### Scan a repository

```python
new_discoveries = c.scan(repo_url='https://github.com/user/repo',
                         models=['PathModel', 'SnippetModel'],
                         debug=True)
```

>  **WARNING**: Make sure you add the rules before your first scan.

>  **WARNING**: Make sure you download the models before using them in a scan.

Please refer to the [Wiki](https://github.com/SAP/credential-digger/wiki) for further information on the arguments.

#### Fine-tuning

Credential Digger offers the possibility to fine-tune the snippet model, by retraining a model on each repository scanned.
If you want to activate this option, set `generate_snippet_extractor=True` and enable the `SnippetModel` when you scan a repository. You need to install the snippet model before using the fine-tuning option.


```python
new_discoveries = c.scan(repo_url='https://github.com/user/repo',
                         models=['PathModel', 'SnippetModel'],
                         generate_snippet_extractor=True,
                         debug=True)
```



## CLI - Command Line Interface

Credential Digger also offers a simple CLI to scan a repository. The CLI supports both sqlite and postgres databases. In case of postgres, you need either to export the credentials needed to connect to the database as environment variables or to setup a `.env` file. In case of sqlite, the path of the db must be passed as argument.

Refer to the [Wiki](https://github.com/SAP/credential-digger/wiki) for all the supported commands and their usage.



## Wiki

For further information, please refer to the [Wiki](https://github.com/SAP/credential-digger/wiki)

## Contributing

We invite your participation to the project through issues and pull requests. Please refer to the [Contributing guidelines](https://github.com/SAP/credential-digger/blob/main/CONTRIBUTING.md) for how to contribute.

## News

-  [Credential Digger announcement](https://blogs.sap.com/2020/06/23/credential-digger-using-machine-learning-to-identify-hardcoded-credentials-in-github)
-  [Credential Digger is now supporting Keras machine learning models](https://github.com/SAP/credential-digger/tree/keras_models)
-  [Credential Digger approach has been published at ICISSP 2021 conference](https://jam4.sapjam.com/groups/KxkEs5HqefZnmgxTYUSSov/documents/pDwaPu8XwYHnxgWwJZP94L/slide_viewer)

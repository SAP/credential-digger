![Logo](github_assets/Logo-CD-Mint_48.png)


# Credential Digger - Supporting Keras Model

Credential Digger is a Github scanning tool that identifies hardcoded credentials (Passwords, API Keys, Secret Keys, Tokens, personal information, etc).
Credential Digger has a clear advantage compared to the other Github scanners in terms of False Positive reduction in the scan reports. 
Credential Digger is using two Machine Learning Models to identify false positives, especially in Password identification:
- Path Model: Identify the portion of code that contains fake credentials used for testing and example purposes (e.g., Unit tests).
- Snippet Model: Identify the portion of code used to authenticate with passwords, and distinguish between real and fake passwords.


## Architecture

Credential Digger finds credentials hardcoded in a repository.
The tool is composed of:
- Postgres database
- Python client
- User interface

### Database

The database is structured in the following way (arrows point to foreign keys).

![DB Structure](github_assets/database.png)


### Project structure

The project includes 3 components: a db (`sql` folder), a client
(`credentialdigger` folder), and a user interface (`ui` folder).

##### `sql`
`create_table.sql` defines the db schema.

Note that, given the `file_name` and `commit_hash` of a discovery, both the
commit and the file can be accessible at addresses:
```bash
REPO_URL/commit/COMMIT_HASH
REPO_URL/blob/COMMIT_HASH/file_name
```

##### `credentialdigger`
This client can be used to easily interact with the db.
It offers a scanner for git repositories, based on
[Hyperscan](https://www.hyperscan.io/) (others can be implemented).

Please note that the database must be up and running.

##### `ui`
The user interface can be used to easily perform scans and flag the discoveries.


## Install

1. Prepare the `.env` file and edit it with the correct data
   ```bash
   cp .env.sample .env
   vim .env  # Insert real credentials
   ```

2. Run the db using docker-compose:
   ```bash
   sudo docker-compose up --build postgres
   ```
   Consider not to expose the db port in production.
   
3. Install the dependencies for the client.
   ```bash
   sudo apt install libhyperscan-dev libpq-dev
   ```

4. Install the Python requirements from the `requirements.txt` file.
   ```bash
   pip install -r requirements.txt
   ```

5. Set which models you want to use in `ui/server.py`
```bash
    MODELS = ['SnippetModel', 'PathModel']
```
6. Run the ui:
```bash
    python3 -m ui.server
```

The ui is available at `http://localhost:5000/`

__Warning: To use the keras models, make sure the credentialdigger pypi package is NOT installed__


### Run the db on a different machine

In case the db and the client are run on different machines, then clone this
repository on both of them.

Then, execute the steps 1. and 2. as described in the installation section
above on the machine running the db, and execute the remaining steps on the machine 
running the client.

In case the db and the client/ui run on separate machines, the port of the db
must be exposed.

## Use machine learning models

Currently no pretrained keras models are provided. 

If available, the models and their respective tokenizers are expected to be found in the 
`models_data` directory, in their respective subdirectories. Model hyperparameters can be found in the `models/keras_support` folder .

Note that `snippet_extractor` is still a fasttext model.



### File Path Model
The File Path Model classifies a discovery as false positive according to its file
path when it indicates that the code portion is used for test or example. A pre-trained Path Model [is available here](https://github.com/SAP/credential-digger/releases/download/v1.0.0/path_model-1.0.0.tar.gz).

### Code Snippet Model

The code Snippet model identifies the password based authentication in a code and differeciate between real and fake passwords.

WARNING: This Model is pre-trained with synthetic data in order to protect privacy. It will help to reduce the False Positives related to password recongnition but with a lower precision compared to a Model pre-trained with real data.

## Usage (client)

```python
from credentialdigger.cli import Client
c = Client(dbname='MYDB', dbuser='MYUSER', dbpassword='*****',
           dbhost='localhost', dbport=5432)
```


## Wiki
Refer to the [Wiki](https://github.com/SAP/credential-digger/wiki) for further information.


## News
- [Credential Digger announcement](https://blogs.sap.com/2020/06/23/credential-digger-using-machine-learning-to-identify-hardcoded-credentials-in-github)

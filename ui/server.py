import os
import sys
import threading
from collections import defaultdict
from enum import Enum
from itertools import groupby

import yaml
from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, redirect, render_template, request, send_file, url_for
from flask_jwt_extended import create_access_token, JWTManager
from werkzeug.utils import secure_filename

load_dotenv()

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
if os.getenv("LOCAL_REPO") == 'True':
    # Load credentialdigger from local repo instead of pip
    sys.path.insert(0, os.path.join(APP_ROOT, '..'))

from backend import PgUiClient, SqliteUiClient  # noqa

app = Flask('__name__', static_folder=os.path.join(APP_ROOT, './res'),
            template_folder=os.path.join(APP_ROOT, './templates'))
app.config['UPLOAD_FOLDER'] = os.path.join(APP_ROOT, './backend')
app.config['DEBUG'] = True  # Remove this line in production
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

# HTTPS = True if both a certificate and private key exist, False otherwise.
HTTPS = (os.getenv("SSL_certificate") !=
         '' and os.getenv("SSL_private_key") != '')

if os.getenv('USE_PG') == 'True':
    app.logger.info('Use Postgres Client')
    c = PgUiClient(dbname=os.getenv('POSTGRES_DB'),
                   dbuser=os.getenv('POSTGRES_USER'),
                   dbpassword=os.getenv('POSTGRES_PASSWORD'),
                   dbhost=os.getenv('DBHOST'),
                   dbport=os.getenv('DBPORT'))
else:
    app.logger.info('Use Sqlite Client')
    c = SqliteUiClient(path=os.path.join(APP_ROOT, './data.db'))
c.add_rules_from_file(os.path.join(APP_ROOT, './backend/rules.yml'))


# ################### UTILS ####################

def _get_active_scans():
    active_scans = []
    for thread in threading.enumerate():
        if thread.name.startswith("credentialdigger"):
            active_scans.append(thread.name.split("@")[1])
    return active_scans


def _get_rules():
    # There may be missing ids. Restructure as a dict
    # There may be no mapping between list index and rule id
    # Not very elegant, but avoid IndexError
    rules = c.get_rules()
    cat = set()
    rulesdict = {}
    for rule in rules:
        rulesdict[rule['id']] = rule
        cat.add(rule['category'])

    return rulesdict, cat


# Store JWT's value for every connected user
registered_tokens = []


@app.before_request
def before_request():
    """
        Treat all incoming requests before-hand. 
        If the user is not yet logged in, he/she will be redirected towards the login page.
    """
    if(HTTPS):
        token = request.cookies.get('AUTH')
        if(token not in registered_tokens):
            if(request.endpoint != 'login' and '/res/' not in request.path):
                return render_template('login.html',
                                       msg='🔒 Enter your secret key to access the scanner:')

# ################### ROUTES ####################


@app.route('/login', methods=['POST', 'GET'])
def login():
    # If the HTTPS protocol is not in use, then the login feature will be disabled.
    if(not HTTPS):
        redirect(url_for('root'))
    else:
        if(request.method == 'POST'):
            auth_key = request.form['auth_key']
            if(auth_key != os.getenv('AUTH_KEY')):
                redirect(url_for('login'))
                return render_template('login.html',
                                       msg='❌ Wrong key, please try again:')
            # We generate a UUID to be saved as a JWT's value
            import uuid
            access_token = create_access_token(identity=str(uuid.uuid1()))
            resp = make_response(redirect(url_for('root')))

            # We store the HttpOnly token on the browser. A HttpOnly token
            # cannot be accessed by javascript for security purposes
            resp.set_cookie('AUTH', value=str(access_token), httponly=True,
                            secure=True)

            # Store the new JWT's value in the registered_tokens list
            registered_tokens.append(str(access_token))
            return resp
        else:
            redirect(url_for('login'))
            return render_template('login.html',
                                   msg='🔒 Enter your secret key to access the scanner:')


@app.route('/logout')
def logout():
    """
    The user loses his access to the tool when his JWT's value no longer exists in the local
    registered_tokens list.
    """
    token = request.cookies.get('AUTH')
    registered_tokens.remove(token)
    resp = make_response(redirect(url_for('root')))
    return resp


@app.route('/')
def root():
    repos = c.get_repos()

    # Total num of discoveries
    tot_discoveries = c.get_discoveries_count()

    rulesdict, cat = _get_rules()

    return render_template('repos.html',
                           tot_discoveries=tot_discoveries,
                           len_repos=len(repos),
                           len_rules=len(rulesdict),
                           categories=list(cat))


@app.route('/files', methods=['GET'])
def files():
    # Get all the discoveries of this repository
    url = request.args.get('url')
    rulesdict, cat = _get_rules()
    discoveries_count = c.get_discoveries_count(repo_url=url)
    active_scans = _get_active_scans()
    scanning = url in active_scans

    return render_template('discoveries/files.html',
                           url=url,
                           discoveries_count=discoveries_count,
                           scanning=scanning,
                           categories=list(cat))


@app.route('/discoveries', methods=['GET'])
def discoveries():
    # Get all the discoveries of this repository
    url = request.args.get('url')
    file = request.args.get('file')
    rulesdict, cat = _get_rules()
    discoveries_count = c.get_discoveries_count(repo_url=url, file_name=file)
    active_scans = _get_active_scans()
    scanning = url in active_scans

    if file:
        return render_template('discoveries/file.html',
                               url=url,
                               file=file,
                               discoveries_count=discoveries_count,
                               scanning=scanning,
                               categories=list(cat))
    else:
        return render_template('discoveries/discoveries.html',
                               url=url,
                               discoveries_count=discoveries_count,
                               scanning=scanning,
                               categories=list(cat))


@app.route('/rules')
def rules():
    rules = c.get_rules()
    return render_template('rules.html', rules=rules)


@app.route('/delete_repo', methods=['POST'])
def delete_repo():
    c.delete_repo(**request.values)
    return redirect('/')


@app.route('/add_rule', methods=['POST'])
def add_rule():
    c.add_rule(**request.values)
    return redirect('/rules')


@app.route('/delete_rule', methods=['POST'])
def delete_rule():
    c.delete_rule(**request.values)
    return redirect('/rules')


@app.route('/upload_rule', methods=['POST'])
def upload_rule():
    file = request.files['filename']
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    c.add_rules_from_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return redirect('/rules')


@app.route('/download_rule')
def download_rule():
    rules = c.get_rules()
    dictrules = defaultdict(list)
    for rule in rules:
        dictrules['rules'].append({
            'regex': rule['regex'],
            'category': rule['category'],
            'description': rule['description']
        })

    with open(os.path.join(APP_ROOT, './backend/Downloadrules.yml'), 'w') as file:
        yaml.dump(dict(dictrules), file)
    return send_file(os.path.join(APP_ROOT, './backend/Downloadrules.yml'), as_attachment=True)


# ################### JSON APIs ####################

@app.route('/scan_repo', methods=['POST'])
def scan_repo():
    # Get scan properties
    repo_link = request.form['repolink'].strip()
    rules_to_use = request.form.get('rule_to_use')
    use_snippet_model = request.form.get('snippetModel')
    use_path_model = request.form.get('pathModel')
    # If the form does not contain the 'Force' checkbox,
    # then 'forceScan' will be set to False; thus, ignored.
    force_scan = request.form.get('forceScan') == 'force'
    git_token = request.form.get('gitToken')
    local_repo = not (repo_link.startswith(
        'http://') or repo_link.startswith('https://'))

    url_is_valid, err_code = c.check_repo(repo_link, git_token, local_repo)
    if not url_is_valid:
        return err_code, 401

    # Set up models
    models = []
    if use_path_model == 'path':
        models.append('PathModel')
    if use_snippet_model == 'snippet':
        models.append('SnippetModel')

    # Scan
    args = {
        "repo_url": repo_link,
        "models": models,
        "force": force_scan,
        "git_token": git_token,
        "local_repo": local_repo
    }
    if rules_to_use != 'all':
        args["category"] = rules_to_use
    thread = threading.Thread(
        name=f"credentialdigger@{repo_link}", target=c.scan, kwargs=args)
    thread.start()

    return 'OK', 200


@app.route('/get_repos')
def get_repos():
    active_scans = _get_active_scans()

    repos = c.get_repos()
    for repo in repos:
        repo['lendiscoveries'] = c.get_discoveries_count(repo['url'])
        repo['scan_active'] = False
        if repo['url'] in active_scans:
            repo['scan_active'] = True

    return jsonify(repos)


@app.route('/get_files', methods=['GET'])
def get_files():
    # Get all the discoveries of this repository
    url = request.args.get('url')
    files = c.get_files_summary(url)
    return jsonify(files)


@app.route('/get_discoveries', methods=['GET'])
def get_discoveries():
    # Get all the discoveries of this repository
    url = request.args.get('url')
    file_name = request.args.get('file')
    where = request.args['search[value]']
    where = where if len(where) > 0 else None
    limit = int(request.args['length'])
    offset = int(request.args['start'])
    order_by_index = request.args['order[0][column]']
    order_by = request.args[f'columns[{order_by_index}][data]']
    order_direction = request.args['order[0][dir]']

    # Determine the state filter value
    col_index = 0
    state_filter = None
    while f'columns[{col_index}][data]' in request.args:
        if request.args[f'columns[{col_index}][data]'] == 'state':
            state_filter = request.args[f'columns[{col_index}][search][value]']
            if len(state_filter) == 0 or state_filter == 'all':
                state_filter = None
            break
        col_index += 1

    discoveries_count, discoveries = c.get_discoveries(
        repo_url=url, file_name=file_name, state_filter=state_filter,
        where=where, limit=limit, offset=offset, order_by=order_by,
        order_direction=order_direction)

    # Add the category to each discovery
    rulesdict, cat = _get_rules()
    categories_found = set()
    for discovery in discoveries:
        if discovery['rule_id']:
            discovery['category'] = rulesdict[discovery['rule_id']]['category']
        else:
            discovery['category'] = '(rule deleted)'
        categories_found.add(discovery['category'])

    # Build the response json
    class States(Enum):
        new = 0
        false_positive = 1
        addressing = 2
        not_relevant = 3

    discoveries = sorted(discoveries, key=lambda i: (
        i["snippet"], i["category"], States[i["state"]].value))
    response = {
        "recordsTotal": discoveries_count,
        "recordsFiltered": discoveries_count,
        "data": sorted([
            {
                "snippet": keys[0],
                "category": keys[1],
                "state": States(keys[2]).name,
                "occurrences": [
                    {
                        "file_name": i["file_name"],
                        "line_number": i["line_number"],
                        "commit_id": i["commit_id"],
                        "id": i["id"]
                    } for i in list(values)
                ],
            }
            for keys, values in groupby(
                discoveries, lambda i: (i["snippet"], i["category"], States[i["state"]].value))
        ], key=lambda i: States[i[order_by]].value, reverse=order_direction == 'desc')
    }

    return jsonify(response)


@app.route('/get_scan_status')
def get_scan_status():
    url = request.args.get('url')
    active_scans = _get_active_scans()
    return jsonify({"scanning": url in active_scans})


@app.route('/update_discovery_group', methods=['POST'])
def update_discovery_group():
    state = request.form.get('state')
    url = request.form.get('url')
    file = request.form.get('file')
    snippet = request.form.get('snippet')
    response = c.update_discovery_group(state, url, file, snippet)
    if response is False:
        return 'Error in updatating the discovery group', 500
    else:
        return 'OK', 200


jwt = JWTManager(app)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

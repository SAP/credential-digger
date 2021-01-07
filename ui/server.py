import os
import sys
from collections import defaultdict
from itertools import groupby
import threading

import yaml
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename

load_dotenv()

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
if os.getenv("LOCAL_REPO") == 'True':
    # Load credentialdigger from local repo instead of pip
    sys.path.insert(0, os.path.join(APP_ROOT, '..'))

from credentialdigger import PgClient, SqliteClient  # noqa

app = Flask('__name__', static_folder=os.path.join(APP_ROOT, './res'),
            template_folder=os.path.join(APP_ROOT, './templates'))
app.config['UPLOAD_FOLDER'] = os.path.join(APP_ROOT, './backend')
app.config['DEBUG'] = True  # Remove this line in production

if os.getenv('USE_PG') == 'True':
    app.logger.info('Use Postgres Client')
    c = PgClient(dbname=os.getenv('POSTGRES_DB'),
                 dbuser=os.getenv('POSTGRES_USER'),
                 dbpassword=os.getenv('POSTGRES_PASSWORD'),
                 dbhost=os.getenv('DBHOST'),
                 dbport=os.getenv('DBPORT'))
else:
    app.logger.info('Use Sqlite Client')
    c = SqliteClient(path=os.path.join(APP_ROOT, './data.db'))
c.add_rules_from_file(os.path.join(APP_ROOT, './backend/rules.yml'))


# ################### ROUTES ####################
@app.route('/')
def root():
    repos = c.get_repos()

    # Discoveries per repo
    for repo in repos:
        repo['lendiscoveries'] = len(c.get_discoveries(repo['url']))

    # Total num of discoveries
    tot_discoveries = sum(map(lambda r: r.get('lendiscoveries', 0), repos))

    rules = c.get_rules()

    # Get rule categories
    cat = set()
    for rule in rules:
        cat.add(rule['category'])

    return render_template('repos.html',
                           rules=rules,
                           tot_discoveries=tot_discoveries,
                           len_repos=len(repos),
                           len_rules=len(rules),
                           categories=list(cat))


@app.route('/files', methods=['GET'])
def files():
    # Get all the discoveries of this repository
    url = request.args.get('url')

    rules = c.get_rules()
    # There may be missing ids. Restructure as a dict
    # There may be no mapping between list index and rule id
    # Not very elegant, but avoid IndexError
    cat = set()
    rulesdict = {}
    for rule in rules:
        rulesdict[rule['id']] = rule
        cat.add(rule['category'])
    return render_template('discoveries/files.html',
                           url=url,
                           categories=list(cat))


@app.route('/discoveries', methods=['GET'])
def discoveries():
    # Get all the discoveries of this repository
    url = request.args.get('url')
    file = request.args.get('file')

    rules = c.get_rules()
    # There may be missing ids. Restructure as a dict
    # There may be no mapping between list index and rule id
    # Not very elegant, but avoid IndexError
    cat = set()
    rulesdict = {}
    for rule in rules:
        rulesdict[rule['id']] = rule
        cat.add(rule['category'])

    if file:
        return render_template('discoveries/file.html',
                               url=url,
                               file=file,
                               categories=list(cat))
    else:
        return render_template('discoveries/discoveries.html',
                               url=url,
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
    repolink = request.form['repolink'].strip()
    rulesToUse = request.form.get('rule_to_use')
    useSnippetModel = request.form.get('snippetModel')
    usePathModel = request.form.get('pathModel')
    # If the form does not contain the 'Force' checkbox,
    # then 'forceScan' will be set to False; thus, ignored.
    forceScan = request.form.get('forceScan') == 'force'

    # Set up models
    models = []
    if usePathModel == 'path':
        models.append('PathModel')
    if useSnippetModel == 'snippet':
        models.append('SnippetModel')

    # Scan
    args = {
        "repo_url": repolink,
        "models": models,
        "force": forceScan
    }
    if rulesToUse != 'all':
        args["category"] = rulesToUse
    thread = threading.Thread(
        name=f"credentialdigger@{repolink}", target=c.scan, kwargs=args)
    thread.start()

    return 'OK', 200


@app.route('/get_active_scans')
def get_active_scans():
    active_scans = []
    for thread in threading.enumerate():
        if thread.name.startswith("credentialdigger"):
            active_scans.append(thread.name.split("@")[1])
    return jsonify(active_scans)


@app.route('/get_repos')
def get_repos():
    active_scans = []
    for thread in threading.enumerate():
        if thread.name.startswith("credentialdigger"):
            active_scans.append(thread.name.split("@")[1])

    repos = c.get_repos()
    for repo in repos:
        repo['lendiscoveries'] = len(c.get_discoveries(repo['url']))
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
    file = request.args.get('file')
    if file is None:
        discoveries = c.get_discoveries(url)
    else:
        discoveries = c.get_discoveries(url, file)

    # There may be missing ids. Restructure as a dict
    # There may be no mapping between list index and rule id
    # Not very elegant, but avoid IndexError
    rules = c.get_rules()
    rulesdict = {}
    for rule in rules:
        rulesdict[rule['id']] = rule

    # Add the category to each discovery
    categories_found = set()
    for discovery in discoveries:
        discovery['category'] = rulesdict[discovery['rule_id']]['category']
        categories_found.add(discovery['category'])

    discoveries = sorted(discoveries, key=lambda i: (
        i["snippet"], i["category"], i["state"]))
    response = [
        {
            "snippet": keys[0],
            "category": keys[1],
            "state": keys[2],
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
            discoveries, lambda i: (i["snippet"], i["category"], i["state"]))
    ]

    return jsonify(response)


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


app.run(host='0.0.0.0', port=5000)

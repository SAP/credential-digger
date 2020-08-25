import os
import yaml
from collections import defaultdict

from credentialdigger import PgClient, SqliteClient
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, send_file
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask('__name__', static_folder='res')
app.config['UPLOAD_FOLDER'] = './backend'
app.config['DEBUG'] = True  # Remove this line in production

if os.getenv('USE_PG'):
    app.logger.info('Use Postgres Client')
    c = PgClient(dbname=os.getenv('POSTGRES_DB'),
                 dbuser=os.getenv('POSTGRES_USER'),
                 dbpassword=os.getenv('POSTGRES_PASSWORD'),
                 dbhost=os.getenv('DBHOST'),
                 dbport=int(os.getenv('DBPORT')))
else:
    app.logger.info('Use Sqlite Client')
    c = SqliteClient(path='/credential-digger-ui/data.db')
c.add_rules_from_file('/credential-digger-ui/backend/rules.yml')


# ################### UI ####################
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
                           repos=repos,
                           rules=rules,
                           tot_discoveries=tot_discoveries,
                           len_repos=len(repos),
                           len_rules=len(rules),
                           categories=list(cat))


@app.route('/discoveries', methods=['GET'])
def discoveries():
    # Get all the discoveries of this repository
    url = request.args.get('url')
    discoveries = c.get_discoveries(url)

    rules = c.get_rules()
    # There may be missing ids. Restructure as a dict
    # There may be no mapping between list index and rule id
    # Not very elegant, but avoid IndexError
    rulesdict = {}
    for rule in rules:
        rulesdict[rule['id']] = rule

    categories_found = set()

    # Add the category to each discovery
    for discovery in discoveries:
        discovery['cat'] = rulesdict[discovery['rule_id']]['category']
        categories_found.add(discovery['cat'])

    return render_template('discoveries.html',
                           url=url,
                           discoveries=discoveries,
                           lendiscoveries=len(discoveries),
                           all_categories=categories_found,
                           ruleslist=rules)


@app.route('/rules')
def rules():
    rules = c.get_rules()
    return render_template('rules.html', rules=rules)


@app.route('/fp/<id>', methods=['GET'])
def fp(id):
    url = request.args.get('url')
    c.update_discovery(id, 'false_positive')
    return redirect('/discoveries?url=%s' % url)


@app.route('/addressing/<id>', methods=['GET'])
def addressing(id):
    url = request.args.get('url')
    c.update_discovery(id, 'addressing')
    return redirect('/discoveries?url=%s' % url)


@app.route('/not_relevant/<id>', methods=['GET'])
def not_relevant(id):
    url = request.args.get('url')
    c.update_discovery(id, 'not_relevant')
    return redirect('/discoveries?url=%s' % url)


@app.route('/scan_repo', methods=['POST'])
def scan_repo():
    # Get scan properties
    repolink = request.form['repolink']
    rulesToUse = request.form.get('rule_to_use')
    useSnippetModel = request.form.get('snippetModel')
    usePathModel = request.form.get('pathModel')
    # Set up models
    models = []
    if usePathModel == 'path':
        models.append('PathModel')
    if useSnippetModel == 'snippet':
        models.append('SnippetModel')
    # Scan
    if rulesToUse == 'all':
        c.scan(repolink, models=models)
    else:
        c.scan(repolink, models=models, category=rulesToUse)
    return redirect('/')


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

    with open('./backend/Downloadrules.yml', 'w') as file:
        yaml.dump(dict(dictrules), file)
    return send_file('./backend/Downloadrules.yml', as_attachment=True)


app.run(host='0.0.0.0', port=5000)

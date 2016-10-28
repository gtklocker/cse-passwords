from flask import Flask, request, render_template
from flask_redis import FlaskRedis
import json
import requests

app = Flask(__name__)
redis_store = FlaskRedis(app)

def assert_creds(creds):
    assert type(creds) is dict
    assert set(creds.keys()) == set(['user', 'pass'])

def are_correct_credentials(url, creds):
    assert_creds(creds)
    return requests.head(url, auth=(creds['user'], creds['pass'])).status_code == requests.codes.ok

def save_url(url, creds):
    assert_creds(creds)
    url_id = redis_store.incr('new_url_id')
    redis_store.hmset('url:%s' % url_id, {
        'url': url,
        'user': creds['user'],
        'pass': creds['pass']
    })
    redis_store.rpush('url_ids', url_id)

class IncorrectCredsError(Exception):
    pass

# TODO: Handle sites that don't requre passwords anyway
@app.route('/submit', methods=['POST'])
def do_submit():
    error = True
    try:
        url = request.form['url']
        creds = {
            'user': request.form['user'],
            'pass': request.form['pass']
        }

        if are_correct_credentials(url, creds):
            save_url(url, creds)
            error = False
        else:
            raise IncorrectCredsError
    except (KeyError, IncorrectCredsError):
        pass
    finally:
        return render_template('submitted.html', error=error)

@app.route('/submit', methods=['GET'])
def view_submit():
    return render_template('submit.html')

# TODO: modify redis connection to encode/decode automatically and remove this
decode_dict = lambda strdict: {k.decode('utf8'): v.decode('utf8') for k, v in strdict.items()}

@app.route('/')
def index():
    urls = []
    for url_id in redis_store.lrange('url_ids', 0, -1):
        urls.append(redis_store.hgetall('url:%d' % int(url_id)))
    return render_template('index.html', urls=map(decode_dict, urls))
    #return str(are_correct_credentials('http://www.cs.uoi.gr/~stergios/teaching/mye007/lectures/lectures_gr.html', ('mye007sec16', 'mye007sec16')))

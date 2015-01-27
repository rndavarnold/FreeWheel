import flask
import redis
from flask import Flask
from flask import Response, request
from flask import jsonify
from functools import wraps
from flask import request, Response
import json
import os, sys
import uuid
import hashlib

sys.path.append(os.path.abspath(os.path.join(__file__, '../..')))
from db_objects import organizations
import app_config

app = Flask(__name__)


def hash_password(password):
    return hashlib.md5(password).hexdigest()

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    org = organization.Organizations()
    org.laod(name=username, passord=hash_password(password))
    if org.dump() and org.get('enabled'):
        request.headers['api_key'] = org.get('api_key')
        return True
    else:
        return False

def check_api_key(api_key):
    r = redis.Redis(app_config.redis.get('host'),
                    password=app_config.redis.get('auth'))
    if api_key == r.get('master_api_key'):
        return True
    org = organizations.Organizations()
    org.load(api_key=api_key)
    if org.dump():
        return True
    else:
        return False

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_headers = request.authorization
        api_key = request.headers.get('api_key')
        if check_api_key(api_key):
            return f(*args, **kwargs)
        elif auth_headers and check_auth(auth_headers.username, auth_headers.password):
            return f(*args, **kwargs)
        else:
            return authenticate()
        return f(*args, **kwargs)
    return decorated


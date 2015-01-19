import flask
from flask import Flask
from flask import Response, request
from functools import wraps
from flask import request, Response
import json
import redis

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.abspath(__file__), '../..')))
import db_objects

app = Flask(__name__)

def check_org(json_obj):
    org = db_objects.orgnanizations.Organization()
    org.load(name=json_obj.get('organization'))
    print json.dumps(org.dump(), separators=(',', ':'), indent=4, sort_keys=True)
        

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == 'secret'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@requires_auth
@app.route('/service/<service_id>', methods=['PUT', 'GET'])
def service_id(service_id):
    # work with existing services
    if request.method == 'PUT':
        # update service
        pass
    elif request.method == 'GET':
        # return service definition
        pass
    
@requires_auth
@app.route('/service/', methods=['POST', 'GET'])
def service():
    if request.method == 'POST':
        print json.dumps(request.json, separators=(',', ':'), indent=4, sort_keys=True)
        check_org(request.json)
        return Response(status=200)

    elif request.method == 'GET':
        # list services
        return Response(status=200)

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('--port', dest='port', type='int', default=8080)
    parser.add_option('--ip', dest='ip', type='str', default='0.0.0.0')
    parser.add_option('--debug', dest='debug', action='store_true', default=False)
    opt, arg = parser.parse_args()
    app.run(host=opt.ip, port=opt.port, debug=opt.debug)


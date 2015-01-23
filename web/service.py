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
import db_objects.organizations
import db_objects.service_dependencies
import db_objects.service
import auth
app = Flask(__name__)

@app.route('/service/<service_id>', methods=['PUT', 'GET'])
@auth.requires_auth
def service_id(service_id):
    # work with existing services
    if request.method == 'PUT':
        # update service
        pass
    elif request.method == 'GET':
        # return service definition
        pass
    
@app.route('/service/', methods=['POST', 'GET'])
@auth.requires_auth
def service():
    if request.method == 'POST':
        j = request.json
        dependencies = {}
        org = db_objects.organizations.Organizations()
        org.load(api_key=request.headers.get('api_key'))
        org_dump = org.dump()
        org_id = org_dump.get('id')

        if j.get('dependencies'):
            dependencies = j.pop('dependencies')

        j['org_id'] = org_id
        svc = db_objects.service.Services()
        svc.load(**j)

        if svc.dump():
            return Response(json.dumps(dict(error='cannot create requested item. already exists')), status=400, mimetype='application/json')

        for k, v in j.items():
            svc.set(k, v)
        svc.insert()

        for k, v in dependencies.items():
            name = v.pop('id')
            v['name'] = name
            v['engine'] = k                
            #print json.dumps(v, separators=(',', ':'), sort_keys=True, indent=4)
            svc_dep = db_objects.service_dependencies.ServiceDependencies()
            for key, value in v.items():
                svc_dep.set(key, value)
            svc_dep.insert() 

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


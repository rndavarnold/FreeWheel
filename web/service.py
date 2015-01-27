import flask
from flask import Flask
from flask import Response, request
from functools import wraps
from flask import request, Response
import json
import redis
import uuid

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.abspath(__file__), '../..')))
import db_objects
import db_objects.organizations
import db_objects.service_dependencies
import db_objects.service_loadbalancers as svc_lb
import db_objects.service
import auth
app = Flask(__name__)

def check_fields():
    error_fields = []
    svc = db_objects.service.Services()
    lb =  svc_lb.ServiceLoadBalancers()
    svc_dep = db_objects.service_dependencies.ServiceDependencies()
    
    j = request.json
    
    load_balancer = None
    if 'load_balancer' in j.keys():
        load_balancer = j.pop('load_balancer')
    
    dependencies = None
    if 'dependencies' in j.keys():
        dependencies = j.pop('dependencies')
    
    for key in j:
        if key not in svc.get_fields():
            error_fields.append(key)
            continue
    
    if load_balancer:
        for key in load_balancer:
            if key not in lb.get_fields():
                error_fields.append(key)

    if dependencies:
        for dep in dependencies:
            for key in dependencies.get(dep):
                if key not in svc_dep.get_fields():
                    error_fields.append(key)
                
    if error_fields:
        return False
    else:
        return True

@app.route('/service/<service_api_key>', methods=['PUT', 'GET'])
@auth.requires_auth
def service_id(service_api_key):
    # work with existing services
    if request.method == 'PUT':
        org = db_objects.organizations.Organizations()
        org.load(api_key=request.headers.get('api_key'))
        lb = None
        dep = None
        if not check_fields():
            return Response(json.dumps(dict(error='fields incorrect')),
                            status=400,
                            mimetype='application/json')
               
        j = request.json
        print json.dumps(j, sort_keys=True, indent=4, separators=(',', ':'))
        if j.get('load_balancer'):
            lb = j.pop('load_balancer')

        if j.get('dependencies'):
            dep = j.pop('dependencies')

        # update service definition
        svc = db_objects.service.Services()
        svc.load(service_api_key=service_api_key,
                 org_id=org.get('id'))    

        # if service doesn't exist return 400
        if not svc.dump():
            return Response(json.dumps(dict(error='service does not exist')),
                            status=400,
                            mimetype='application/json')
            
        for k, v in j.items():
            # cant allow users to change their service api key
            # as this could give them access to other services outside of their organization
            if k == 'service_api_key': continue
            if k == 'service_name': continue
            svc.set(k, v) 
        if j:
            svc.update()
        
        if lb:
            svc_lb = db_objects.service_loadbalancers.ServiceLoadBalancers()
            svc_lb.load(service_id=svc.get('id'))
            for k, v in lb.items():
                svc_lb.set(k, v)
            svc_lb.update()
        else:
            svc_lb = db_objects.service_loadbalancers.ServiceLoadBalancers()
            svc_lb.load(service_id=svc.get('id'))
            if svc_lb.dump():
                svc_lb.delete()
        if dep:
            svc_dep = db_objects.service_dependencies.ServiceDependencies()
            svc_dep.load(service_id=svc.get('id'))
            for k, v in dep.items():
                svc_dep.set(k, v)
            svc.update()
        else:
            svc_dep = db_objects.service_dependencies.ServiceDependencies()
            svc_dep.load(service_id=svc.get('id'))
            if svc_dep.dump():
                svc_dep.delete()
        return Response(json.dumps(dict(success='service updated')),
                        status=200,
                        mimetype='application/json')
                            
    elif request.method == 'GET':
        svc = db_objects.service.Services()
        org = db_objects.organizations.Organizations()
        org.load(api_key=request.headers.get('api_key'))
        svc.load(org_id=org.get('id'), service_api_key=service_api_key)
        svc_json = svc.dump()
        if not svc.dump():
            return Response(json.dumps(dict(error='service does not exist')),
                            status=400,
                            mimetype='application/json')
        else:
            service_id = svc.get('id')
            svc_lb = db_objects.service_loadbalancers.ServiceLoadBalancers()
            svc_lb.load(service_id=service_id)
            print json.dumps(svc_lb.dump(), indent=4, separators=(',', ':'))
            if svc_lb.dump():
                svc_json['load_balancer'] = svc_lb.dump()
            svc_dep = db_objects.service_dependencies.ServiceDependencies()
            svc_dep.load(service_id=service_id)
            print json.dumps(svc_dep.dump(), indent=4, separators=(',', ':'))
            if svc_dep.dump():
                svc_json['dependencies'] = svc_dep.dump()
            return Response(json.dumps(svc_json),
                            status=200,
                            mimetype='application/json')
     
@app.route('/service/', methods=['POST', 'GET'])
@auth.requires_auth
def service():
    if request.method == 'POST':
        j = request.json
        dependencies = {}
        org = db_objects.organizations.Organizations()
        org.load(api_key=request.headers.get('api_key'))
        org_dump = org.dump()

        if not org_dump.get('enabled'):
            e = 'cannot create requested item. account is disabled'
            return Response(json.dumps(dict(error=e)), 
                            status=400, 
                            mimetype='application/json')

        org_id = org_dump.get('id')

        if j.get('dependencies'):
            dependencies = j.pop('dependencies')

        if j.get('load_balancer'):
            load_balancer = j.pop('load_balancer')

        j['org_id'] = org_id
        svc = db_objects.service.Services()
        svc.load(service_name=j.get('service_name'), org_id=org_id)

        if svc.dump():
            e = 'cannot create requested item. already exists'
            return Response(json.dumps(dict(error=e)), 
                            status=400, 
                            mimetype='application/json')

        for k, v in j.items():
            svc.set(k, v)
        svc.set('service_api_key', uuid.uuid4())
        svc.insert()
        svc.load(**j)

        for k, v in dependencies.items():
            v['name'] = svc.get('service_name')
            v['engine'] = k                
            #print json.dumps(v, separators=(',', ':'), sort_keys=True, indent=4)
            svc_dep = db_objects.service_dependencies.ServiceDependencies()
            svc_dep.set('service_id', svc.get('id'))
            for key, value in v.items():
                svc_dep.set(key, value)
            svc_dep.insert() 
        lb = svc_lb.ServiceLoadBalancers()
        for k, v in load_balancer.items():
            lb.set(k, v)
        lb.set('service_id', svc.get('id'))
        lb.insert()       
        return Response(json.dumps(dict(success='created service', 
                                        service_api_key=str(svc.get('service_api_key')))), 
                        status=200, 
                        mimetype='application/json')

    elif request.method == 'GET':
        svcs = []
        org = db_objects.organizations.Organizations()
        org.load(id=request.headers.get('api_key'))
        svc = db_objects.service.Services()
        for s in svc.loadall(org_id=org.get('id')):
            service_id = s.get('service_id')
            lb = db_objects.service_loadbalancers.ServiceLoadBalancers()
            lb.load(service_id=service_id)
            if lb.dump():
                s['load_balancer'] = lb.dump()
            dep = db_objects.service_dependencies.ServiceDependencies()
            dep.load(service_id=service_id)
            if dep.dump():
                s['dependencies'] = dep.dump()
            svcs.append(s)
        return Response(json.dumps(svcs),
                        status=200,
                        mimetype='application/json')

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('--port', dest='port', type='int', default=8080)
    parser.add_option('--ip', dest='ip', type='str', default='0.0.0.0')
    parser.add_option('--debug', dest='debug', action='store_true', default=False)
    opt, arg = parser.parse_args()
    app.run(host=opt.ip, port=opt.port, debug=opt.debug)


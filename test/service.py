import json, requests, os
import string
import random
import random
import urlparse
import sys

svc_url = 'http://localhost:8085/service/'

headers = {'Content-Type': 'application/json',
           'api_key': 'e8b11e26-574a-41e2-b6ff-07f1f2735239'}

svc_def = {
    "service_name": "user-signup",
    "service_port": 80,
    "instance_type": "m3.large",
    "instances": 3,
    "user": "ubuntu",
    "ami_id": "ami-9eaa1cf6",
    "region": "us-east-1",
    "git_url": "https://github.com/djaboxx/TestProject",
    "configuration_url": "https://github.com/djaboxx/TestProject",
    "load_balancer": {
        "healthcheck_interval": 10,
        "healthy_threshold": 3,
        "unhealthy_threshold": 5,
        "target": "HTTP:80/healthcheck"
    },
    "dependencies": {
        "mysql": {
            "size": 10,
            "instance_type": "db.m1.small",
            "user": "root",
            "connection_settings_file": "/etc/database.conf",
            "password": "hunter2"
        }
    }
}

# create initial service
resp = requests.post(svc_url, data=json.dumps(svc_def), headers=headers)
assert(resp.status_code == 200)
service_api_key = resp.json().get('service_api_key')

resp = requests.get(urlparse.urljoin(svc_url, service_api_key), headers=headers)
assert(resp.json() == json.loads(json.dumps(svc_def)))
assert(resp.status_code == 200)

# attempt to create the same service again
resp = requests.post(svc_url, data=json.dumps(svc_def), headers=headers)
assert(resp.status_code == 400)

if 'y' not in raw_input('continue? '): sys.exit()

# attempt to remove the load balancer
print json.dumps(svc_def, sort_keys=True, indent=4, separators=(',', ':'))
resp = requests.put(urlparse.urljoin(svc_url, service_api_key), data=json.dumps(svc_def), headers=headers)
assert(resp.status_code == 200)

resp = requests.get(urlparse.urljoin(svc_url, service_api_key), headers=headers)
print resp.text
assert(resp.status_code == 200)


import json, requests, os
import string
import random
import random
org_url = 'http://localhost:8082/organization/'

rand_string = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(16))

org_def = {
  "domain": 'dev.custom-integrations.com.',
  "name": 'qa',
  "admin_email": "x@att.net",
  "password": "password123",
  "aws_access_key_id": "AKIAIN4R4JU67R7AXT6A",
  "aws_secret_access_key": "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"
}

headers = {'Content-Type': 'application/json'}

# create initial organization
resp = requests.post(org_url, data=json.dumps(org_def), headers=headers)
headers['api_key'] = resp.json().get('api_key')
assert(resp.status_code == 200)

# get organization
print headers
resp = requests.get(org_url, params=dict(name=org_def.get('name'), domain=org_def.get('domain')), headers=dict(api_key=headers.get('api_key')))
try:
    assert(resp.status_code == 200)
except:
    print resp.text

# update organization        
org_def['domain'] = 'dev.custom-integrations.org.'
resp = requests.put(org_url, data=json.dumps(org_def), headers=headers)
assert(resp.status_code == 200)


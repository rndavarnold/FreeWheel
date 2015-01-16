#!/usr/bin/python
import redis
import json
import sys

def retrieve(config_path, service_name):
    j = json.load(open(config_path, 'r'))
    j['service_name'] = service_name
    r = redis.Redis()
    r.lpush('service_configs', json.dumps(j)) 

if __name__ == '__main__':
    retrieve(sys.argv[1], sys.argv[2])   

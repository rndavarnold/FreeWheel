import subprocess
from ansible import runner
import json
import redis
import os
import boto
from ConfigParser import RawConfigParser

# we need to watch the git repository of the project deployment.
# if that changed then we need to update the configs and playbooks that we have.
# this script will do that.
# we dont need to deploy yet, we just need to make sure the deployment plan 
# store in our systems. We will need to also watch the git urls that are found in the configuration
# files, but that will be performed in another process.
with open('/etc/gitpoller.conf', 'r') as conf:
    cfg = RawConfigParser()
    cfg.readfp(conf)

redis_auth = cfg.get('redis', 'password')
redis_host = cfg.get('redis', 'host')
r = redis.Redis(redis_host, password=redis_auth)

while True:
    msg = r.brpop('deployment_check')
    json_msg = json.loads(msg)
    poll_git(json_msg.get('organization'),
             json_msg.get('current_hash'),
             json_msg.get('branch'),
             json_msg.get('git_url'))

def get_host():
    # get worker host for grabbing configuration info
    # will grab a random entry in the pool of hosts in aws tagged with 
    # deployment_configuration
    return

# a different process will be responsible for updating the database
# for git status
def save_hash(current_hash, branch, git_url):
    r.lpush('deployment_git_project', json.dumps(dict(current_hash=current_hash,
                                                      branch=branch,
                                                      git_url=git_url)))


def poll_git(organization, current_hash, branch, git_url):
    p = subprocess.Popen(shlex.split('git ls-remote {0}'.format(git_url)), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    for x in out.splitlines():
        rsha1 = x.split()[0].strip()
        rbranch = x.split()[-1].split('/')[-1]
        if rbranch == branch and current_hash != rsha1:
            save_hash(rsha1, branch, git_url)
            get_configs(organization, git_url)


def get_configs(organization, git_url):
    host = get_host()
    script_path = os.path.join(os.path.abspath(__file__), 'scripts/')
    git_dir = os.path.join('/opt/', git_url.split('/')[-1])

    # for loop at bottom of function calls this function...
    # this will get the config files, we still need to get the playbooks
    def get_config(organization, config_path, service_name):
        base_name = os.path.basename(config_path)
        script_call = "{0}/redis_push_config.py \
                          --config={1} \
                          --service={2} \
                          --organization={3}\
                          --rhost={4} \
                          --rpass={5}".format(script_path, config_path, organization, service_name, redis_host, redis_auth)

        r = runner.Runner(transport='paramiko',
                          pattern=host,
                          module_name='script',
                          module_args=script_call)
        return r.run()

    # checkout git project
    r = runner.Runner(transport='paramiko',  
                      pattern=host, 
                      module_name='git', 
                      module_args='repo={0} dest={1}'.format(git_url, git_dir))
    r.run()

    # install python redis client so we can push configuration to redis
    # we'll pick up the configuration afterwards in order to configure the machine
    r = runner.Runner(transport='paramiko',  
                      pattern=host, 
                      module_name='command', 
                      module_args='easy_install redis')
    r.run()

    # find all app_settings file so we can iterate over them and parse.
    r = runner.Runner(transport='paramiko', 
                      pattern=host,
                      module_name='shell',  
                      module_args='find {0} -name app_settings.json'.format(git_dir))
    results = r.run()

    configs = results.get('contacted').get(host).get('stdout')
    for config in configs.splitlines():
        base_name = os.path.basename(config)
        service_name = os.path.dirname(config).split('/')[-1]
        get_config(organization, config, service_name)


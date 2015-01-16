from ansible import runner
import json
import redis
import os
# git fetch of repository
# will need to have some way of finding an available deployment node
def poll_git(redis_host, redis_pass, host, script_path, git_url, git_dir):
    # if updated, get_configs
    get_configs(redis_host, redis_pass, host, script_path, git_url, git_dir)

def get_configs(redis_host, redis_pass, host, script_path, git_url, git_dir):
    host = host
    script_path = script_path
   
    # for loop at bottom of function calls this function...
    def get_config(config_path, service_name):
        base_name = os.path.basename(config_path)

        script_call = "{0}/redis_push_config.py \
                          --config={1} \
                          --service={2} \
                          --rhost={3} \
                          --rpass={4}".format(script_path, config_path, service_name, redis_host, redis_pass)

        r = runner.Runner(transport='paramiko',
                          pattern=host,
                          host_list='{0}/inventory'.format(script_path),
                          module_name='script',
                          module_args=script_call)
        return r.run()

    r = runner.Runner(transport='paramiko', 
                      pattern=host, 
                      host_list='{0}/inventory'.format(script_path), 
                      module_name='git', 
                      module_args='repo={0} dest={1}'.format(git_url, git_dir))
    r.run()
    r = runner.Runner(transport='paramiko', 
                      pattern=host, 
                      host_list='{0}/inventory'.format(script_path), 
                      module_name='shell', 
                      module_args='find {0} -name app_settings.json'.format(git_dir))
    results = r.run()
    configs = results.get('contacted').get(host).get('stdout')
    services = {}
    for config in configs.splitlines():
        base_name = os.path.basename(config)
        service_name = os.path.dirname(config).split('/')[-1]
        get_config(config, service_name)


# walk path of respository looking for app_settings.json
pass

# check if organization exists, if not create it
def org_exists(org_name):
    # return true or false if org exists
    pass

def create_org(org_name, domain, admin_email):
    if not org_exists(org_name):
        # create organization
        pass

# Next, create service endpoint.
def elb_exists(service_name, org):
    # check to see if elb exists, return True or False if it exists
    pass

def create_elb(serivce_name, organization, domain, region):
    if not elb_exists(service_name, organization):
        # create elb
        pass
        created_elb = True
    else:
        created_elb = False

# Now if created elb, set name in DNS
def set_elb_dns(service_name, organization, domain, elb_id):
    # now setup dns for the elastic load balancer
    pass

# Now that you have an elastic load balancer setup, go ahead and create your instances
# but first see if you have that many instances already created...
def find_instances(organization, service, domain):
    # use boto to find instances
    # count instances
    # return instances
    pass

def check_instance_health(instance_id, elb):
    # get health of nodes on elb.
    # if instance id is not healthy, return False if it is return True
    pass

def create_instance(instance_type, ami_id, security_group, subnet_id, elb_id, region, organization, domain, service):
    # create instance, attach to elb
    # tag instance with organization, domain, service
    # save info in database
    pass

def setup_instances(organization, service, domain, instance_type, ami_id, instance_count, region, subnet_id, elb_id):
    # we will now setup our instances
    instances = find_instances(organization, service, domain)
    if not instances:
        for x in xrange(0, instance_count):
            create_instance(instance_type, ami_id, region, subnet_id, elb_id, region, organization, domain, service)
    else:
        for instance in [instance for instance in instances if not check_instance_health(instance)]:
            # strike instance
            create_instance(instance_type, ami_id, region, subnet_id, elb_id, region, organization, domain, service)
        for x in xrange(0, int(instance_count-len(instances))):
            create_instance(instance_type, ami_id, region, subnet_id, elb_id, region, organization, domain, service)
    
# Now that instance is provisioned, deploy code 
def git_fetch(service_name, organization, domain, git_url, code_path):
    # use ansible to fetch the git repository and place into code_path
    pass

# Now that code is deployed, configure according to configuration playbook
def configure_instances(service_name, organization, domain, config_url):
    pass

# Now that instance is configured, add to monitoring
def monitor_instance(service_name, organization, domain, checks_dir):
    pass

# Now that instance is being monitored, add to web front end
def add_backend(elb_dns, url):
    pass

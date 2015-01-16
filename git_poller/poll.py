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


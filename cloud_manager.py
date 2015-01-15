#!/usr/bin/python
import os
import boto
from boto.ec2 import elb as aws_lb
import time
import subprocess
import sys
import MySQLdb
import json
import shutil
import paramiko
import sys
from collections import defaultdict
from MySQLdb.cursors import DictCursor

def sync_db():
    query = "select name from ec2_instances group by name"
    cursor.execute(query)
    for instance_name in [instance.get('name') for instance in cursor.fetchall()]:
        aws_instances = [instance.get('instance_id') for instance in find_instances(instance_name)]
        query = "select instance_id from ec2_instances where name='{0}'".format(instance_name)
        cursor.execute(query)
        for instance_id in [instance.get('instance_id') for instance in cursor.fetchall()]:
            if instance_id not in aws_instances:
                query = "delete from ec2_instances where instance_id='{0}'".format(instance_id)
                cursor.execute(query)
                db.commit() 
   
def name_instance(instance_id):
    query = "select name from ec2_instances where instance_id='{0}'".format(instance_id)
    cursor.execute(query)
    return cursor.fetchone().get('name')

def get_template(template_name):
    query = "select * from aws_templates where name='{0}'".format(template_name)
    cursor.execute(query)
    return cursor.fetchone()

def register_instance(elb_name, instance_id):
    elb_conn = boto.connect_elb()
    elb = elb_conn.get_all_load_balancers([elb_name])[0]
    elb.register_instances(instance_id)

def deregister_instance(elb_name, instance_id):
    elb_conn = boto.connect_elb()
    elb = elb_conn.get_all_load_balancers([elb_name])[0]
    elb.deregister_instances(instance_id)

def sync_instance(instance_id):
    instance_name = name_instance(instance_id)
    instances = find_instances(instance_name)
    for instance in instances:
        if instance.get('instance_id') == instance_id:
            query = "update ec2_instances set public_ip='{0}' where instance_id='{1}'"
            query = query.format(instance.get('ip_address'), instance_id)
            cursor.execute(query)
            db.commit()

def find_instances(instance_name):
    instances = []
    boto_conn = boto.connect_ec2()
    for reservation in boto_conn.get_all_instances():
        for instance in reservation.instances:
            if str(instance.tags.get('Name')) == instance_name:
                instances.append(dict(name=instance.tags.get('Name'),
                                     ip_address=instance.ip_address, 
                                     instance_id=instance.id,
                                     status=instance.update()))
    return instances

def list_all():
    instance_dict = defaultdict(list)
    query = "select name from ec2_instances group by name"
    cursor.execute(query)
    for name in cursor.fetchall():
        for instance in find_instances(name.get('name')):
            instance_dict[name.get('name')].append(instance)
    return instance_dict

def list_instances(instance_name):
    instance_list = []
    for instance in find_instances(instance_name):
        instance_list.append(dict(name=instance.get('name'), 
                                  status=instance.get('status'), 
                                  instance_id=instance.get('instance_id'), 
                                  ip_address=instance.get('ip_address')))
    return instance_list

def create_instances(instance_name, template_name, **kwargs):
    boto_conn = boto.connect_ec2()
    if 'instance_count' not in kwargs.keys():
         kwargs['instance_count'] = 1
    template = get_template(template_name)
    for x in xrange(kwargs.get('instance_count')):
        res = boto_conn.run_instances(template.get('ami_id'),
                                      key_name=template.get('key_name'),
                                      placement=template.get('availability_zone'),
                                      instance_type=template.get('instance_type'),
                                      security_groups=[template.get('security_group')])
        instance = res.instances[0]
        while instance.update() != "running":
            time.sleep(5)

        # there are times when the instance will have a running state; but, will not be ready to add tags
        # this loop should spin until the tags have been created. Tags being the name of the instance. 
        while True:
            try:
                boto_conn.create_tags(instance.id, {'Name': instance_name})
                break
            except:
                continue

        query = "insert into ec2_instances (instance_id, name, \
        instance_type, public_ip, availability_zone, template) VALUES \
        ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}')"
        cursor.execute(query.format(instance.id, 
                                    instance_name, 
                                    instance.instance_type, 
                                    instance.ip_address, 
                                    template.get('availability_zone'),
                                    template_name))
        db.commit()
        if 'elb' in kwargs.keys():
            register_instance(kwargs.get('elb'), instance.id)
        yield instance

def terminate_instance(instance_id):
    boto_conn = boto.connect_ec2()
    query = "select instance_id from ec2_instances where instance_id='{0}'".format(instance_id)
    cursor.execute(query)
    instances = [instance.get('instance_id') for instance in cursor.fetchall()]
    if not instances:
        return False
    else:
        try:
            boto_conn = boto.connect_ec2()
            boto_conn.terminate_instances(instance_id)
            query = "delete from ec2_instances where instance_id='{0}'".format(instance_id)
            cursor.execute(query)
            db.commit()
        except:
            return False
        return True
        
def drop_instances(instance_name, **kwargs):
    boto_conn = boto.connect_ec2()
    if 'instance_count' not in kwargs.keys():
         kwargs['instance_count'] = 1
    drop_instances = []
    count = 0 
    for instance in find_instances(instance_name):
        if instance.get('ip_address') and count < kwargs.get('instance_count'):
            drop_instances.append(instance) 
            count += 1
    if not drop_instances:
        return
    boto_conn.terminate_instances([instance.get('instance_id') for instance in drop_instances])
    for drop_instance in drop_instances:
        query = "delete from ec2_instances where instance_id='{0}'".format(drop_instance.get('instance_id'))
        cursor.execute(query)
        db.commit()
        if 'elb' in kwargs.keys():
            for drop_instance in drop_instances:
                deregister_instance(kwargs.get('elb'), drop_instance.get('instance_id'))
    remove_ssh_host(instance.get('instance_id'))

def ssh_key(instance_id):
    global ec2_instance, aws_template, aws_keys, ssh_dir, ssh_key_path
    query = "select name, template, public_ip from ec2_instances where instance_id='{0}'".format(instance_id)
    cursor.execute(query)
    ec2_instance = cursor.fetchone()

    query = "select key_name, user from aws_templates where name='{0}'".format(ec2_instance.get('template'))
    cursor.execute(query)
    aws_template = cursor.fetchone()

    query = "select ssh_key from aws_keys where key_name='{0}'".format(aws_template.get('key_name'))
    cursor.execute(query)
    aws_keys = cursor.fetchone()

    ssh_dir = "{0}/.ssh".format(os.environ['HOME'])
    ssh_key_path = os.path.join(ssh_dir, "{0}.pem".format(aws_template.get('key_name')))
    with open(ssh_key_path, 'w') as ssh_key:
        ssh_key.write(aws_keys.get('ssh_key'))
    os.system('chmod 600 {0}/*'.format(ssh_dir))

def connect(instance_id):
    ssh_key(instance_id)
    ssh_cmd = "ssh {0} -i {1}.pem -l {2}".format(ec2_instance.get('public_ip'),
                                                 os.path.join(ssh_dir, aws_template.get('key_name')),
                                                 aws_template.get('user'))
    os.system(ssh_cmd)
    try:
        os.unlink(os.path.join(ssh_dir, "{0}.pem".format(aws_template.get('key_name'))))
    except: # clean up must have already happend... no biggie
        pass
  

def remove_ssh_host(instance_id):
    ssh_dir = "{0}/.ssh".format(os.environ['HOME'])
    ssh_config = os.path.join(ssh_dir, 'config')
    tmp_config = '{0}.tmp'.format(ssh_config)
    tmp_ssh_config = open(tmp_config, 'w')
    with open(ssh_config, 'r') as config:
        seen_host = False
        for line in config:
            if seen_host and instance_id in line:
                seen_host = False
            if instance_id in line:
                seen_host = True
            if not seen_host:
                tmp_ssh_config.write(line)
    tmp_ssh_config.close()
    shutil.move(tmp_config, ssh_config)
    

def add_ssh_host():
    ssh_config = os.path.join(ssh_dir, 'config')
    with open(ssh_config, 'a') as ssh_config:
        ssh_config.write("\n\n# {0}\n".format(instance_details.get('instance_id')))
        ssh_config.write('host {0}\n'.format(ec2_instance.get('public_ip')))
        ssh_config.write('\thostname {0}\n'.format(instance_details.get('public_ip')))
        ssh_config.write('\tIdentityFile {0}\n'.format(ssh_key_path))
        ssh_config.write("# {0}\n\n".format(instance_details.get('instance_id')))

def check_ssh_config(ip_address):
    ssh_config = paramiko.SSHConfig()
    with open(os.path.join(ssh_dir, 'config'), 'r') as ssh_conf:
        ssh_config.parse(ssh_conf)
    conf = ssh_config.lookup(ip_address)
    conf.pop('hostname')
    if conf:
        return True
    else:
        return False

def ansible_host(instance_id):
    global instance_details, template_details
    query = "select * from ec2_instances where instance_id='{0}'".format(instance_id)
    cursor.execute(query)
    instance_details = cursor.fetchone()
    query = "select * from aws_templates where name='{0}'".format(instance_details.get('template'))
    cursor.execute(query)
    template_details = cursor.fetchone()
    ssh_key(instance_id)
    if not check_ssh_config(instance_details.get('public_ip')):
        add_ssh_host()
    print json.dumps(dict(ansible_ssh_host=instance_details.get('public_ip'),
                          ansible_ssh_identity=ssh_key_path,
                          ansible_ssh_user=template_details.get('user')))
    

def ansible_list():
    query = "select instance_id, name from ec2_instances"
    cursor.execute(query)
    results = cursor.fetchall()
    ansible_host_list = defaultdict(list)
    for result in results:
        ansible_host_list[result.get('name')].append(result.get('instance_id'))
    print json.dumps(ansible_host_list)


def fresh(instance_id, threshold):
    query = "select count(*) as fresh from ec2_instances where instance_id='{0}' and \
             create_time < DATE_SUB( CURRENT_TIME(), INTERVAL {1} MINUTE)"    
    query = query.format(instance_id, threshold)
    cursor.execute(query)
    results = cursor.fetchone()
    if results.get('fresh'):
        return False
    else:
        return True
    
def purge_nodes(load_balancer):
    dead_nodes = []
    load_balancer_health = report_load_balancer(load_balancer)
    for node in load_balancer_health:
        if load_balancer_health.get(node) != 'InService' and not fresh(node, 10):
            dead_nodes.append(node)
    for node in dead_nodes:
        deregister_instance(load_balancer, node)
        terminate_instance(node)

def lb_status():
    query = "select name from aws_load_balancers"
    cursor.execute(query)
    cloud_dict = defaultdict(list)
    for lb in cursor.fetchall():
        lb_report = report_load_balancer(lb.get('name')) 
        for node in lb_report:
            cloud_dict[lb.get('name')].append(dict(node=node, status=lb_report.get(node)))
        if not cloud_dict.get(lb.get('name')):
            cloud_dict[lb.get('name')].append(dict(status='no attached nodes'))
    return cloud_dict               

def report_load_balancer(load_balancer):
    elb = aws_lb.ELBConnection()
    load_balancer_health = {}
    for instance in elb.describe_instance_health(load_balancer):
        load_balancer_health[instance.instance_id] = instance.state
    return load_balancer_health

def main():
    #try:
        global db, cursor, instance_id
        db = MySQLdb.connect(db='aws_devops', 
                             user='aws_cloud', 
                             passwd='aws_cloud', 
                             host='64.111.110.171',
                             cursorclass=DictCursor)
        cursor = db.cursor()
   
        sync_db()

        if opt.create:
            print 'creating {0} instances using {1} template'.format(opt.create, opt.template)
            params = {}
            if opt.elb: params['elb'] = opt.elb
            params['instance_count'] = opt.create
            for instance in create_instances(opt.name, opt.template, **params):
                print 'You can now connect by running {0} --conn={1}'.format(os.path.basename(sys.argv[0]), instance.id) 

        elif opt.destroy:
            params = {}
            if opt.elb: params['elb'] = opt.elb
            params['instance_count'] = opt.destroy 
            drop_instances(opt.name, **params)

        elif opt.list_instances:
            if opt.name:
                instances = []
                for instance in find_instances(opt.name):
                    instances.append(instance)
                print json.dumps(dict(instances=instances), sort_keys=True, indent=4, separators=(',', ': '))
            else:
                print json.dumps(dict(instances=list_all()), sort_keys=True, indent=4, separators=(',', ': '))

        elif opt.connect:
            connect(opt.connect)

        elif opt.ansible_list:
            ansible_list() 

        elif opt.sync:
            sync_instance(opt.sync)

        elif opt.purge:
            purge_nodes(opt.purge) 

        elif opt.ansible_host:
            ansible_host(opt.ansible_host)

        elif opt.elbstatus:
            print json.dumps(dict(load_balancers=lb_status()), sort_keys=True, indent=4, separators=(',', ': '))

        elif opt.terminate:
           if terminate_instance(opt.terminate):
               print "Terminated {0}".format(opt.terminate)
           else:
               print "Could not terminate instance"
        elif opt.name_instance:
            print name_instance(opt.name_instance)

        return 0
    #except Exception, e:
    #    sys.stderr.write('{0}\n'.format(str(e)))
    #    return 1


if __name__ == '__main__':
    from optparse import OptionParser, OptionGroup
    parser = OptionParser()

    ec2_options = OptionGroup(parser, 'EC2 Options')
    ec2_options.add_option('--ec2status', 
                      help='list status, instance id, and ip address for all nodes of type specified by --name',
                      dest='list_instances', 
                      action='store_true', 
                      default=False)
    ec2_options.add_option('--sync')
    ec2_options.add_option('--template')
    ec2_options.add_option('--name')
    ec2_options.add_option('--create', type='int')
    ec2_options.add_option('--destroy', type='int')
    ec2_options.add_option('--name-instance', dest='name_instance')
    ec2_options.add_option('--elb')
    ec2_options.add_option('--connect')
    ec2_options.add_option('--terminate')
    parser.add_option_group(ec2_options)

    elb_options = OptionGroup(parser, "ELB Options")
    elb_options.add_option('--elbstatus', action='store_true', default=False)
    elb_options.add_option('--purge')
    parser.add_option_group(elb_options)
    
    ansible_options = OptionGroup(parser, 'Ansible Options')
    ansible_options.add_option('--list', action='store_true', default=False, dest='ansible_list')
    ansible_options.add_option('--host', dest='ansible_host')
    parser.add_option_group(ansible_options)
    opt, args = parser.parse_args()
    sys.exit(main())

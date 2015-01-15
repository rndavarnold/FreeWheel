'''
Created on Jan 12, 2015

@author: darnold
'''
import os
from boto.exception import BotoClientError
import time
from boto import ec2
from boto import route53
from aws_objects.security_group import SecGroup
from db_objects import instance as db_instance
import boto.ec2

class EC2Instance:
    def __init__(self, name=None, region=None, organization=None, domain=None):
        self.name = name
        self.region = region
        self.organization = organization
        self.domain = domain
        self.ec2 = ec2.connect_to_region(region)

    def set_instance_dns(self, instance_id, host_name, domain_name, ip_address):
        r53 = route53.connect_to_region(self.region)
        dns_zone = None
        for zone in r53.get_zones():
            if domain_name == zone.name:
                dns_zone = zone
        if not dns_zone:
            raise Exception('DNS Hosting for {0} not setup in Route53'.format(domain_name))
        dns_name = "{0}.{1}.{2}".format(instance_id, host_name, domain_name)
        dns_zone.add_record('A', dns_name, ip_address) 
        return dns_name
        
    def remove_instances(self, count):
        instances = self.get_instances_by_name(self.name)
        removed_instances = []
        for x in xrange(count):
            try:
                removed_instances.append(instances[x].id)
            except:
                break
        self.ec2.terminate_instances(removed_instances)
        return removed_instances
    
    def create_instance(self, allow_ssh=True, set_dns=True, vpc_info=None, **template_details):
        sec_group = SecGroup(self.region)
        
        if not self.key_pair_exists(template_details.get('key_name')):
            self.create_key_pair(template_details.get('key_name'))

        if not sec_group.sec_group_exists(template_details.get('security_group')):
            sec_group.create_sec_group(template_details.get('security_group'))
            
        if allow_ssh:
            sec_group.allow_ssh(template_details.get('security_group'))
        
        if not vpc_info:
            res = self.ec2.run_instances(template_details.get('ami_id'), 
                                         key_name=template_details.get('key_name'), 
                                         instance_type=template_details.get('instance_type'),
                                         security_groups=[template_details.get('security_group')])
        else:
            res = self.ec2.run_instances(template_details.get('ami_id'), 
                                         key_name=template_details.get('key_name'),
                                         subnet_id=vpc_info.get('subnet_id'),
                                         instance_type=template_details.get('instance_type'),
                                         security_groups=[template_details.get('security_group')])
        instance = res.instances[0]
        while instance.update() != "running":
            time.sleep(5)
        # there are times when the instance will have a running state; but, will not be ready to add tags
        # this loop should spin until the tags have been created. Tags being the name of the instance.
        while True:
            try:
                self.ec2.create_tags(instance.id, {'name': self.name})
                self.ec2.create_tags(instance.id, {'template': template_details.get('name')})
                break
            except:
                continue
            
        if self.organization:
            self.ec2.create_tags(instance.id, {'organization': self.organization})

        if self.domain:
            self.ec2.create_tags(instance.id, {'domain': self.domain})    
        
        return instance
    
    def get_instances_by_service(self, domain):
        ec2 = boto.ec2.connect_to_region(self.region)
        return ec2.get_all_instances(filters={'tag:domain': domain})
    
    def get_instances_by_name(self, name):
        ec2 = boto.ec2.connect_to_region(self.region)
        return ec2.get_all_instances(filters={'tag:name': name})
    
    def save_instance_info(self, **instance_info):
        ec2_instance = db_instance.Instances()
        ec2_instance.load_from_dict(instance_info)
        ec2_instance.insert()
    
    def create_key_pair(self, key_name):
        key_pair = self.ec2.create_key_pair(key_name)
        try:
            key_pair.save(os.path.join(os.environ.get('HOME'), '.ssh/'))
        except BotoClientError:
            pass

    def key_pair_exists(self, key_name):
        for key_pair in self.ec2.get_all_key_pairs():
            if key_name == key_pair.name:
                return True
        return False
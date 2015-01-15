import boto
from boto.exception import EC2ResponseError, BotoClientError
from boto import ec2
import boto.route53 as route53
from boto.ec2.elb import HealthCheck
import json
import aws_dynamo_objects_meta

import boto.ec2.elb
import time
from boto.vpc import VPCConnection

class ServiceDeploy:

    def __init__(self, name, region, instance_count, port=80, healthcheck_url='healthcheck'):
        self.app_name = name.strip()
        self.app_port = port
        self.instance_count = instance_count
        self.region = region
        self.healthcheck_url = healthcheck_url
        self.domain = None
        self.organization = None
        
        
    def get_zones(self):
        zones = []
        for zone in ec2.connect_to_region(self.region).get_all_zones():
            zones.append(zone.name)
        return zones

    def set_configuration(self, configuration):
        '''
        pass in json object which represents Ansible Playbook
        redis hset {0}_configuration.format(self.app_name), json.dumps(configuration)
        '''

    def create_instances(self):
        ec2_instances = EC2Instance(name=self.app_name, 
                                    region=self.region, 
                                    organization=self.organization, 
                                    domain=self.domain)
       
        instance_ids = [] 
        for x in xrange(self.instance_count):
            create_instance = ec2_instances.create_instance_from_template
            instance_ids.append(create_instance(self.app_name, 
                                                allow_ssh=True, 
                                                set_dns=False))
            
        self.app_load_balancer.register_instances(instance_ids)
            
            
    def create_load_balancer(self):
        lb = EC2LoadBalancer(self.app_name, self.region)
        zones = self._get_zones()
        target = 'HTTP:{0}/{1}'.format(self.app_port, self.healthcheck_url)
        lb.create_healthcheck(10, 10, 10, target)
        self.app_load_balancer =  lb.create_load_balancer(zones,
                                                          (self.app_port, 
                                                           self.app_port, 
                                                           'http')) 
        
    def set_service_dns(self, domain_name):
        r53 = route53.connect_to_region(self.region)
        dns_zone = None
        for zone in r53.get_zones():
            if domain_name == zone.name:
                dns_zone = zone
        if not dns_zone:
            raise Exception('DNS Hosting for {0} not setup in Route53'.format(domain_name))
        status = dns_zone.add_record('CNAME', 
                                     '{0}.{1}'.format(self.app_name.strip(), domain_name),
                                     self.app_load_balancer.dns_name) 
        return status

    def deploy_app(self):
        pass











        
                                                   


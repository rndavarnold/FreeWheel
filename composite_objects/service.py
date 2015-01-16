'''
Created on Jan 12, 2015

@author: darnold
'''
import os, sys
top_level = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
sys.path.append(top_level)
import urlparse

from aws_objects import load_balancer, instances
from db_objects import organizations, service , organization_vpc
from db_objects import organization_services, template
from db_objects import instance

class Service:
    
    def __init__(self, service_name, **kwargs):
        self.service_name = service_name
        for k, v in kwargs.items():
            setattr(self, k, v)
        
    def create(self):
        svc = service.Services()
        svc.set_elb_name(self.service_name)
        svc.set_dns_name('{0}.{1}.{2}'.format(self.service_name, 
                                              self.organization, 
                                              self.domain))
        svc.set_configuration_url(self.configuration_url)
        svc.set_name(self.service_name)
        svc.save()
        svc.load(name=self.service_name)
        org = organizations.Organizations()
        org.load(name=self.organization)
        org_id = org.get('id')
        svc_id = svc.get('id')
        org_svc = organization_services.OrganizationServices()
        org_svc.load_from_dict(dict(organization_id=org_id,
                                    service_id=svc_id))
        org_svc.save()
        
    def get_service_info(self):
        svc = service.Services()
        svc.load(name=self.service_name)
        return svc.dump()
        
    def create_service_endpoint(self, healthcheck_url, ports):
        lb_name = '{0}-{1}'.format('-'.join(self.service_name.split('.')),
                                   '-'.join(self.organization.split('.')))
        lb = load_balancer.EC2LoadBalancer(lb_name, self.region)
        lb.create_healthcheck(10, 3, 3, healthcheck_url)
        lb.create_load_balancer(ports)
        lb.set_elb_dns(self.domain)
        
    def create_service_node(self, template):
        vpc = organization_vpc.OrganizationVPC()
        org = organizations.Organizations()
        org.load(name=self.organization)
        vpc.load(organization_id=org.get('id'))
        vpc = vpc.dump()
        node = instances.EC2Instance(self.service_name,
                                     self.region,
                                     self.organization,
                                     self.domain)
        tpl = template.Templates()
        tpl.load(name=template)
        if not vpc:
            instance = node.create_instance(template, allow_ssh=False, set_dns=False, vpc_info=None, **tpl.dump())
        else:
            instance = node.create_instance(template, allow_ssh=False, set_dns=False, vpc_info=vpc, **tpl.dump())
        lb_name = '{0}.{1}'.format(self.service_name,
                                   self.organization)
        lb = load_balancer.EC2LoadBalancer(lb_name, self.region)
        ins = instance.Instances()
        ins.set('name', self.service_name)
        ins.set('instance_id', instance.id)
        ins.set('user', template.get('user'))
        ins.set('key_name', template.get('key_name'))
        ins.set('private_ip', instance.private_ip)
        ins.set('template_id', template.get('id'))
        ins.insert()
        lb.register_node(instance.id)
        return node
        
        
        
        
        
        

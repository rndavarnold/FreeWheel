'''
Created on Jan 12, 2015

@author: darnold
'''
import os, sys
from boto.vpc import VPCConnection
top_level = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
sys.path.append(top_level)
from db_objects import organizations, organization_vpc
from composite_objects import service as comp_service

class Organization:
    
    def __init__(self, organization_name, domain):
        self.organization = organization_name
        self.domain = domain

    def create(self, **organization_details):
        self.organization = organization_details.get('name')
        self.domain = organization_details.get('domain')
        org = organizations.Organizations()
        org.load_from_dict(organization_details)
        org.insert()
        return Organization(self.organization, self.domain)

    def get(self):
        org = organizations.Organizations()
        org.load(name=self.organization)
        return org.dump() 

    def delete(self, organization_name):
        org = organizations.Organizations()
        org.load(name=self.organization_name)
        org.delete()
    
    def create_vpc(self, vpc_cidr, subnet_cidr):
        c = VPCConnection()
        vpc = c.create_vpc(vpc_cidr)
        vpc.add_tag('organization', value=self.organization)
        subnet = c.create_subnet(vpc.id, subnet_cidr)
        while True:
            try:
                subnet.add_tag('organization', value=self.organization)
                break
            except:
                pass
        
        db_vpc = organization_vpc.OrganizationVPC()
        org = organizations.Organizations()
        org.load(name=self.organization)
        print org
        db_vpc.set('organization_id', org.get('id'))
        db_vpc.set('vpc_id', vpc.id)
        db_vpc.set('subnet_id', subnet.id)
        db_vpc.insert()
        return vpc.id, subnet.id, org.get('id')
    
    def remove_vpc(self):
        c = VPCConnection()
        for subnet in c.get_all_subnets():
            if subnet.tags.get('organization') == self.organization:
                c.delete_subnet(subnet.id)
        for vpc in c.get_all_vpcs():
            if vpc.tags.get('organization') == self.organization:
                vpc.delete()
        db_vpc = organization_vpc.OrganizationVPC()
        org = organizations.Organizations()
        org.load(name=self.organization_name)
        db_vpc.load(organization_id=org.get('id'))
        db_vpc.delete()

    def get_vpc_info(self):
        org = organizations.Organizations()
        org.load(name=self.organization_name)
        org = org.dump()
        org_id = org.get('id')
        vpc = organization_vpc.OrganizationVPC()
        vpc.load(organization_id=org_id)
        vpc = vpc.dump()
        return dict(vpc=org.get('vpc_id'),
                    subnet=org.get('subnet_id'))
        
    def launch_service(self, service_name, region):
        service = comp_service.Service(self.organization, self.domain, service_name, region)
        return service

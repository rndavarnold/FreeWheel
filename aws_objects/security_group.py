'''
Created on Jan 12, 2015

@author: darnold
'''
from boto import ec2
from boto.exception import EC2ResponseError

class SecGroup:

    def __init__(self, region):
        self.region = region
        self.ec2 = ec2.connect_to_region(region)       
        
    def sec_group_exists(self, sec_group_name):
        for sec_group in self.ec2.get_all_security_groups():
            if sec_group_name == sec_group.name:
                return True
        return False

    def allow_ssh(self, sec_group_name):
        try:
            sec_group = self.get_sec_group(sec_group_name)
            sec_group.authorize('tcp', 22, 22, '0.0.0.0/0')
        except EC2ResponseError:
            pass
        
    def allow_http(self, sec_group_name):
        try:
            sec_group = self.get_sec_group(sec_group_name)
            sec_group.authorize('tcp', 80, 80, '0.0.0.0/0')
        except EC2ResponseError:
            pass
    
    def allow_https(self, sec_group_name):
        try:
            sec_group = self.get_sec_group(sec_group_name)
            sec_group.authorize('tcp', 443, 443, '0.0.0.0/0')
        except EC2ResponseError:
            pass
        
    def create_sec_group(self, sec_group_name, inbound=None, src_group=None):
        s_group = self.ec2.create_security_group(sec_group_name, sec_group_name)
        if src_group:
            s_group.authorize(src_group=src_group)
        elif inbound:
            s_group.authorize('tcp', inbound, inbound, '0.0.0.0/0')
           

    def get_sec_group(self, sec_group_name):
        for sec_group in self.ec2.get_all_security_groups():
            if sec_group_name == sec_group.name:
                return sec_group
        return False

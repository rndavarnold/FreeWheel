'''
Created on Jan 12, 2015

@author: darnold
'''
from boto.ec2.elb import HealthCheck
from boto.ec2 import elb
import boto
import boto.ec2
from boto import ec2
import boto.ec2.elb
from security_group import SecGroup
from boto import route53
from boto import ec2

class EC2LoadBalancer:

    def __init__(self, app_name, region):
        self.lb_name = app_name
        self.hc = False
        self.region = region
        self.lb_sec_group = SecGroup(region)
        self.lb_sec_group_name = '{0}_elb'.format(app_name)

    def register_node(self, instance_id):
        elb = elb.connect_to_region(self.region)
        lb = elb.get_all_load_balancers(load_balancer_names=self.app_name)
        lb.register_instances([instance_id])
            
    def create_healthcheck(self, interval, healthy_threshold, unhealthy_threshold, target):
        print target
        self.hc = HealthCheck(interval=interval,
                              healthy_threshold=healthy_threshold,
                              unhealthy_threshold=unhealthy_threshold,
                              target=target)

    def create_load_balancer(self, ports):
        conn = boto.ec2.elb.connect_to_region(self.region)
        if not self.hc:
            raise Exception('must configure healthcheck before creating load balancer')
        if not self.lb_sec_group.sec_group_exists(self.lb_sec_group_name):
            self.lb_sec_group.create_sec_group(self.lb_sec_group_name, inbound=ports[0])
        lb_sec_group = self.lb_sec_group.get_sec_group(self.lb_sec_group_name)
        zones = self._get_zones()
        self.lb = conn.create_load_balancer(self.lb_name, 
                                       zones, 
                                       [ports], 
                                       security_groups=[lb_sec_group.id])
        self.lb.configure_health_check(self.hc)
        for zone in self._get_zones():
            self.lb.enable_zones(zone)        

        self.lb.enable_cross_zone_load_balancing()
        return self.lb
    
    def set_elb_dns(self, domain_name):
        elbo = elb.connect_to_region(self.region)
        lb = elbo.get_all_load_balancers(load_balancer_names=self.lb_name).pop()
        r53 = route53.connect_to_region(self.region)
        dns_zone = None
        for zone in r53.get_zones():
            if domain_name == zone.name:
                dns_zone = zone
        if not dns_zone:
            raise Exception('DNS Hosting for {0} not setup in Route53'.format(domain_name))
        status = dns_zone.add_record('CNAME', 
                                     '{0}.{1}'.format(self.lb_name.strip(), domain_name),
                                     lb.dns_name) 
        return status
    
    def _get_zones(self):
        zones = []
        for zone in boto.ec2.connect_to_region(self.region).get_all_zones():
            zones.append(zone.name)
        return zones

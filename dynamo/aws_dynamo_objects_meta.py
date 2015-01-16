import boto
from dynamodb_mapper.model import DynamoDBModel
from dynamodb_mapper.model import ConnectionBorg


def __init__(self, **kwargs):
    conn = boto.connect_dynamodb()
    super(self.__class__, self).__init__(**kwargs)
    if self.__table__ not in conn.list_tables():
        conn = ConnectionBorg()
        conn.create_table(self, 10, 10, wait_for_active=True)

def __setattr__(self, name, value):
    if type(value) == type(str()):
        value = unicode(value)
    self.__dict__[name] = value

def get_json(self, hash_key):
    try:
        tmpl = super(self.__class__, self).get(hash_key)
        return tmpl.to_json_dict()
    except:
        return None


class _OrganizationMap(DynamoDBModel):
    __table__ = u"organization_vpcs"
    __hash_key__ = u"organization"
    __schema__ = {
        u"organization": unicode,
        u"has_vpc": bool,
        u"vpc_id": unicode,
        u'subnet_id': unicode
    }

Organization = type('Organization', 
                   (_OrganizationMap,), 
                   {'__init__': __init__,
                    '__setattr__': __setattr__,
                    'get_json': get_json})




class _EC2TemplateMap(DynamoDBModel):
    __table__ = u"ec2_templates"
    __hash_key__ = u"name"
    __schema__ = {
        u'name': unicode,
        u"ami_id": unicode,
        u"key_name": unicode,
        u'instance_type': unicode,
        u'security_group': unicode,
        u'organization': unicode,
        u'user': unicode,
    }

EC2Template = type('EC2Template', 
                   (_EC2TemplateMap,), 
                   {'__init__': __init__,
                    '__setattr__': __setattr__,
                    'get_json': get_json})
                               




class _EC2LoadBalancerHealthcheckMap(DynamoDBModel):
    __table__ = u"load_balancer_healthchecks"
    __hash_key__ = u"name"
    __schema__ = {
        u'name': unicode,
        u'interval': int,
        u'healthy_threshold': int,
        u'unhealthy_threshold': int,
        u'target': unicode
    }

EC2LoadBalancerHealthCheck = type('EC2LoadBalancerHealthCheck', 
                                  (_EC2LoadBalancerHealthcheckMap,), 
                                  {'__init__': __init__,
                                   '__setattr__': __setattr__,
                                   'get_json': get_json})





class _EC2LoadBalancerMap(DynamoDBModel):
    __table__ = u"aws_load_balancers"
    __hash_key__ = u"name"
    __schema__ = {
        u'name': unicode,
        u'url': unicode,
        u'zones': list,
        u'ports': list,
    }

EC2LoadBalancer = type('EC2LoadBalancer', 
                       (_EC2LoadBalancerMap,), 
                       {'__init__': __init__,
                        '__setattr__': __setattr__,
                        'get_json': get_json})





class _EC2InstanceMap(DynamoDBModel):
    __table__ = u"ec2_instances"
    __hash_key__ = u"instance_id"
    __schema__ = {
        u'name': unicode,
        u'template': unicode,
        u'instance_id': unicode,
        u'public_ip': unicode,
        u'organization': unicode,
        u'domain': unicode,
        u'dns_name': unicode
    }

EC2Instance = type('EC2Instance',
                   (_EC2InstanceMap,),
                   {'__init__': __init__,
                    '__setattr__': __setattr__,
                    'get_json': get_json})




class _EC2SecurityGroupMap(DynamoDBModel):
    __table__ = u"aws_security_groups"
    __hash_key__ = u"name"
    __schema__ = {
        u'name': unicode,
        u'description': unicode,
        u'rules': list,
    }

EC2SecurityGroup = type('EC2SecurityGroup',
                        (_EC2SecurityGroupMap,),
                        {'__init__': __init__,
                         '__setattr__': __setattr__,
                         'get_json': get_json})
                        

import boto
from dynamodb_mapper.model import DynamoDBModel
from dynamodb_mapper.model import ConnectionBorg


class _EC2TemplateMap(DynamoDBModel):
    __table__ = u"ec2_templates"
    __hash_key__ = u"name"
    __schema__ = {
        u'name': unicode,
        u"ami_id": unicode,
        u"key_name": unicode,
        u'availability_zone': unicode,
        u'instance_type': unicode,
        u'security_group': unicode,
        u'user': unicode,
    }

class EC2Template(_EC2TemplateMap):

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
        tmpl = super(self.__class__, self).get(hash_key)
        return tmpl.to_json_dict()






class _EC2LoadBalancerHealthcheck(DynamoDBModel):
    __table__ = u"load_balancer_healthchecks"
    __hash_key__ = u"load_balancer"
    __schema__ = {
        u'interval': int,
        u'healthy_threshold': int,
        u'unhealthy_threshold': int,
        u'target': unicode
    }

class EC2LoadBalancerHealthCheck(_EC2TemplateMap):

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
        tmpl = super(self.__class__, self).get(hash_key)
        return tmpl.to_json_dict()




class _EC2LoadBalancerMap(DynamoDBModel):
    __table__ = u"aws_load_balancers"
    __hash_key__ = u"name"
    __schema__ = {
        u'name': unicode,
        u'url': unicode,
        u'zones': list,
        u'ports': list,
    }

class EC2LoadBalancer(_EC2LoadBalancerMap):

    def __init__(self, **kwargs):
        conn = boto.connect_dynamodb()
        super(EC2LoadBalancer, self).__init__(**kwargs)
        if self.__table__ not in conn.list_tables():
            conn = ConnectionBorg()
            conn.create_table(self, 10, 10, wait_for_active=True)

    def __setattr__(self, name, value):
        if type(value) == type(str()):
            value = unicode(value)
        self.__dict__[name] = value

    def get_json(self, hash_key):
        tmpl = super(EC2LoadBalancer, self).get(hash_key)
        return tmpl.to_json_dict()




class _EC2InstanceMap(DynamoDBModel):
    __table__ = u"ec2_instances"
    __hash_key__ = u"name"
    __schema__ = {
        u'name': unicode,
        u'template': unicode,
        u'instance_id': unicode,
        u'public_ip': unicode,
    }

class EC2Instance(_EC2InstanceMap):

    def __init__(self, **kwargs):
        conn = boto.connect_dynamodb()
        super(EC2Instance, self).__init__(**kwargs)
        if self.__table__ not in conn.list_tables():
            conn = ConnectionBorg()
            conn.create_table(self, 10, 10, wait_for_active=True)

    def __setattr__(self, name, value):
        if type(value) == type(str()):
            value = unicode(value)
        self.__dict__[name] = value

    def get_json(self, hash_key):
        tmpl = super(EC2Instance, self).get(hash_key)
        return tmpl.to_json_dict()




class _EC2SecurityGroupMap(DynamoDBModel):
    __table__ = u"aws_security_groups"
    __hash_key__ = u"name"
    __schema__ = {
        u'name': unicode,
        u'description': unicode,
        u'rules': list,
    }

class EC2SecurityGroup(_EC2SecurityGroupMap):

    def __init__(self, **kwargs):
        conn = boto.connect_dynamodb()
        super(EC2SecurityGroup, self).__init__(**kwargs)
        if self.__table__ not in conn.list_tables():
            conn = ConnectionBorg()
            conn.create_table(self, 10, 10, wait_for_active=True)

    def __setattr__(self, name, value):
        if type(value) == type(str()):
            value = unicode(value)
        self.__dict__[name] = value

    def get_json(self, hash_key):
        tmpl = super(EC2Instance, self).get(hash_key)
        return tmpl.to_json_dict()


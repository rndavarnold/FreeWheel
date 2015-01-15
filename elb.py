from boto.ec2 import elb as aws_lb

class Elb():
    def __init__(self, secret_key, 
    def register_instance(elb_name, instance_id):
        elb_conn = boto.connect_elb()
        elb = elb_conn.get_all_load_balancers([elb_name])[0]
        elb.register_instances(instance_id)

    def deregister_instance(elb_name, instance_id):
        elb_conn = boto.connect_elb()
        elb = elb_conn.get_all_load_balancers([elb_name])[0]
        elb.deregister_instances(instance_id)

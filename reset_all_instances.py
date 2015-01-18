import boto
ec2 = boto.connect_ec2()
for region in ec2.get_all_regions():
    print region
    try:
        c = boto.ec2.connect_to_region(region.name)
        for instance in [res for res in c.get_all_instances()]:
            c.terminate_instances([x.id for x in instance.instances])
    except Exception, e:
        print str(e)


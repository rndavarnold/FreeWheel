# paas
Basic PaaS/Service Deployment project for AWS.

This project will allow devops to easily deploy services to AWS. 
This project shall watch a gitub repository for changes in infrastructure code and deploy according 
to configuration files in top level directories.

Given a configuration file like:

{
  "domain": "dev.custom-integrations.com.",
  "organization": "dev",
  "front_end": True,
  "organization": "custom-integrations",
  "admin_email": "dave.arnold@custom-integrations.com",
  "git_url": "https://github.com/djaboxx/TestProject",
  "code_path": "/opt/",
  "configuration_url": "https://github.com/djaboxx/TestProject/config.yml",
  "dependencies": {
    "mysql": {"id": "test-app",
              "size": 10,
              "instance_type": "db.m1.small",
              "user": "root",
              "connection_settings_file": "/etc/database.conf",
              "password": "hunter2"}
  },
  "instances": 3,
  "instance_type": "m3.large",
  "ami_id": "ami-9eaa1cf6",
  "region": "us-east-1"
}

and a project structure like:
.
├── README.md
├── shopping-cart
│   ├── app_settings.json
│   └── config
│       └── playbook.yml
├── user-signup
│   ├── app_settings.json
│   ├── checks
│   │   ├── gunicorn_check.py
│   │   ├── ping_check.py
│   │   └── redis_check.py
│   └── config
│       └── playbook.yml
└── web-front
    ├── app_settings.json
    └── config
        └── playbook.yml
        
A service will be deployed such that there will be 3 instances of type m3.large provisioned 
in the us-east-1 region. These 3 instances will be behind an Elastic Load Balancer that will 
have a DNS name of <service_name>.<organization>.<domain> where service name is that of the 
top-level directory.

These instances will have code from given git_url placed into code_path.
These instances will be configured according to Ansible playbooks found in the config directory.
The instances will be enrolled in sensu monitoring and will have the checks in the checks directory 
installed.

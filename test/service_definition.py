{
  "service_port": 80,
  "service_healthcheck": "/healthcheck",
  "git_url": "https://github.com/djaboxx/TestProject",
  "configuration_url": "https://github.com/djaboxx/TestProject",
  "dependencies": {
    "mysql": {"id": "test-app", 
              "size": 10, 
              "instance_type": "db.m1.small", 
              "user": "root", 
              "connection_settings_file": "/etc/database.conf",
              "password": "hunter2"}
  },
  "instances": 3,
  "user": "ubuntu",
  "instance_type": "m3.large",
  "ami_id": "ami-9eaa1cf6",
  "region": "us-east-1"
}

{
    "service_name": "user-signup",
    "service_port": 80,
    "instance_type": "m3.large",
    "instances": 3,
    "user": "ubuntu",
    "ami_id": "ami-9eaa1cf6",
    "region": "us-east-1",
    "git_url": "https://github.com/djaboxx/TestProject",
    "configuration_url": "https://github.com/djaboxx/TestProject",
    "load_balancer": {
        "healthcheck_interval": 10,
        "healthy_threshold": 3,
        "unhealthy_threshold": 5,
        "target": "HTTP:80/healthcheck"
    },
    "dependencies": {
        "mysql": {
            "size": 10,
            "instance_type": "db.m1.small",
            "user": "root",
            "connection_settings_file": "/etc/database.conf",
            "password": "hunter2"
        }
    }
}

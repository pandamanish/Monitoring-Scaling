import boto3
import time

# Initializing boto3 resource and client
ec2 = boto3.resource('ec2')
ec2_client = boto3.client('ec2')

# Required Parameters for the EC2 instance
key_name = 'manish'  # Existing key pair name
instance_type = 't4g.micro'# the instance_type
ami_id = 'ami-0c65913e98a358f43'  # Amazon Linux 2 AMI
existing_security_group_id = 'sg-09f2f07262c80b0e8'  # security group ID

# S3 bucket and object details
s3_bucket_name = 'manish-new-boto'  # provided S3 bucket name
s3_object_key = 'index.html'  # The name of the file in S3

# User data script to install Nginx, AWS CLI, and copy the HTML file from S3
config = f'''#!/bin/bash
# Update the instance and install necessary packages
sudo apt-get update -y
sudo apt-get install -y nginx curl unzip

# Download AWS CLI v2 and install it
curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS CLI
aws configure set aws_access_key_id "AKI*******"
aws configure set aws_secret_access_key "3YhObMPi3g3******************"
aws configure set default.region "us-west-2"

# Create the directory for the web server
sudo mkdir -p /var/www/html

# Copy the index.html file from S3 to the /var/www/html directory
sudo aws s3 cp s3://{s3_bucket_name}/{s3_object_key} /var/www/html/

# Set proper permissions for the web files
sudo chmod -R 775 /var/www/html

# Restart Nginx to serve the file
sudo systemctl restart nginx
'''

# Launching of EC2 instance using the existing security group and key pair ,instance type and ami_id
def launch_ec2_instance(ami_id, instance_type, key_name, security_group_id, config):
    instance = ec2.create_instances(
        ImageId=ami_id,
        InstanceType=instance_type,
        KeyName=key_name,  
        SecurityGroupIds=[security_group_id],  
        MinCount=1,
        MaxCount=1,
        UserData=config
    )
    instance_id = instance[0].id
    print(f'EC2 instance {instance_id} launched.')
    
    # Waiting for instance to enter the running state
    instance[0].wait_until_running()
    instance[0].reload()  # will reload the instance attributes

    print(f'EC2 instance {instance_id} is now running.')
    return instance[0]

# Executing the flow here
instance = launch_ec2_instance(ami_id, instance_type, key_name, existing_security_group_id, config)

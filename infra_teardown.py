import boto3
import zipfile
import os

# Initialized boto3 clients and resources
ec2 = boto3.resource('ec2')
ec2_client = boto3.client('ec2')
asg_client = boto3.client('autoscaling')
elb_client = boto3.client('elbv2')
sns_client = boto3.client('sns')
lambda_client = boto3.client('lambda')

# Configuration
key_name = 'manish'
instance_type = 't4g.micro'
ami_id = 'ami-0c65913e98a358f43'
existing_security_group_id = 'sg-09f2f07262c80b0e8'
s3_bucket_name = 'manish-new-boto'
s3_object_key = 'index.html'
tag_key = 'CreatedByScript'
tag_value = 'True'
subnets = ['subnet-09bd0e0acc92d4efa', 'subnet-0f30c30418def6379'] 
vpc_id = 'vpc-0321f38a7b594180d' 

# Deploy infrastructure
def deploy_infrastructure():
    # Creating SNS Topics
    topic_arns = create_sns_topics()

    # Creatung Load Balancer
    lb_arn, lb_dns = create_load_balancer()

    # Creating Target Group
    target_group_arn = create_target_group(vpc_id)

    # Launching EC2 instances
    instances = launch_ec2_instances()

    # Registered instances with Target Group
    register_instances_to_target_group(instances, target_group_arn)

    # Created Auto Scaling Group
    create_asg(target_group_arn)

    print(f"Infrastructure deployed. Load Balancer DNS: {lb_dns}")

# Creating SNS topics
def create_sns_topics():
    topics = {
        "HealthIssues": "HealthIssues",
        "ScalingEvents": "ScalingEvents",
        "HighTraffic": "HighTraffic"
    }
    topic_arns = {}
    for name, display_name in topics.items():
        response = sns_client.create_topic(Name=display_name)
        topic_arns[name] = response['TopicArn']
        print(f"SNS Topic created: {name} - ARN: {response['TopicArn']}")
    return topic_arns

# Creating Load Balancer
def create_load_balancer():
    response = elb_client.create_load_balancer(
        Name='manish-lb',
        Subnets=subnets,
        SecurityGroups=[existing_security_group_id],
        Scheme='internet-facing',
        Tags=[{'Key': 'Name', 'Value': 'manish-lb'}],
        Type='application',
        IpAddressType='ipv4'
    )
    lb_arn = response['LoadBalancers'][0]['LoadBalancerArn']
    lb_dns = response['LoadBalancers'][0]['DNSName']
    print(f"Load Balancer created with ARN: {lb_arn} and DNS: {lb_dns}")
    return lb_arn, lb_dns

# Creating Target Group
def create_target_group(vpc_id):
    response = elb_client.create_target_group(
        Name='manish-tg',
        Protocol='HTTP',
        Port=80,
        VpcId=vpc_id,
        HealthCheckProtocol='HTTP',
        HealthCheckPort='80',
        HealthCheckPath='/',
        TargetType='instance'
    )
    target_group_arn = response['TargetGroups'][0]['TargetGroupArn']
    print(f"Target Group created with ARN: {target_group_arn}")
    return target_group_arn

# Launching EC2 instances
def launch_ec2_instances():
    user_data_script =f'''#!/bin/bash
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

   
    
    instances = ec2.create_instances(
        ImageId=ami_id,
        InstanceType=instance_type,
        KeyName=key_name,
        SecurityGroupIds=[existing_security_group_id],
        MinCount=2,
        MaxCount=2,
        UserData=user_data_script,
        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': [{'Key': tag_key, 'Value': tag_value}]
        }]
    )
    for instance in instances:
        instance.wait_until_running()
        instance.reload()
    print(f'EC2 instances launched: {[instance.id for instance in instances]}')
    return instances

# Registered instances with Target Group
def register_instances_to_target_group(instances, target_group_arn):
    target_group_instances = [{'Id': instance.id} for instance in instances]
    elb_client.register_targets(
        TargetGroupArn=target_group_arn,
        Targets=target_group_instances
    )
    print(f'Instances registered to Target Group: {target_group_arn}')

# Created Auto Scaling Group
def create_asg(target_group_arn):
    launch_configuration_name = 'manish-launch-config'
    asg_name = 'manish-asg'

    asg_client.create_launch_configuration(
        LaunchConfigurationName=launch_configuration_name,
        ImageId=ami_id,
        InstanceType=instance_type,
        KeyName=key_name,
        SecurityGroups=[existing_security_group_id]
    )
    print(f'Launch configuration created: {launch_configuration_name}')

    asg_client.create_auto_scaling_group(
        AutoScalingGroupName=asg_name,
        LaunchConfigurationName=launch_configuration_name,
        MinSize=2,
        MaxSize=2,
        DesiredCapacity=2,
        VPCZoneIdentifier=','.join(subnets),
        TargetGroupARNs=[target_group_arn]
    )
    print(f'Auto Scaling Group created: {asg_name}')

# Update infrastructure
def update_infrastructure():
    
    print("Update functionality to be implemented.")

# Tear down infrastructure
def teardown_infrastructure():
    asg_name = 'manish-asg'
    lb_name = 'manish-lb'
    topic_names = ["HealthIssues", "ScalingEvents", "HighTraffic"]

    # Delete Auto Scaling Group
    asg_client.delete_auto_scaling_group(
        AutoScalingGroupName=asg_name,
        ForceDelete=True
    )
    print(f"Auto Scaling Group {asg_name} deleted.")

    # Deleting Load Balancer
    lb_response = elb_client.describe_load_balancers(Names=[lb_name])
    lb_arn = lb_response['LoadBalancers'][0]['LoadBalancerArn']
    elb_client.delete_load_balancer(LoadBalancerArn=lb_arn)
    print(f"Load Balancer {lb_name} deleted.")

    # Deleting Target Group
    tg_response = elb_client.describe_target_groups(Names=['manish-tg'])
    target_group_arn = tg_response['TargetGroups'][0]['TargetGroupArn']
    elb_client.delete_target_group(TargetGroupArn=target_group_arn)
    print(f"Target Group deleted.")

    # Deleting SNS Topics
    for topic_name in topic_names:
        sns_client.delete_topic(TopicArn=f"arn:aws:sns:us-west-2:975050024946:{topic_name}")  # provided account ID
        print(f"SNS Topic {topic_name} deleted.")

    # Terminating EC2 instances
    instances = ec2.instances.filter(Filters=[{'Name': 'tag:CreatedByScript', 'Values': ['True']}])
    for instance in instances:
        instance.terminate()
        print(f"Terminated EC2 instance: {instance.id}")

# Main execution
if __name__ == "__main__":
    action = input("Enter 'deploy', 'update', or 'teardown': ").strip().lower()
    
    if action == 'deploy':
        deploy_infrastructure()
    elif action == 'update':
        update_infrastructure()
    elif action == 'teardown':
        teardown_infrastructure()
    else:
        print("Invalid action specified.")

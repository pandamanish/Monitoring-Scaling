import boto3
import time

# Initialized the boto3 clients
elb_client = boto3.client('elbv2')  # For Load Balancer operations
ec2_client = boto3.client('ec2')    # For EC2 operations

# parameters for the ALB
load_balancer_name = 'manish-loadbalancer'
target_group_name = 'manishtgtg'
vpc_id = 'vpc-0321f38a7b594180d'  # VPC ID
security_group_id = 'sg-09f2f07262c80b0e8'  # Security Group ID
subnets = ['subnet-09bd0e0acc92d4efa', 'subnet-0f30c30418def6379']  # subnet IDs

# Manually specified the instance IDs which I wanted to register
instance_ids = ['i-028887cd4ee1c9a2c', 'i-07dab6cc77c1064b2']  # instance IDs

# Step 1: Creating an Application Load Balancer
def create_load_balancer():
    response = elb_client.create_load_balancer(
        Name=load_balancer_name,
        Subnets=subnets,
        SecurityGroups=[security_group_id],
        Scheme='internet-facing',
        Type='application',
        IpAddressType='ipv4'
    )
    lb_arn = response['LoadBalancers'][0]['LoadBalancerArn']
    print(f"Load Balancer created: {lb_arn}")
    return lb_arn

# Step 2: Creating a Target Group
def create_target_group():
    response = elb_client.create_target_group(
        Name=target_group_name,
        Protocol='HTTP',
        Port=80,
        VpcId=vpc_id,
        HealthCheckProtocol='HTTP',
        HealthCheckPort='80',
        HealthCheckPath='/',
        TargetType='instance'
    )
    target_group_arn = response['TargetGroups'][0]['TargetGroupArn']
    print(f"Target Group created: {target_group_arn}")
    return target_group_arn

# Step 3: Registered EC2 instances with the Target Group
def register_targets(target_group_arn):
    targets = [{'Id': instance_id} for instance_id in instance_ids]
    elb_client.register_targets(
        TargetGroupArn=target_group_arn,
        Targets=targets
    )
    print(f"Instances {instance_ids} registered with Target Group.")

# Step 4: Creating a Listener for the Load Balancer
def create_listener(lb_arn, target_group_arn):
    response = elb_client.create_listener(
        LoadBalancerArn=lb_arn,
        Protocol='HTTP',
        Port=80,
        DefaultActions=[{
            'Type': 'forward',
            'TargetGroupArn': target_group_arn
        }]
    )
    print(f"Listener created for Load Balancer: {response['Listeners'][0]['ListenerArn']}")

# Deploying the ALB and register EC2 instances
def deploy_load_balancer():
    lb_arn = create_load_balancer()
    target_group_arn = create_target_group()
    register_targets(target_group_arn)
    create_listener(lb_arn, target_group_arn)

# Executed the deployment
deploy_load_balancer()

import boto3

# Initializing the boto3 clients
asg_client = boto3.client('autoscaling')
ec2_client = boto3.client('ec2')
elb_client = boto3.client('elbv2')  # For Load Balancer operations

# Defining parameters
launch_configuration_name = 'manish-launch-config'
auto_scaling_group_name = 'manish-asg'
vpc_id = 'vpc-0321f38a7b594180d'  
subnets = ['subnet-09bd0e0acc92d4efa', 'subnet-0f30c30418def6379'] 
target_group_arn = 'arn:aws:elasticloadbalancing:us-west-2:975050024946:targetgroup/manishtgtg/3801181b448164e0' 

# Specifying the instance IDs of the existing instances
instance_ids = ['i-028887cd4ee1c9a2c', 'i-07dab6cc77c1064b2']  # Replace with your EC2 Instance IDs

# Step 1: Creating Launch Configuration
def create_launch_configuration():
    response = asg_client.create_launch_configuration(
        LaunchConfigurationName=launch_configuration_name,
        ImageId='ami-0c65913e98a358f43',  # Amazon Linux 2 AMI
        InstanceType='t4g.micro', #instance type
        KeyName='manish',  # existing key pair name
        SecurityGroups=['sg-09f2f07262c80b0e8'],  # security group
    )
    print(f"Launch Configuration created: {launch_configuration_name}")

# Step 2: Creating Auto Scaling Group
def create_auto_scaling_group():
    response = asg_client.create_auto_scaling_group(
        AutoScalingGroupName=auto_scaling_group_name,
        LaunchConfigurationName=launch_configuration_name,
        MinSize=2,  # Minimum number of instances
        MaxSize=5,  # Maximum number of instances
        DesiredCapacity=2,  # Desired number of instances
        VPCZoneIdentifier=','.join(subnets),  # Subnet IDs
        TargetGroupARNs=[target_group_arn],  # Attaching the target group to the ASG
    )
    print(f"Auto Scaling Group created: {auto_scaling_group_name}")

# Step 3: Attaching existing instances to the ASG
def attach_instances_to_asg():
    response = asg_client.attach_instances(
        AutoScalingGroupName=auto_scaling_group_name,
        InstanceIds=instance_ids,
    )
    print(f"Instances {instance_ids} attached to Auto Scaling Group.")

# Step 4: Setting up Scaling Policies
def create_scaling_policies():
    asg_client.put_scaling_policy(
        AutoScalingGroupName=auto_scaling_group_name,
        PolicyName='scale-out',
        AdjustmentType='ChangeInCapacity',
        ScalingAdjustment=1,
        Cooldown=300,
    )
    asg_client.put_scaling_policy(
        AutoScalingGroupName=auto_scaling_group_name,
        PolicyName='scale-in',
        AdjustmentType='ChangeInCapacity',
        ScalingAdjustment=-1,
        Cooldown=300,
    )
    print("Scaling policies created.")

# Executing the setup
create_launch_configuration()
create_auto_scaling_group()
attach_instances_to_asg()
create_scaling_policies()

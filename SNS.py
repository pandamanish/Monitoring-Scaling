import boto3
import zipfile
import os

# Initialized AWS clients
sns_client = boto3.client('sns')
lambda_client = boto3.client('lambda')

# Defined SNS topic names
topics = {
    "HealthIssues": "HealthIssues",
    "ScalingEvents": "ScalingEvents",
    "HighTraffic": "HighTraffic"
}

# Created SNS topics and stored their ARNs
topic_arns = {}
for name, display_name in topics.items():
    response = sns_client.create_topic(Name=display_name)
    topic_arns[name] = response['TopicArn']

print("SNS Topics created:")
print(topic_arns)

# Existing IAM Role ARN
lambda_role_arn = 'arn:aws:iam::975050024946:role/LambdaSNSPublishRole'  #  existing role ARN

# Creating Lambda function code file
lambda_function_code = """
import json
import boto3

def lambda_handler(event, context):
    sns = boto3.client('sns')
    
    # Example message
    message = "Alert: " + event['alert_type'] + " occurred."
    
    # Publish to SNS Topic
    sns.publish(
        TopicArn=event['topic_arn'],
        Message=message,
        Subject='Alert Notification'
    )
    return {
        'statusCode': 200,
        'body': json.dumps('Message sent!')
    }
"""

# Written the code to a Python file
with open('lambda_function.py', 'w') as f:
    f.write(lambda_function_code)

# Created a ZIP file containing the Python file
with zipfile.ZipFile('lambda_function.zip', 'w') as zipf:
    zipf.write('lambda_function.py')

# Created the Lambda function using the ZIP file
with open('lambda_function.zip', 'rb') as zipf:
    response = lambda_client.create_function(
        FunctionName='SNSAlertLambda',
        Runtime='python3.8',
        Role=lambda_role_arn,
        Handler='lambda_function.lambda_handler',
        Code={
            'ZipFile': zipf.read()
        },
        Description='Lambda function to publish SNS notifications.',
        Timeout=30,
        MemorySize=128,
    )

print("Lambda function created:", response['FunctionArn'])

# Subscribe to SNS topics with Lambda function
for name, topic_arn in topic_arns.items():
    sns_client.subscribe(
        TopicArn=topic_arn,
        Protocol='lambda',
        Endpoint=response['FunctionArn']
    )
    print(f"Lambda function subscribed to {name} topic.")

# Email Subscription (replace with my email)
email_address = 'pandamanish75@gmail.com'  

# Subscribed the email to each topic
for topic_arn in topic_arns.values():
    response = sns_client.subscribe(
        TopicArn=topic_arn,
        Protocol='email',
        Endpoint=email_address
    )
    print(f"Subscription request sent to {email_address} for topic {topic_arn}. Check your email to confirm the subscription.")

# Confirming the subscription
print("Check your email for confirmation to complete the subscription.")

# Cleaned up the generated files
os.remove('lambda_function.py')
os.remove('lambda_function.zip')

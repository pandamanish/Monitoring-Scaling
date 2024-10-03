import boto3
import os

# Initializing S3 resource
s3 = boto3.client('s3')

bucket_name = 'manish-new-boto'

# Creating S3 bucket
def create_s3_bucket(bucket_name):
    response = s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={
        'LocationConstraint': boto3.Session().region_name})
    print(f'S3 bucket {bucket_name} created.')
    return response

# Uploaded one static web file to the bucket
def upload_static_files(bucket_name, folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            s3.upload_file(os.path.join(root, file), bucket_name, file)
            print(f'Uploaded {file} to {bucket_name}')

create_s3_bucket(bucket_name)
upload_static_files(bucket_name, 'C:/Users/17282/OneDrive/Documents/Python_Scripts/Monitoring&Scaling/index.html')  #directory for index.html static fiole

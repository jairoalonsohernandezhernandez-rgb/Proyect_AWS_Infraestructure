import boto3
from botocore.exceptions import ClientError
import os

s3_client = boto3.client("s3", region_name="us-east-2")

def check_s3_status(bucket_name):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return 1
    except ClientError:
        return 0


sqs_client = boto3.client("sqs", region_name="us-east-1")

def check_sqs_status(queue_url):
    try:
        sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["All"])
        return 1
    except ClientError:
        return 0


lambda_client = boto3.client("lambda", region_name="us-east-2")

def check_lambda_status(function_name):
    try:
        lambda_client.get_function(FunctionName=function_name)
        return 1
    except ClientError:
        return 0


api_gateway_client = boto3.client("apigateway", region_name="us-east-2")

def check_api_gateway_status(api_id):
    try:
        api_gateway_client.get_rest_api(restApiId=api_id)
        return 1
    except ClientError:
        return 0


def gather_all_metrics():
    metrics = {
        "s3_status": check_s3_status(os.getenv("S3_BUCKET_NAME")),
        "sqs_status": check_sqs_status(os.getenv("SQS_QUEUE_URL")),
        "lambda_status": check_lambda_status(os.getenv("LAMBDA_FUNCTION_NAME")),
        "api_gateway_status": check_api_gateway_status(os.getenv("API_GATEWAY_ID"))
    }
    return metrics
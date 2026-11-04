import boto3
from botocore.exceptions import ClientError
import os
import sys

def _log(servicio, error):
    codigo = error.response["Error"]["Code"]
    print(f"[{servicio}] fallo: {codigo}", file=sys.stderr)

def _get_env(nombre):
    valor = os.getenv(nombre)
    if not valor:
        print(f"Variable de entorno {nombre} no definida", file=sys.stderr)
    return valor

s3_client = boto3.client("s3", region_name="us-east-2")

def check_s3_status(bucket_name):
    if not bucket_name:
        return 0
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return 1
    except ClientError as e:
        _log("s3", e)
        return 0


sqs_client = boto3.client("sqs", region_name="us-east-2")

def check_sqs_status(queue_url):
    if not queue_url:
        return 0
    try:
        sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["All"])
        return 1
    except ClientError as e:
        _log("sqs", e)
        return 0


lambda_client = boto3.client("lambda", region_name="us-east-2")

def check_lambda_status(function_name):
    if not function_name:
        return 0
    try:
        lambda_client.get_function(FunctionName=function_name)
        return 1
    except ClientError as e:
        _log("lambda", e)
        return 0


api_gateway_client = boto3.client("apigateway", region_name="us-east-2")

def check_api_gateway_status(api_id):
    if not api_id:
        return 0
    try:
        api_gateway_client.get_rest_api(restApiId=api_id)
        return 1
    except ClientError as e:
        _log("api_gateway", e)
        return 0


def gather_all_metrics():
    metrics = {
        "s3_status": check_s3_status(_get_env("S3_BUCKET_NAME")),
        "sqs_status": check_sqs_status(_get_env("SQS_QUEUE_URL")),
        "lambda_status": check_lambda_status(_get_env("LAMBDA_FUNCTION_NAME")),
        "api_gateway_status": check_api_gateway_status(_get_env("API_GATEWAY_ID"))
    }
    return metrics
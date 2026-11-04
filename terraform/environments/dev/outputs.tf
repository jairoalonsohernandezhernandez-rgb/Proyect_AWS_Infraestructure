output "s3_bucket_name" {
  description = "Nombre del bucket"
  value = module.s3_bucket.bucket_name
}

output "lambda_function_name" {
    description = "Nombre de la función Lambda"
    value = module.lambda_function.lambda_function_name
}

output "sqs_queue_url" {
    description = "URL de la cola SQS"
    value = module.sqs_queue.queue_url
}

output "api_gateway_id" {
    description = "ID de la API Gateway"
    value = module.api_gateway.rest_api_id
}
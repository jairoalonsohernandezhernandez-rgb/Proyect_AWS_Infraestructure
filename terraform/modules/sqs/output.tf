output "queue_id" {
    description = "ID de la cola"
    value = aws_sqs_queue.main.id
}

output "queue_arn" {
    description = "arn de la cola"
    value = aws_sqs_queue.main.arn
}

output "queue_name" {
    description = "Nombre de la cola principal"
    value = aws_sqs_queue.main.name
}

output "dlq_arn" {
    description = "ARN de la Dead Letter Queue"
    value = aws_sqs_queue.dlq.arn
}

output "queue_url" {
    description = "URL de la cola"
    value = aws_sqs_queue.main.url
}
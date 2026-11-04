output "bucket_arn" {
  description = "El ARN del bucket de S3"
  value = aws_s3_bucket.bucket_principal.arn
}
output "bucket_id" {
  description = "El ID del bucket de S3"
  value = aws_s3_bucket.bucket_principal.id
}

output "bucket_name" {
  description = "El nombre del bucket de S3"
  value = aws_s3_bucket.bucket_principal.bucket
}
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.region
  # la URL de la cola termina en .../<cuenta>/<nombre-de-la-cola>
  sqs_name   = element(split("/", module.sqs_queue.queue_url), 4)
}

data "aws_iam_policy_document" "health_check" {
  statement {
    actions   = ["s3:ListBucket"]
    resources = ["arn:aws:s3:::${module.s3_bucket.bucket_name}"]
  }
  statement {
    actions   = ["sqs:GetQueueAttributes"]
    resources = ["arn:aws:sqs:${local.region}:${local.account_id}:${local.sqs_name}"]
  }
  statement {
    actions   = ["lambda:GetFunction"]
    resources = ["arn:aws:lambda:${local.region}:${local.account_id}:function:${module.lambda_function.lambda_function_name}"]
  }
  statement {
    actions   = ["apigateway:GET"]
    resources = ["arn:aws:apigateway:${local.region}::/restapis/${module.api_gateway.rest_api_id}"]
  }
}

resource "aws_iam_role_policy" "health_check" {
  name   = "health-check-lectura"
  role   = "dev-github-actions-role"   # el nombre de tu rol de OIDC
  policy = data.aws_iam_policy_document.health_check.json
}
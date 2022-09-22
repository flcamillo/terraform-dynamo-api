# define a trusted policy do api gateway
data "aws_iam_policy_document" "api_gateway_trusted_policy_doc" {
  statement {
    effect = "Allow"
    principals {
      type = "Service"
      identifiers = [
        "apigateway.amazonaws.com"
      ]
    }
    actions = ["sts:AssumeRole"]
  }
}

# cria a role do api gateway com a trusted policy
resource "aws_iam_role" "api_gateway_role" {
  name               = var.api_gateway_role_name
  assume_role_policy = data.aws_iam_policy_document.api_gateway_trusted_policy_doc.json
}

# define a policy de acesso do api gateway
data "aws_iam_policy_document" "api_gateway_policy_doc" {
  statement {
    effect    = "Allow"
    resources = ["arn:aws:logs:*:*:*"]
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
      "logs:PutLogEvents",
      "logs:GetLogEvents",
      "logs:FilterLogEvents"
    ]
  }
}

# cria a policy do api gateway com os acessos definidos
resource "aws_iam_policy" "api_gateway_policy" {
  name        = var.api_gateway_policy_name
  policy      = data.aws_iam_policy_document.api_gateway_policy_doc.json
  path        = "/"
  description = "Policy de acesso para o API Gateway"
}

# associa a role com a policy
resource "aws_iam_role_policy_attachment" "attach_api_gateway_role" {
  role       = aws_iam_role.api_gateway_role.name
  policy_arn = aws_iam_policy.api_gateway_policy.arn
}

# define a role no api gateway
resource "aws_api_gateway_account" "demo" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_role.arn
}

# define o arquivo swagger da api
data "template_file" "swagger_file" {
  template = file("${var.swagger_root}/swagger.yaml")
  vars = {
    region          = "${data.aws_region.current.name}"
    lambda_arn = aws_lambda_function.lambda.arn
  }
}

# cria o api gateway
resource "aws_api_gateway_rest_api" "api_gateway" {
  name = var.apigateway_name
  body = data.template_file.swagger_file.rendered
  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

# define a trigger para recriar o api gateway
resource "aws_api_gateway_deployment" "api_deployment" {
  rest_api_id = aws_api_gateway_rest_api.api_gateway.id
  triggers = {
    redeployment = sha1("${data.template_file.swagger_file.rendered}")
  }
  lifecycle {
    create_before_destroy = true
  }
}

# define o estagio do api gateway
resource "aws_api_gateway_stage" "api_stage" {
  deployment_id = aws_api_gateway_deployment.api_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.api_gateway.id
  stage_name    = "dev"
}

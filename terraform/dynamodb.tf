# cria a tabela do dynamodb
resource "aws_dynamodb_table" "users" {
  name           = var.tb_users
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"
  attribute {
    name = "id"
    type = "S"
  }
}
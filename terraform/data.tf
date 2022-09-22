# identifica a conta que esta sendo utilizada
data "aws_caller_identity" "current" {}

# identifica a região que esta sendo utilizada
data "aws_region" "current" {}
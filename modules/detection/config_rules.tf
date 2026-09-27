locals {
  config_rules = {
    "s3-bucket-level-public-access-prohibited" = {
      identifier = "S3_BUCKET_LEVEL_PUBLIC_ACCESS_PROHIBITED"
      scope      = ["AWS::S3::Bucket"]
    }
    "restricted-ssh" = {
      identifier = "INCOMING_SSH_DISABLED"
      scope      = ["AWS::EC2::SecurityGroup"]
    }
    "restricted-common-ports" = {
      identifier = "RESTRICTED_INCOMING_TRAFFIC"
      scope      = ["AWS::EC2::SecurityGroup"]
      parameters = {
        blockedPort1 = "22"
        blockedPort2 = "3389"
        blockedPort3 = "5432"
      }
    }
    "rds-instance-public-access-check" = {
      identifier = "RDS_INSTANCE_PUBLIC_ACCESS_CHECK"
      scope      = ["AWS::RDS::DBInstance"]
    }
    "ec2-imdsv2-check" = {
      identifier = "EC2_IMDSV2_CHECK"
      scope      = ["AWS::EC2::Instance"]
    }
    "cloudtrail-enabled" = {
      identifier = "CLOUD_TRAIL_ENABLED"
      frequency  = "One_Hour"
      enabled    = var.create_trail
    }
  }

  active_config_rules = {
    for name, rule in local.config_rules : name => rule if try(rule.enabled, true)
  }
}

resource "aws_config_config_rule" "managed" {
  for_each = local.active_config_rules

  name                        = "${var.project}-${each.key}"
  input_parameters            = try(jsonencode(each.value.parameters), null)
  maximum_execution_frequency = try(each.value.frequency, null)

  source {
    owner             = "AWS"
    source_identifier = each.value.identifier
  }

  dynamic "scope" {
    for_each = try(each.value.scope, null) == null ? [] : [each.value.scope]

    content {
      compliance_resource_types = scope.value
    }
  }

  depends_on = [aws_config_configuration_recorder_status.main]
}

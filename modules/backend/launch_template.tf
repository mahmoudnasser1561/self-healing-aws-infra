data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

locals {
  user_data = templatefile("${path.module}/instance/user-data.sh.tftpl", {
    db_host       = var.db_address
    db_secret_arn = var.db_secret_arn
    region        = data.aws_region.current.name
    bucket        = aws_s3_bucket.releases.id
    deploy_script = chomp(file("${path.module}/instance/deploy-release.sh"))
    service_unit  = chomp(file("${path.module}/instance/app.service"))
    agent_config = chomp(templatefile("${path.module}/instance/cloudwatch-agent.json.tftpl", {
      log_group = aws_cloudwatch_log_group.app.name
    }))
  })
}

resource "aws_launch_template" "app" {
  name                   = "${var.project}-app"
  image_id               = nonsensitive(data.aws_ssm_parameter.al2023.value)
  instance_type          = "t3.micro"
  update_default_version = true
  vpc_security_group_ids = [var.app_sg_id]
  user_data              = base64encode(local.user_data)

  iam_instance_profile {
    name = aws_iam_instance_profile.app.name
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size           = 8
      volume_type           = "gp3"
      encrypted             = true
      delete_on_termination = true
    }
  }

  tag_specifications {
    resource_type = "instance"

    tags = {
      Name    = "${var.project}-app"
      Project = var.project
    }
  }

  tag_specifications {
    resource_type = "volume"

    tags = {
      Name    = "${var.project}-app"
      Project = var.project
    }
  }
}

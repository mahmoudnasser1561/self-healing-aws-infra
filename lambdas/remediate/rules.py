import os

import boto3

PROJECT_PREFIX = os.environ.get("PROJECT_PREFIX", "self-healing-aws-infra-")
PROJECT = PROJECT_PREFIX.rstrip("-")

s3 = boto3.client("s3")
ec2 = boto3.client("ec2")
rds = boto3.client("rds")
cloudtrail = boto3.client("cloudtrail")

BLOCK_FLAGS = (
    "BlockPublicAcls",
    "IgnorePublicAcls",
    "BlockPublicPolicy",
    "RestrictPublicBuckets",
)


def has_project_tag(tags):
    return any(
        t.get("Key") == "Project" and t.get("Value") == PROJECT for t in tags or []
    )


def fix_public_access_block(detail):
    bucket = detail["requestParameters"]["bucketName"]
    if not bucket.startswith(PROJECT_PREFIX):
        return None
    try:
        config = s3.get_public_access_block(Bucket=bucket)[
            "PublicAccessBlockConfiguration"
        ]
    except s3.exceptions.ClientError as error:
        code = error.response["Error"]["Code"]
        if code == "NoSuchBucket":
            return None
        config = {}  # NoSuchPublicAccessBlockConfiguration: treat as all off
    if all(config.get(flag) for flag in BLOCK_FLAGS):
        return None
    s3.put_public_access_block(
        Bucket=bucket,
        PublicAccessBlockConfiguration={flag: True for flag in BLOCK_FLAGS},
    )
    return f"turned all four public access block settings on for {bucket}"


def fix_open_ingress(detail):
    group_id = detail["requestParameters"]["groupId"]
    group = ec2.describe_security_groups(GroupIds=[group_id])["SecurityGroups"][0]
    if not has_project_tag(group.get("Tags")):
        return None
    rules_now = ec2.describe_security_group_rules(
        Filters=[{"Name": "group-id", "Values": [group_id]}]
    )["SecurityGroupRules"]
    open_rules = [
        r
        for r in rules_now
        if not r["IsEgress"]
        and (r.get("CidrIpv4") == "0.0.0.0/0" or r.get("CidrIpv6") == "::/0")
    ]
    if not open_rules:
        return None
    ec2.revoke_security_group_ingress(
        GroupId=group_id,
        SecurityGroupRuleIds=[r["SecurityGroupRuleId"] for r in open_rules],
    )
    return f"revoked {len(open_rules)} world-open ingress rule(s) on {group_id}"


def fix_public_rds(detail):
    identifier = detail["requestParameters"]["dBInstanceIdentifier"]
    if not identifier.startswith(PROJECT_PREFIX):
        return None
    instance = rds.describe_db_instances(DBInstanceIdentifier=identifier)[
        "DBInstances"
    ][0]
    if not instance.get("PubliclyAccessible"):
        return None
    rds.modify_db_instance(
        DBInstanceIdentifier=identifier, PubliclyAccessible=False, ApplyImmediately=True
    )
    return f"set PubliclyAccessible back to false on {identifier}"


def fix_imdsv2(detail):
    # CloudTrail nests this one call's parameters one level deeper than the
    # other four rules, inside ModifyInstanceMetadataOptionsRequest -- see
    # input.json's captured EC2-1 event.
    instance_id = detail["requestParameters"]["ModifyInstanceMetadataOptionsRequest"][
        "InstanceId"
    ]
    instance = ec2.describe_instances(InstanceIds=[instance_id])
    instance = instance["Reservations"][0]["Instances"][0]
    if not has_project_tag(instance.get("Tags")):
        return None
    if instance["MetadataOptions"]["HttpTokens"] == "required":
        return None
    ec2.modify_instance_metadata_options(
        InstanceId=instance_id, HttpTokens="required", HttpEndpoint="enabled"
    )
    return f"set HttpTokens back to required on {instance_id}"


def fix_stopped_trail(detail):
    name = detail["requestParameters"]["name"]
    if not name.startswith(PROJECT):
        return None
    status = cloudtrail.get_trail_status(Name=name)
    if status["IsLogging"]:
        return None
    cloudtrail.start_logging(Name=name)
    return f"restarted logging on trail {name}"


RULES = {
    "DeleteBucketPublicAccessBlock": fix_public_access_block,
    "PutBucketPublicAccessBlock": fix_public_access_block,
    "AuthorizeSecurityGroupIngress": fix_open_ingress,
    "ModifyDBInstance": fix_public_rds,
    "ModifyInstanceMetadataOptions": fix_imdsv2,
    "StopLogging": fix_stopped_trail,
}

import boto3
import pytest

import rules

BUCKET = "self-healing-aws-infra-frontend-123456789012"
ALL_ON = {flag: True for flag in rules.BLOCK_FLAGS}


def event(event_name, **params):
    return {"eventName": event_name, "requestParameters": params, "eventID": "evt-1"}


# --- S3-1 -------------------------------------------------------------


def test_s3_1_turns_the_block_back_on(cloud):
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket=BUCKET)
    s3.put_public_access_block(Bucket=BUCKET, PublicAccessBlockConfiguration=ALL_ON)
    s3.delete_public_access_block(Bucket=BUCKET)

    result = rules.fix_public_access_block(
        event("DeleteBucketPublicAccessBlock", bucketName=BUCKET)
    )

    assert result is not None
    assert (
        s3.get_public_access_block(Bucket=BUCKET)["PublicAccessBlockConfiguration"]
        == ALL_ON
    )


def test_s3_1_leaves_a_compliant_bucket_alone(cloud):
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket=BUCKET)
    s3.put_public_access_block(Bucket=BUCKET, PublicAccessBlockConfiguration=ALL_ON)

    assert (
        rules.fix_public_access_block(
            event("PutBucketPublicAccessBlock", bucketName=BUCKET)
        )
        is None
    )


def test_s3_1_ignores_a_bucket_outside_the_project(cloud):
    # a real bucket, left with no public access block at all, so the only
    # thing stopping the fix from "helping" it is the scope check
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="someone-elses-bucket")

    assert (
        rules.fix_public_access_block(
            event("DeleteBucketPublicAccessBlock", bucketName="someone-elses-bucket")
        )
        is None
    )
    with pytest.raises(s3.exceptions.ClientError):
        s3.get_public_access_block(Bucket="someone-elses-bucket")


# --- SG-1 ---------------------------------------------------------------


def test_sg_1_revokes_the_world_open_rule(cloud):
    ec2 = boto3.client("ec2")
    vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]["VpcId"]
    group = ec2.create_security_group(GroupName="g", Description="d", VpcId=vpc)[
        "GroupId"
    ]
    ec2.create_tags(
        Resources=[group], Tags=[{"Key": "Project", "Value": "self-healing-aws-infra"}]
    )
    ec2.authorize_security_group_ingress(
        GroupId=group,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            }
        ],
    )

    result = rules.fix_open_ingress(
        event("AuthorizeSecurityGroupIngress", groupId=group)
    )

    assert result is not None
    left = ec2.describe_security_group_rules(
        Filters=[{"Name": "group-id", "Values": [group]}]
    )["SecurityGroupRules"]
    assert not any(r.get("CidrIpv4") == "0.0.0.0/0" and not r["IsEgress"] for r in left)


def test_sg_1_ignores_a_group_outside_the_project(cloud):
    ec2 = boto3.client("ec2")
    vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]["VpcId"]
    group = ec2.create_security_group(GroupName="g", Description="d", VpcId=vpc)[
        "GroupId"
    ]
    ec2.authorize_security_group_ingress(
        GroupId=group,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            }
        ],
    )

    assert (
        rules.fix_open_ingress(event("AuthorizeSecurityGroupIngress", groupId=group))
        is None
    )


# --- RDS-1 ----------------------------------------------------------------


def test_rds_1_turns_public_access_back_off(cloud):
    rds = boto3.client("rds")
    dbid = "self-healing-aws-infra-postgres"
    rds.create_db_instance(
        DBInstanceIdentifier=dbid,
        DBInstanceClass="db.t3.micro",
        Engine="postgres",
        MasterUsername="app",
        MasterUserPassword="x",
        AllocatedStorage=20,
        PubliclyAccessible=True,
    )

    result = rules.fix_public_rds(event("ModifyDBInstance", dBInstanceIdentifier=dbid))

    assert result is not None
    assert (
        rds.describe_db_instances(DBInstanceIdentifier=dbid)["DBInstances"][0][
            "PubliclyAccessible"
        ]
        is False
    )


def test_rds_1_leaves_a_private_database_alone(cloud):
    rds = boto3.client("rds")
    dbid = "self-healing-aws-infra-postgres"
    rds.create_db_instance(
        DBInstanceIdentifier=dbid,
        DBInstanceClass="db.t3.micro",
        Engine="postgres",
        MasterUsername="app",
        MasterUserPassword="x",
        AllocatedStorage=20,
        PubliclyAccessible=False,
    )

    assert (
        rules.fix_public_rds(event("ModifyDBInstance", dBInstanceIdentifier=dbid))
        is None
    )


# --- EC2-1 ------------------------------------------------------------------
# moto does not implement modify_instance_metadata_options (as of 5.0.11), so
# these use a small fake client instead of a real AWS/moto call.


class FakeEC2:
    def __init__(self, http_tokens, tagged=True):
        self.instance = {
            "Tags": (
                [{"Key": "Project", "Value": "self-healing-aws-infra"}]
                if tagged
                else []
            ),
            "MetadataOptions": {"HttpTokens": http_tokens},
        }
        self.modify_calls = []

    def describe_instances(self, InstanceIds):
        return {"Reservations": [{"Instances": [self.instance]}]}

    def modify_instance_metadata_options(self, **kwargs):
        self.modify_calls.append(kwargs)


def test_ec2_1_sets_http_tokens_back_to_required(monkeypatch):
    fake = FakeEC2(http_tokens="optional")
    monkeypatch.setattr(rules, "ec2", fake)

    result = rules.fix_imdsv2(
        event(
            "ModifyInstanceMetadataOptions",
            ModifyInstanceMetadataOptionsRequest={"InstanceId": "i-1"},
        )
    )

    assert result is not None
    assert fake.modify_calls == [
        {"InstanceId": "i-1", "HttpTokens": "required", "HttpEndpoint": "enabled"}
    ]


def test_ec2_1_leaves_a_hardened_instance_alone(monkeypatch):
    fake = FakeEC2(http_tokens="required")
    monkeypatch.setattr(rules, "ec2", fake)

    result = rules.fix_imdsv2(
        event(
            "ModifyInstanceMetadataOptions",
            ModifyInstanceMetadataOptionsRequest={"InstanceId": "i-1"},
        )
    )

    assert result is None
    assert fake.modify_calls == []


def test_ec2_1_ignores_an_instance_outside_the_project(monkeypatch):
    fake = FakeEC2(http_tokens="optional", tagged=False)
    monkeypatch.setattr(rules, "ec2", fake)

    result = rules.fix_imdsv2(
        event(
            "ModifyInstanceMetadataOptions",
            ModifyInstanceMetadataOptionsRequest={"InstanceId": "i-1"},
        )
    )

    assert result is None
    assert fake.modify_calls == []


# --- CT-1 -------------------------------------------------------------------


def test_ct_1_restarts_logging(cloud):
    boto3.client("s3").create_bucket(Bucket="trail-bucket-123456789012")
    ct = boto3.client("cloudtrail")
    name = "self-healing-aws-infra"
    ct.create_trail(Name=name, S3BucketName="trail-bucket-123456789012")
    ct.start_logging(Name=name)
    ct.stop_logging(Name=name)

    result = rules.fix_stopped_trail(event("StopLogging", name=name))

    assert result is not None
    assert ct.get_trail_status(Name=name)["IsLogging"] is True


def test_ct_1_leaves_a_logging_trail_alone(cloud):
    boto3.client("s3").create_bucket(Bucket="trail-bucket-123456789012")
    ct = boto3.client("cloudtrail")
    name = "self-healing-aws-infra"
    ct.create_trail(Name=name, S3BucketName="trail-bucket-123456789012")
    ct.start_logging(Name=name)

    assert rules.fix_stopped_trail(event("StopLogging", name=name)) is None


def test_ct_1_ignores_a_trail_outside_the_project(cloud):
    boto3.client("s3").create_bucket(Bucket="trail-bucket-123456789012")
    ct = boto3.client("cloudtrail")
    ct.create_trail(
        Name="someone-elses-trail", S3BucketName="trail-bucket-123456789012"
    )
    ct.start_logging(Name="someone-elses-trail")
    ct.stop_logging(Name="someone-elses-trail")

    result = rules.fix_stopped_trail(event("StopLogging", name="someone-elses-trail"))

    assert result is None
    assert ct.get_trail_status(Name="someone-elses-trail")["IsLogging"] is False

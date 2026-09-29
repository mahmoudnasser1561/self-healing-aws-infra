"""Backend architecture and delivery-lane diagrams.

    python3 docs/diagrams/backend_overview.py

Requires: pip install diagrams   (and the graphviz `dot` binary on PATH)
"""

import os
from html import escape

import diagrams
from diagrams import Edge, Node
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.general import Users
from diagrams.aws.management import Cloudwatch, SSM
from diagrams.aws.network import ALB, CloudFront, NATGateway
from diagrams.aws.security import WAF, SecretsManager
from diagrams.aws.storage import S3
from diagrams.onprem.ci import GithubActions

from backend_release_flow import FILLS, FLOW, GREY, MUTED, OK, box, canvas, card, icon, link


def resource_icon(cls):
    root = os.path.dirname(os.path.dirname(diagrams.__file__))
    return os.path.join(root, cls._icon_dir, cls._icon)


def services_card(title, rows):
    bg, pen = FILLS["aws"]
    body = "".join(
        f'<tr><td fixedsize="true" width="52" height="52"><img src="{resource_icon(cls)}" scale="true"/></td>'
        f'<td align="left"><font point-size="19"><b>{escape(name)}</b></font><br align="left"/>'
        f'<font point-size="16" color="{MUTED}">{escape(detail)}</font><br align="left"/></td></tr>'
        for cls, name, detail in rows
    )
    label = (
        f'<<table border="3" color="{pen}" bgcolor="{bg}" cellborder="0" cellspacing="6" '
        f'cellpadding="8" style="rounded">'
        f'<tr><td colspan="2" align="left"><font point-size="22" color="{pen}"><b>{escape(title)}</b></font></td></tr>'
        f"{body}</table>>"
    )
    return Node(label, shape="plain", fixedsize="false", width="0", height="0", margin="0")


def runtime():
    with canvas(
        "backend_architecture",
        "Where the backend runs",
        compound="true",
        nodesep="1.2",
        ranksep="0.9",
    ) as d:
        users = icon(Users, "Browser", "one HTTPS domain")

        with box("Edge", "ci", just="r"):
            waf = icon(WAF, "WAF web ACL", "AWS managed rules")
            cdn = icon(CloudFront, "CloudFront", "TLS ends here")
            site = icon(S3, "Site bucket", "React build, private")

        with box("VPC · two availability zones", "aws", just="r"):
            with box("Public subnets", "aws", just="r"):
                alb = icon(ALB, "Load balancer", "port 80")
                nat = icon(NATGateway, "NAT Gateway", "outbound only")

            with box("Private app subnets · Auto Scaling group", "app", just="r") as asg:
                a = icon(EC2, "Instance A", "zone a", "gunicorn :8000")
                b = icon(EC2, "Instance B", "zone b", "gunicorn :8000")

            with box("Private data subnets · Multi-AZ", "ok", just="r") as data:
                db = icon(RDS, "RDS PostgreSQL", "primary, zone a", "port 5432")
                db_standby = icon(RDS, "RDS PostgreSQL", "standby, zone b")

        services = services_card(
            "AWS services, over HTTPS",
            [
                (S3, "Releases bucket", "the application tarball"),
                (SSM, "Systems Manager", "deploys and shell access"),
                (SecretsManager, "Secrets Manager", "the database credentials"),
                (Cloudwatch, "CloudWatch Logs", "application logs"),
            ],
        )

        users >> link("HTTPS", FLOW) >> cdn
        waf >> link("inspects", GREY, "dashed") >> cdn
        cdn >> link("/ and assets", FLOW) >> site
        cdn >> link("/api/*  over HTTP", FLOW) >> alb
        alb >> link("port 8000", FLOW, lhead=asg.name) >> a
        b >> link("port 5432", FLOW, ltail=asg.name, lhead=data.name) >> db
        db >> link("synchronous replication", OK, "dashed") >> db_standby
        b >> link("egress", GREY, ltail=asg.name, constraint="false") >> nat
        nat >> link("port 443", GREY, constraint="false") >> services

        for left, right in ((waf, cdn), (cdn, site), (alb, nat), (nat, services), (a, b), (db, db_standby)):
            left >> Edge(style="invis") >> right
        for group in ((waf, cdn, site), (alb, nat, services), (a, b), (db, db_standby)):
            d.dot.body.append("\t{rank=same; " + "; ".join(f'"{n._id}"' for n in group) + "}")


def lanes():
    with canvas("backend_delivery_lanes", "Three branches, three pipelines, three narrow roles"):
        with box("main · the platform", "ci"):
            main_branch = icon(GithubActions, "terraform.yml", "plan, then gated apply and destroy")
            main_role = card(
                "Role: github-actions",
                "trusted only for the prod environment",
                "creates and destroys the infrastructure",
            )
            main_out = card(
                "Builds",
                "network, RDS, load balancer,",
                "Auto Scaling group with its boot recipe,",
                "releases bucket, CloudFront, WAF",
                kind="aws",
            )

        with box("backend · the API (this branch)", "app"):
            be_branch = icon(GithubActions, "backend.yml", "test, upload, roll out, promote")
            be_role = card(
                "Role: backend-deploy",
                "trusted only for ref backend",
                "writes releases, sends the deploy command",
                kind="app",
            )
            be_out = card(
                "Delivers",
                "releases/<sha>.tar.gz and latest.tar.gz",
                "the new code on every instance",
                kind="app",
            )

        with box("frontend · the web app", "ci"):
            fe_branch = icon(GithubActions, "frontend.yml", "test, build, sync, invalidate")
            fe_role = card(
                "Role: frontend-deploy",
                "trusted only for ref frontend",
                "writes the site bucket, invalidates the cache",
            )
            fe_out = card(
                "Delivers",
                "the React build in the site bucket",
                "a fresh CloudFront cache",
                kind="aws",
            )

        contract = card(
            "The contract between main and backend",
            "Auto Scaling group tag  aws:autoscaling:groupName = self-healing-aws-infra-app",
            "Releases bucket  self-healing-aws-infra-app-releases-<account>",
            "On every instance: /usr/local/bin/deploy-release and /etc/app.env",
            "Health check  GET /api/health on port 8000",
            kind="ok",
        )

        main_branch >> link(color=FLOW) >> main_role >> link(color=FLOW) >> main_out
        be_branch >> link(color=FLOW) >> be_role >> link(color=FLOW) >> be_out
        fe_branch >> link(color=FLOW) >> fe_role >> link(color=FLOW) >> fe_out
        main_out >> link("provides", OK, "dashed") >> contract
        be_out >> link("relies on", OK, "dashed") >> contract


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    runtime()
    lanes()
    print("rendered")

"""Backend release flow diagrams.

    python3 docs/diagrams/backend_release_flow.py

Requires: pip install diagrams   (and the graphviz `dot` binary on PATH)
"""

import os
from html import escape

from diagrams import Cluster, Diagram, Edge, Node
from diagrams.aws.compute import EC2, EC2AutoScaling
from diagrams.aws.general import Users
from diagrams.aws.management import SSM
from diagrams.aws.network import ALB
from diagrams.aws.storage import S3
from diagrams.onprem.ci import GithubActions

FONT = "Noto Sans"
INK = "#1F2A37"
MUTED = "#64748B"
FLOW = "#1D4ED8"
OK = "#3F8624"
WARN = "#D13212"
GREY = "#64748B"

FILLS = {
    "ci": ("#EEF2F6", "#475569"),
    "aws": ("#FFF6E5", "#ED7100"),
    "app": ("#E6F1FB", "#147EBA"),
    "ok": ("#EAF6E7", "#3F8624"),
    "bad": ("#FDECEC", "#D13212"),
}


def canvas(filename, title, direction="TB", **graph_extra):
    return Diagram(
        "",
        filename=filename,
        show=False,
        direction=direction,
        outformat="png",
        graph_attr={
            "label": title,
            "labelloc": "t",
            "labeljust": "l",
            "fontname": FONT,
            "fontsize": "38",
            "fontcolor": INK,
            "pad": "1.0",
            "nodesep": "1.5",
            "ranksep": "1.3",
            "bgcolor": "white",
            "splines": "spline",
            "dpi": "110",
            "newrank": "true",
            **graph_extra,
        },
        node_attr={"fontname": FONT, "fontsize": "18", "fontcolor": INK},
        edge_attr={
            "fontname": FONT,
            "fontsize": "17",
            "fontcolor": INK,
            "penwidth": "2.4",
            "color": GREY,
            "arrowsize": "1.1",
        },
    )


def box(label, kind, just="l"):
    bg, pen = FILLS[kind]
    return Cluster(
        label,
        graph_attr={
            "label": label,
            "fontname": FONT,
            "fontsize": "26",
            "fontcolor": pen,
            "bgcolor": bg,
            "pencolor": pen,
            "penwidth": "2.6",
            "style": "rounded,filled",
            "labeljust": just,
            "margin": "36",
        },
    )


def card(title, *rows, kind="ci"):
    bg, pen = FILLS[kind]
    body = "".join(
        f'<tr><td align="left"><font point-size="17">{escape(r)}</font></td></tr>'
        for r in rows
    )
    label = (
        f'<<table border="3" color="{pen}" bgcolor="{bg}" cellborder="0" '
        f'cellspacing="2" cellpadding="9" style="rounded">'
        f'<tr><td align="left"><font point-size="22" color="{pen}"><b>{escape(title)}</b></font></td></tr>'
        f"{body}</table>>"
    )
    return Node(label, shape="plain", fixedsize="false", width="0", height="0", margin="0")


def icon(cls, title, *detail):
    lines = [f'<font point-size="21"><b>{escape(title)}</b></font>']
    lines += [f'<font point-size="16" color="{MUTED}">{escape(d)}</font>' for d in detail]
    return cls("<" + "<br/>".join(lines) + ">", height=str(1.9 + 0.4 * (1 + len(detail))))


def link(label=None, color=GREY, style="solid", **extra):
    attrs = {"color": color, "style": style}
    if label:
        attrs["label"] = f"  {label}  "
    attrs.update(extra)
    return Edge(**attrs)


def delivery():
    with canvas("backend_release_flow", "Backend release flow — from a push to running instances"):
        dev = icon(Users, "Developer", "git push to the backend branch")

        with box("GitHub Actions · backend.yml", "ci"):
            test = card("1 · Test", "black · flake8 · pytest", "a failure stops everything here")
            upload = card(
                "2 · Package and upload",
                "VERSION = the commit sha",
                "signs in as the deploy role (OIDC)",
                "uploads releases/<sha>.tar.gz",
            )
            rollout = card(
                "3 · Roll out",
                "deploy-release <sha> on each instance",
                "one at a time, stops at the first failure",
            )
            promote = card(
                "4 · Promote",
                "copy <sha> to latest.tar.gz",
                "runs only if step 3 succeeded",
                kind="ok",
            )

        with box("AWS", "aws"):
            bucket = card(
                "Releases bucket",
                "releases/<sha>.tar.gz  (every release)",
                "releases/latest.tar.gz  (last release that fully deployed)",
                kind="aws",
            )
            ssm = icon(SSM, "Systems Manager", "Run Command")
            with Cluster(
                "Auto Scaling group",
                graph_attr={
                    "label": "Auto Scaling group",
                    "labelloc": "b",
                    "labeljust": "l",
                    "fontname": FONT,
                    "fontsize": "26",
                    "fontcolor": FILLS["app"][1],
                    "bgcolor": FILLS["app"][0],
                    "pencolor": FILLS["app"][1],
                    "penwidth": "2.6",
                    "style": "rounded,filled",
                    "margin": "36",
                },
            ):
                first = icon(EC2, "Instance A", "updated first", "downloads <sha>")
                second = icon(EC2, "Instance B", "updated second", "downloads <sha>")

        dev >> link("push", FLOW) >> test
        test >> link("tests pass", FLOW) >> upload
        upload >> link("build succeeded", FLOW) >> rollout
        rollout >> link("every instance succeeded", OK) >> promote

        upload >> link("upload", FLOW) >> bucket
        rollout >> link("send-command", FLOW) >> ssm
        ssm >> link("1st", FLOW) >> first
        ssm >> link("2nd, after the 1st succeeded", FLOW) >> second
        promote >> link("copy", OK, constraint="false") >> bucket


def boot():
    with canvas("backend_instance_boot", "New and replacement instances — always start on the last good release"):
        asg = icon(EC2AutoScaling, "Auto Scaling group", "replaces an unhealthy instance", "or adds one when CPU is high")

        with Cluster(
            "New instance",
            graph_attr={
                "label": "New instance",
                "labelloc": "b",
                "labeljust": "l",
                "fontname": FONT,
                "fontsize": "26",
                "fontcolor": FILLS["app"][1],
                "bgcolor": FILLS["app"][0],
                "pencolor": FILLS["app"][1],
                "penwidth": "2.6",
                "style": "rounded,filled",
                "margin": "36",
            },
        ):
            prepare = card(
                "1 · Prepare",
                "install Python 3.11 and the log agent",
                "create the app user, write the env file",
            )
            fetch = card(
                "2 · deploy-release (no argument)",
                "downloads latest.tar.gz",
                "retries every 15 s until a release exists",
            )
            start = card(
                "3 · Start and check",
                "restart the app service",
                "wait for GET /api/health to answer",
            )

        guard = card(
            "Why latest is safe",
            "a release that fails its rollout is never promoted,",
            "so replacements keep booting into the last good one",
            kind="ok",
        )
        bucket = card(
            "Releases bucket",
            "latest.tar.gz  =  the last release that",
            "deployed to every instance",
            kind="aws",
        )
        alb = icon(ALB, "Load balancer", "sends traffic once /api/health answers")

        asg >> link("launches", FLOW) >> prepare
        prepare >> link(color=FLOW) >> fetch
        fetch >> link("healthy", FLOW) >> start
        start >> link("registers", FLOW) >> alb
        guard >> link(color=OK, style="dashed") >> bucket
        fetch >> link("reads latest", GREY, "dashed", constraint="false") >> bucket


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    delivery()
    boot()
    print("rendered")

SCHEMA = """
    CREATE TABLE IF NOT EXISTS components (
        id serial PRIMARY KEY,
        name text NOT NULL UNIQUE,
        tier text NOT NULL,
        description text NOT NULL
    )
"""

INSERT = """
    INSERT INTO components (name, tier, description)
    VALUES (%s, %s, %s)
    ON CONFLICT (name) DO NOTHING
"""

COMPONENTS = [
    (
        "CloudFront",
        "frontend",
        "Serves this page over HTTPS and routes /api requests to the load balancer.",
    ),
    (
        "S3 frontend bucket",
        "frontend",
        "Private bucket holding the React build; only CloudFront can read it.",
    ),
    (
        "WAF",
        "frontend",
        "Managed rules filter malicious requests at the edge.",
    ),
    (
        "Application Load Balancer",
        "backend",
        "Spreads requests across the app instances in two availability zones.",
    ),
    (
        "Auto Scaling group",
        "backend",
        "Keeps the Flask instances running and replaces any that turn unhealthy.",
    ),
    (
        "Flask instances",
        "backend",
        "Run this API in private subnets, reachable only from the load balancer.",
    ),
    (
        "Systems Manager",
        "backend",
        "Gives shell access and rolling deploys to the instances with no SSH.",
    ),
    (
        "S3 releases bucket",
        "backend",
        "Holds the tested release that each instance downloads.",
    ),
    (
        "NAT Gateway",
        "network",
        "Gives the private subnets outbound access to the internet and AWS APIs.",
    ),
    (
        "VPC Flow Logs",
        "network",
        "Record the network traffic in the VPC for auditing.",
    ),
    (
        "RDS PostgreSQL",
        "data",
        "Stores the data behind this API in private subnets, reachable only from "
        "the app tier.",
    ),
    (
        "Secrets Manager",
        "data",
        "Holds the database credentials that RDS manages; the API reads them "
        "each time it connects.",
    ),
]

# ADR-0003: TLS through CloudFront's default certificate

Status: Accepted

## Context

Users must reach the application over HTTPS, and the project owns no domain name. A certificate for a custom domain is not available, but CloudFront already sits in front of everything as the single public entry point.

## Decision

Viewers connect to the distribution's `*.cloudfront.net` name over HTTPS, using the certificate CloudFront provides for that name. HTTP requests are redirected to HTTPS. CloudFront reaches the load balancer over HTTP on port 80 inside AWS. The load balancer accepts traffic only from CloudFront's origin-facing prefix list, so nothing else can send it requests.

## Consequences

- Users get end-to-end HTTPS from their browser to the edge with no domain purchase and no certificate to issue or renew.
- The hop from CloudFront to the load balancer is not encrypted. It is confined to CloudFront's own address ranges by the security group rule.
- The application is reached at a generated `*.cloudfront.net` address; a custom domain would need its own certificate.
- The default certificate keeps CloudFront's default TLS protocol policy, which favours broad client compatibility.

# ADR-0007: Frontend delivery through S3 and CloudFront

Status: Accepted

## Context

The React application is a set of static files after it is built. It calls the backend API on `/api/...`. It should be served fast, kept away from the compute tier, and share an origin with the API so the browser needs no cross-origin configuration.

## Decision

The build output is stored in a private S3 bucket that only CloudFront can read, through origin access control. CloudFront serves the application from that bucket and forwards `/api/*` to the application load balancer with caching disabled, so both share one domain. The deploy pipeline builds the application, syncs the build to the bucket and invalidates CloudFront's cache.

## Consequences

- The web tier has no servers to run, patch or scale, and static files are served from edge locations.
- The bucket has no public access of any kind: even a mistaken bucket policy cannot expose it.
- The application and the API share an origin, so the API needs no CORS headers.
- CloudFront caches the application files, so every deploy must invalidate the cache or users keep the previous build.
- The load balancer is only reachable through CloudFront, so any request that skips it is refused.

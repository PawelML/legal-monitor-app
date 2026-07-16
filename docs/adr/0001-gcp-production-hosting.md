# ADR-0001: Host production on GCP Cloud Run and Cloud SQL

Status: proposed

Date: 2026-07-16

## Context

The initial plan names Docker Compose on a VPS as the deployment target.
PrawoRadar instead needs a production runtime that keeps the HTTP application,
scheduled ingestion, database credentials and observability separate. The
product is low traffic at MVP, but jobs must be reliable and idempotent because
a missed legal alert harms user trust.

The relevant current GCP capabilities are Cloud Run services for HTTP traffic,
Cloud Run jobs for work that runs to completion, Cloud Scheduler for recurring
invocation, Cloud SQL for PostgreSQL and Secret Manager. Cloud SQL supports the
`pgvector` extension on PostgreSQL 13 and later, preserving the planned
embedding design.

## Options considered

1. **GCP: Cloud Run + Cloud SQL (recommended).** A Cloud Run service hosts
   FastAPI; a Cloud Run job executes ingest/analysis/matching commands; Cloud
   Scheduler triggers jobs; Cloud SQL stores product data; Secret Manager holds
   secrets; Artifact Registry stores images.
2. **Single VPS with Docker Compose.** Lower conceptual overhead and one
   predictable bill, but the application owns patching, backups, job failure
   visibility, secret handling and recovery.
3. **Defer production hosting.** Keep local Compose only until after MVP
   functionality, avoiding cloud cost but delaying an important deployment and
   operational portfolio signal.

## Cost model for a small pilot

Assumptions: one EU region, a scale-to-zero web service, one small daily job,
one non-HA Cloud SQL primary, low public traffic, 20 GiB initial database
storage, no VPC connector, no paid support, and no large LLM cost included.
Amounts are planning ranges in USD, not a quote; calculate the selected region
and Cloud SQL shape in the GCP Pricing Calculator before provisioning.

| Component | Expected pilot cost | Why |
| --- | --- | --- |
| Cloud Run web service | $0–low single digits/month | Request-based billing charges while requests run; zero minimum instances avoids an idle service cost. |
| Cloud Run daily job | Usually within free tier | An official hourly one-minute job example is $0 after the free tier; a daily job is materially smaller. |
| Cloud Scheduler | $0 for up to 3 jobs; then $0.10/job/month | Pricing is per configured job, not per execution. |
| Artifact Registry | $0 below 0.5 GiB; about $0.10/GiB-month after | Retain only recent images and keep the registry co-located with runtime. |
| Cloud SQL PostgreSQL | Main fixed cost; obtain regional quote before approval | It runs continuously and pricing depends on region, CPU, memory, storage and HA. Expect it to dominate the pilot bill. |
| Secrets, logs, egress | Usually small at MVP, but bounded | Set retention, budgets and alerts; public traffic and log volume can change this. |

The approval gate is a Pricing Calculator estimate for the selected region and
single-zone Cloud SQL shape, plus a monthly budget alert. A working pilot should
have an explicit maximum monthly spend before public launch; do not infer one
from the free tiers.

## Decision

**Proposed:** adopt option 1 for public production, while retaining Docker
Compose as the local development environment. Choose one EU region after
verifying Cloud Run, Cloud SQL and Scheduler availability together; prefer the
same region for Artifact Registry, Cloud Run and Cloud SQL to avoid
cross-region transfer.

This proposal is not approved. Approval must record the approver, date, chosen
region, Cloud SQL shape and monthly budget cap in a deployment specification.

## Consequences

### Benefits

- Separates request-serving work from finite background jobs and gives each job
  execution logs, retries and status.
- Reduces server administration and creates a credible managed-cloud case
  study: IAM, secrets, deployment, observability and cost controls.
- Fits the existing explicit ingest command, `job_runs` records and idempotent
  upserts. Cloud Scheduler's at-least-once delivery is therefore safe.
- Keeps PostgreSQL and pgvector rather than adding a new vector datastore.

### Costs and risks

- Cloud SQL adds a continuous, potentially material fixed cost even when web
  traffic is near zero.
- IAM, billing, quota and deployment setup are more complex than a VPS.
- Cloud Run instances have disposable local filesystems; persistent data must
  remain in Cloud SQL or another managed store.
- A deployment error can expose secrets or public endpoints if service accounts
  and ingress are not deliberately scoped.

### Required implementation changes before deployment

- Make the web container listen on Cloud Run's injected `$PORT`, rather than a
  fixed port.
- Remove `alembic upgrade head` from the web-service startup command; run
  migrations once as a controlled deployment job.
- Add deployment configuration as infrastructure-as-code, dedicated service
  accounts with least privilege, Secret Manager bindings, Cloud SQL connection
  configuration, logging/monitoring and budget alerts.
- Keep local Compose for development. Do not add an in-container scheduler;
  Cloud Scheduler and Cloud Run jobs own production scheduling.

## References

- Cloud Run services and jobs: <https://cloud.google.com/run/docs/overview/what-is-cloud-run>
- Cloud Run pricing: <https://cloud.google.com/run/pricing>
- Cloud SQL pricing and extensions: <https://cloud.google.com/sql/pricing/>;
  <https://cloud.google.com/sql/docs/postgres/extensions>
- Cloud Scheduler pricing and delivery semantics:
  <https://cloud.google.com/scheduler/pricing>;
  <https://cloud.google.com/scheduler/docs/overview>
- Artifact Registry pricing: <https://cloud.google.com/artifact-registry/pricing>

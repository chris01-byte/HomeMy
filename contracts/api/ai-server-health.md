# External AI Server Health Contract

Status: accepted architecture; implementation pending.
Owner: HomeMy platform.

## Scope

This contract defines how the on-board Linux computer observes the external AI server. It does not define the server's model, prompt, deployment, or credentials.

## Requirement

The external AI server remains available as an optional remote capability. HomeMy local boot and mandatory local safety checks must not wait indefinitely for it. An unavailable server must be visible to the customer and must not weaken local safety behavior.

## Health Check

The future health client uses an application-level request with a bounded timeout. A network ping alone is insufficient. The final protocol is open, but a successful result must identify server availability, supported capability version, and response timing without exposing credentials or private endpoint details in customer messages.

The check runs during SELF_TEST and periodically after startup. Temporary network failure may be retried with bounded backoff, but retries must not block the local event loop or restart the whole robot stack.

## State Mapping

| Condition | Lifecycle result | Customer result |
| --- | --- | --- |
| Local mandatory checks pass and AI health succeeds | READY | Full configured capability available |
| Local mandatory checks pass and AI health fails | READY_LIMITED | E-AI-001, AI functions unavailable; explicitly permitted local functions remain available |
| A mandatory local check fails | FAULT | Do not classify a local fault as an AI outage |

Only a capability explicitly marked AI-dependent may be rejected because the server is unavailable. AI availability never grants motion, changes safety thresholds, or bypasses a local interlock.

## Recovery

When a later health check succeeds, the boot manager may transition from READY_LIMITED to READY without rebooting the robot. A failed health check during an AI-dependent operation must produce a defined failed or unavailable result; it must not fabricate a model response or fall back to unsafe behavior.

## Customer Fault Record

The customer-visible record for unavailable AI is E-AI-001 with a short message such as External AI server unavailable and a clear statement of which customer functions are limited. Technical endpoint details, credentials, and raw exception messages stay in protected local diagnostics only.

## Validation

Implementation must prove server available, timeout, malformed health reply, capability mismatch, server recovery, and that a server outage cannot block local boot or alter the motion gate. No runtime integration has been performed for this document.

## Rollback

Before the external AI integration is validated, operate HomeMy without AI-dependent features. Disabling the health client must leave local boot, fault display, and safety checks functional; it must not make an unavailable server appear healthy.

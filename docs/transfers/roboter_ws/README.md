# Transfers from roboter_ws

This directory contains focused transfer records after a capability has a concrete destination in HomeMy.

## Authority

The active transfer ledger is integration/roboter_ws/TRANSFER_MANIFEST.md. This directory adds evidence and design detail; it does not replace the ledger.

## Record Format

Name each record YYYY-MM-DD-capability.md and include:

1. Source repository path and immutable commit.
2. HomeMy intent and destination.
3. Interface contract and incompatible assumptions.
4. Tests and results actually run.
5. Hardware and safety impact.
6. Known risks and rollback path.

## Context Rule

Read a transfer record only for the matching capability. Completed evidence belongs here or in docs/archive/, never in the default agent context.

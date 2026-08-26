# Runbooks

Add a runbook only when a component has a repeatable operating or recovery procedure.

Each runbook states its scope, prerequisites, safe default, exact checks, expected results, failure handling, and cleanup. It must not contain secrets, real home coordinates, or an implicit authorization to activate hardware.

Runbooks are loaded only for the component being operated; they are not part of the default agent context.

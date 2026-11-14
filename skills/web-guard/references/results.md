# Result schema, version 1

Keep findings separate from coverage. Pass/fail require executed tests and redacted evidence. Do not fabricate evidence to fill a schema.

```json
{
  "schema_version": 1,
  "run_id": "2026-11-14T120000Z-example",
  "phase": "baseline",
  "timestamp": "2026-11-14T12:00:00Z",
  "target": "https://example.com",
  "scope_id": "sha256-of-canonical-scope",
  "environment": "staging",
  "revision": "commit-or-image-digest-or-unknown",
  "test_profile": "sha256-of-test-definitions-roles-config-tool-versions",
  "coverage": [{"control":"AUTHZ","status":"not_tested","reason":"No roles"}],
  "findings": [{
    "id": "WG-001",
    "key": "AUTHZ|api/orders/:id|read|tenant-isolation",
    "title": "Cross-tenant order access",
    "severity": "high",
    "confidence": "confirmed",
    "status": "open",
    "asset": "api/orders/:id",
    "evidence": ["evidence/WG-001-redacted.txt"],
    "impact": "Other tenant orders exposed",
    "root_cause": "Missing tenant predicate",
    "fix": "Bind tenant from trusted session",
    "owner": "backend",
    "test": {
      "id": "tenant-order-read-v1",
      "surface": "staging-api",
      "role": "tenant-a-user",
      "result": "fail",
      "timestamp": "2026-11-14T12:00:00Z",
      "evidence": ["evidence/WG-001-redacted.txt"]
    }
  }]
}
```

Use phase=final for retest. Coverage: pass/fail/not_tested/not_applicable. Findings: open/fixed_unverified/verified_fixed/risk_accepted/not_retested. Severity: critical/high/medium/low/info. Confidence: confirmed/suspected. Test: pass/fail/blocked/not_tested. Use stable keys for control+asset+operation, not line numbers; preserve IDs when code moves.

Copy ALL original findings into final.json, even if scanners omit them. Only verified_fixed with a passing equivalent timestamped test/evidence can count as fixed. Preserve original evidence, append change references. Changed revision is expected. If scope/environment/profile changes, produce a paired equivalent retest or explicitly label noncomparability. Record additional regression tests outside the unchanged comparison profile or explain profile changes. The comparator verifies structural evidence only; independently assess whether evidence is real and sufficient.

Before report: scope/date/revision, methods/versions/roles, coverage gaps, confirmed vs suspected findings, impact, redacted reproduction/evidence, remediation/owners, blockers and required access.
After report: delivered/deployed revision/surface, per-ID fix and retest, new issues/regressions, remaining risks/untested areas, release decision and next steps. Include observed counts by severity, never an overall security percentage. Missing tests/findings are not fixes.

## Extension records

Keep schema_version=1; add module IDs as coverage controls with the same evidence/reason rules. Each run records module selection and unavailable access in scope.json; comparisons require equivalent selection. Keep chains.json, surface/config snapshots, budget.json and remediation.json separate from the compact state file. Store critical-flow/regression evidence in final coverage as CHANGE and any required project-specific controls.

Remediation record example: `{"id":"WG-001","owner":null,"deadline":null,"deadline_status":"unassigned","priority":"high","status":"fixed_unverified","change_refs":["changes/app.patch"],"retest_refs":[]}`. Assign dates only from user policy or mark proposed. Include risk-acceptance owner, scope and expiry only when actually authorized. Never let a deadline or accepted risk overwrite underlying technical test evidence.

Record CI policy/result, required controls, evidence age, revision/environment checks and prepared/enforced state. Use separate management-summary.md and technical-report.md; link detailed evidence instead of duplicating raw data. Budget values are measured/unavailable/explicitly estimated with source, never assumed zero.

Assurance modules use the same coverage statuses. Keep triage disposition (lead/confirmed/disputed/false_positive), risk acceptance, remediation status and test result separate; schema-v1 finding fields retain their meanings. A false-positive decision needs redacted technical evidence/history, not deletion from the baseline. Record an adjusted scoped baseline explicitly when a reclassified finding makes a paired comparison inappropriate. Do not label it verified_fixed. Maintain separate custody/signature, threat-signal, change-policy and independent-verification records per references/assurance.md. Required assurance controls become explicit gate requirements; their absence cannot silently pass. Signatures and hashes are integrity/authorship signals, not proof that observations are true.

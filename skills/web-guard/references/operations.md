# Authorized testing and changes

## Active testing
Reuse existing authorization; ask only if absent or expanded. Record exact host/path allowlist, roles, environment, limits, forbidden actions and stop conditions. Inspect each scanner check; never enable broad intrusive/exploit templates on production by default. Use synthetic fixtures and bounded evidence, not real data extraction. Prefer offline review when proof would expose data or interrupt service.

## Access and remediation
Use SSH aliases/existing agents, approved connectors or secret managers. Record connection identifiers, never values. Verify host identity through a trusted source; never disable host-key checks. No command-line secrets/env dumps or production credentials in model context. If a secret was pasted, do not repeat/save it; recommend rotation.

Inspect source/runtime/service manager/proxy/deploy method and current health. Back up relevant configs with restricted permissions; verify recovery access. Preserve existing user changes; patch code/config root causes in an isolated worktree when possible. Review frontend/backend/migration compatibility.

Write a concrete change plan: finding IDs, exact files/settings, data/downtime effects, tests, backup and rollback. Scoped reversible fixes need no repeated approval. Check existing explicit authorization before production deployment, destructive schema work, service interruption or management/firewall/key changes that can lock out users; ask only if missing, after preparing patches/tests. Possessing credentials is not unlimited deployment permission.

Validate syntax before reload; check health after deploy. Keep recovery access open and test a new management connection before closing the old one. Avoid blanket CSP/CORS changes that break login/payment. Coordinate key/session revocation with consumers. Never disable MFA/WAF/EDR to make a test pass.

## Delivery
Return a sanitized full project when manageable/requested, otherwise a clearly labelled changed-files bundle plus patch and exact base revision. Include new and binary files, deleted-path manifest and modes; git diff alone misses untracked files. Scan the exact delivery set for secrets and inspect risky files; tracked does not mean safe.

Exclude .env*, private keys, credentials, .git, databases, logs, customer uploads, audit evidence, node_modules/vendor/build caches and unrelated user changes. Preserve safe example configs using placeholders. Include SHA-256 manifest, finding-to-file mapping, installation/migration instructions, test results, failed/unavailable tests and rollback. Label prepared/staging/live state. Document server/provider changes separately; file delivery does not apply them. Persist user-facing deliverables through host-native storage when available; do not upload raw secret evidence externally.

## Release
Block confirmed auth bypass, sensitive unauthorized access, tenant failure, reachable critical RCE, exposed live secrets, dangerous public admin/data access and failed critical recovery/alert routing. Document uncertainty for missing evidence. Other high risks need time-bound acceptance by an authorized risk owner and compensating controls; never invent acceptance. Assess incident-specific legal/contract obligations without guessing deadlines.

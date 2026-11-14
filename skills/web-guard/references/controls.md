# Audit coverage

Track each row as pass/fail/not_tested/not_applicable, with evidence/reason. Separate external observation, source review, authenticated testing, infrastructure and operational evidence. This compact matrix is not exhaustive ASVS certification. Use two users/two tenants and privileged/nonprivileged roles where relevant.

| ID | Check and verification |
|---|---|
| GOV | Inventory domains/API/admin/cloud/DNS/CI/vendors/data owners; scope, RTO/RPO, threat model and single points of failure. |
| DNS | Registrar/DNS/mail MFA and recovery; DNS audit, dangling records, certificates, CAA/DNSSEC where applicable. No out-of-scope testing. |
| EDGE | CDN/WAF/upstream DDoS, IPv4/IPv6 parity, origin restrictions, trusted proxy headers, alternate ports, private cache isolation. |
| DOS | Expensive endpoints, quotas, body/time/concurrency/queue bounds, retries/circuit breaker, SMS/AI billing caps and degraded mode. Prove capacity only in authorized controlled tests. |
| NET | Private DB/cache/queue, management path, segmentation, egress/metadata access. Test allowed and denied paths. |
| HOST | Supported OS/runtime, patches, least privilege, service/file permissions, container mounts/socket/capabilities, limits and drift. |
| AUTHN | Signup/login/recovery/MFA/SSO/OAuth; replay, expiry, redirect URI, issuer/audience, account linking; enumeration/rate limits and support recovery. |
| AUTHZ | Every action/object/field/export/job/file checks server-side permissions and tenant isolation; default deny and safe policy failures. |
| SESSION | Rotation, cookie scope/flags, expiry/revocation/logout, JWT verification, refresh reuse; privilege changes reflected within defined limits. |
| INPUT | SQL/NoSQL/command/template injection, context-aware XSS protection, CSRF where relevant, traversal, deserialization, mass assignment and redirects. Trace inputs to sinks. |
| HTTP | TLS, suitable HSTS/CSP/framing/MIME/referrer, CORS, cache keys/private data, parsing disagreement/smuggling across proxies. Intrusive protocol testing in staging. |
| FILE | Allowlisted content, size/count/decompression limits, path handling, quarantine, scanning, isolated processing/nonexecuting serving origin and authorized downloads. |
| SSRF | Allowed targets/protocols, DNS/IP checks, redirects/rebinding, private/loopback/link-local/metadata restrictions and egress. Never extract internal secrets to prove impact. |
| LOGIC | Price/role tampering, webhook signature/replay, idempotency, race conditions, balances/stock/refunds and reconciliation using fixtures. |
| DATA | Classification/minimization, DB roles, encryption/key separation, retention/deletion, masked test data and secret lifecycle. |
| SUPPLY | Reachable dependency/runtime issues, lockfiles/SBOM, SAST/SCA/secrets/IaC, CI permissions, PR isolation, artifact provenance and deploy identity. Inspect scripts first. |
| SOC | App/cloud/DNS/identity/DB/CI/EDR events; time sync, correlation IDs, log protection/redaction, ingestion health and end-to-end alert routing. |
| EDR | Workload support, tamper protection, telemetry, benign simulated detection/response, isolation/recovery and overhead. No malware deployment. |
| DLP | Synthetic sensitive data, actual channel/exclusions, allowed/blocked actions and gaps. Endpoint coverage does not prove server egress coverage. |
| MAIL | Provider MFA, SPF/DKIM/DMARC alignment/rollout, routing, attachment/link controls, quarantine and account compromise detection. |
| BACKUP | Separate credentials/account, immutable/offline encrypted copies, key recovery and consistent point-in-time data; clean restore with measured RTO/RPO. |
| IR | Contacts/authority, evidence preservation, session/key revocation, provider escalation, clean rebuild and incident-specific notification assessment; tabletop drill. |
| OPTIONAL | AI/tool use: prompt injection, tool scope, isolation/cost limits. Payment/regulated data: applicable sector and vendor responsibilities. |

Treat Splunk/FortiSIEM/QRadar/Trellix as potential SIEM implementations; Trellix/ESET/Trend Micro as workload tooling and Forcepoint/Trellix as DLP examples after verifying actual version/licence/platform. Nessus/Qualys findings need validation/retest. Do not install enterprise products because listed. A URL cannot establish SOC/EDR/DLP effectiveness.

## Extended module index

Assess applicability for every module; read only relevant rows of references/extended-controls.md. Always consider CHAIN, SURFACE, ABUSE, CHANGE, TRACK, REPORT and BUDGET; assess API, CLOUD, K8S, MOBILE, THIRD, PRIVACY, CACHE, DRIFT and GATE from stack/scope/access. Unknown access/technology remains not_tested. Actual ongoing monitoring and CI activation require configured integrations; this skill invocation itself performs a bounded snapshot.

## Assurance module index

Use references/assurance.md for EVIDENCE (integrity/signing), TRIAGE (false positives/disputes), PRIORITY (contextual threat prioritization), BLAST (assumed compromise), JIT (temporary privilege), SERVICE (service identity), FAILURE (security dependency failure), DETECT (missed detection stages), RECOVERY (clean-room recovery), INTEGRITY (silent data tampering), PROVENANCE (artifact origin), AUTOFIX (change limits), SELF (skill/tool security), SECOND (independent verification) and DISCLOSE (disclosure channel). Reuse existing tests/evidence and add only depth; conditional modules do not justify expanded scope or routine dual-model use.

References: https://asvs.owasp.org/ ; https://owasp.org/projects/web-security-testing-guide ; https://cheatsheetseries.owasp.org/ ; https://csrc.nist.gov/pubs/sp/800/61/r3/final ; https://csrc.nist.gov/projects/ssdf . Look up current primary documentation only for uncertain version-specific findings/advisories/configuration; do not browse each generic control.

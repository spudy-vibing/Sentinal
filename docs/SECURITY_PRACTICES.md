# Sentinel Security Practices

Security best practices for the Sentinel UHNW Portfolio Monitoring System.

---

## 1. Data Protection

### 1.1 Encryption at Rest

**Envelope Encryption (AES-256-GCM)**
- Master Key stored in environment variable (`MASTER_ENCRYPTION_KEY`) or KMS — never hardcoded
- Unique Data Encryption Key (DEK) generated per encrypted field
- DEKs encrypted with Master Key before storage

```python
# Required implementation
class EnvelopeEncryption:
    def encrypt_field(self, plaintext: str) -> dict:
        dek = AESGCM.generate_key(bit_length=256)
        # DEK encrypts data, Master Key encrypts DEK
```

**SQLCipher Database**
- All SQLite databases use SQLCipher with AES-256 encryption
- Database key derived from `MASTER_ENCRYPTION_KEY`
- Pragma: `cipher_page_size=4096`, `kdf_iter=256000`

**Field-Level Encryption**
| Field Type | Encryption | Example |
|------------|------------|---------|
| PII (name, SSN, address) | Required | `client_profiles.encrypted_pii` |
| Financial constraints | Required | `client_profiles.constraints` |
| Tax lot details | Required | `tax_lots.*` |
| Ticker/quantity | Not required | `holdings.ticker` |

### 1.2 Encryption in Transit

- All external API calls use TLS 1.3
- Anthropic API: HTTPS only, API key in `Authorization` header
- No HTTP fallback allowed
- Certificate pinning for production deployments

### 1.3 Key Management

**Environment Variables (Development)**
```bash
# .env — NEVER commit to git
ANTHROPIC_API_KEY=sk-ant-...
MASTER_ENCRYPTION_KEY=$(openssl rand -base64 32)
```

**Production Requirements**
- Use AWS KMS, HashiCorp Vault, or similar HSM-backed solution
- Rotate Master Key quarterly
- DEKs rotated on re-encryption (triggered by key rotation)
- Key access logged to audit trail

---

## 2. Access Control

### 2.1 Role-Based Access Control (RBAC)

| Role | Permissions | Notes |
|------|-------------|-------|
| `DRIFT_AGENT` | `READ_HOLDINGS` | No PII, no tax lots |
| `TAX_AGENT` | `READ_HOLDINGS`, `READ_TAX_LOTS` | No PII |
| `COORDINATOR` | `READ_HOLDINGS`, `READ_TAX_LOTS`, `WRITE_RECOMMENDATIONS` | Orchestration only |
| `HUMAN_ADVISOR` | All read + `APPROVE_TRADES` | Full client access |
| `ADMIN` | All permissions | System configuration |

**Implementation Pattern**
```python
@require_permission(Permission.READ_CLIENT_PII)
def get_client_profile(self, client_id: str) -> dict:
    # Only human advisors can access PII
    return self._query_client_full(client_id)
```

### 2.2 Session Security Boundaries

| Session Type | Access Level | Execution Environment |
|--------------|--------------|----------------------|
| `advisor:main` | Full portfolio access | Host process |
| `analyst` | Read-only, specific portfolios | Docker sandbox |
| `client` | Own portfolio only | Docker sandbox |
| `system` | Internal processes | Host process |

**Session Constraints**
- `max_tool_calls`: Rate limiting per session
- `allowed_portfolios`: Whitelist for scoped access
- `sandbox_mode`: Enforces Docker isolation

### 2.3 Principle of Least Privilege

- Agents receive only the data needed for their task
- Drift Agent: Holdings summary without cost basis
- Tax Agent: Holdings with tax lots, no client PII
- Coordinator: Aggregated findings, never raw PII

---

## 3. Agent Security

### 3.1 Hub-and-Spoke Communication

**MANDATORY**: Sub-agents (Drift, Tax) NEVER communicate directly.

```python
# FORBIDDEN
drift_agent.send_message(tax_agent, ...)

# REQUIRED
coordinator.dispatch([drift_agent, tax_agent])
coordinator.synthesize([drift_result, tax_result])
```

**Rationale**
- Prevents circular dependencies
- Centralizes conflict resolution
- Simplifies audit trail
- Avoids state synchronization bugs

### 3.2 Sandboxed Execution

Untrusted sessions run in ephemeral Docker containers:

```python
container = docker.containers.run(
    image="sentinel-agent-runtime",
    mem_limit="512m",
    network_mode="none",  # No network access
    remove=True           # Auto-delete after execution
)
```

**Container Restrictions**
- No network access (`network_mode="none"`)
- Memory limited (512MB default)
- CPU limited (0.5 cores)
- Read-only filesystem except `/workspace`
- No privileged escalation

### 3.3 Prompt Injection Mitigation

- User inputs validated via Pydantic schemas before reaching agents
- System prompts clearly delimited from user context
- Agent outputs parsed as structured JSON (schema-validated)
- No dynamic code execution from agent outputs

---

## 4. Audit & Compliance

### 4.1 Merkle Chain Audit Log

**Immutable, Append-Only**
- Every state transition logged with SHA-256 hash
- Chain integrity verifiable: `merkle_chain.verify_integrity()`
- Tampering detectable via hash mismatch

**Logged Events**
| Event Type | Data Captured |
|------------|---------------|
| `system_initialized` | Genesis block |
| `market_event_detected` | Event ID, magnitude, sectors |
| `state_transition` | From state → To state |
| `agent_invoked` | Agent name, portfolio ID, input hash |
| `agent_completed` | Agent name, output hash, duration |
| `conflict_detected` | Conflict type, involved agents |
| `recommendation_generated` | Scenario ID, utility score |
| `human_decision` | Approve/Reject, advisor ID, timestamp |
| `trade_executed` | Trade details, confirmation ID |

### 4.2 Verification Commands

```bash
# Verify Merkle chain integrity
poetry run python -m src.main --verify-merkle

# Export audit log for compliance review
poetry run python -m src.main --export-audit --format json
```

### 4.3 Retention Policy

- Audit logs: 7 years (SEC/FINRA requirement)
- Transaction records: 7 years
- Agent interaction logs: 3 years
- Session logs: 90 days

---

## 5. Input Validation

### 5.1 Gateway Validation

All inputs pass through typed Gateway with Pydantic validation:

```python
class MarketEventInput(InputEvent):
    event_type: Literal["market_event"] = "market_event"
    affected_sectors: list[str]
    magnitude: float  # Validated: -1.0 to 1.0
    description: str  # Max length enforced
```

**Validation Rules**
- String fields: Max length, character whitelist
- Numeric fields: Range validation
- Enums: Strict value matching
- Arrays: Max items, item validation
- Dates: ISO 8601 format required

### 5.2 SQL Injection Prevention

- All database queries use parameterized statements
- No string concatenation for query building
- ORM (SQLAlchemy) preferred over raw SQL

```python
# FORBIDDEN
cursor.execute(f"SELECT * FROM holdings WHERE ticker='{ticker}'")

# REQUIRED
cursor.execute("SELECT * FROM holdings WHERE ticker=?", (ticker,))
```

### 5.3 Output Sanitization

- Agent outputs validated against JSON schema before processing
- HTML Canvas outputs sanitized (no raw user content in HTML)
- Log outputs redact PII patterns (SSN, account numbers)

---

## 6. Network Security

### 6.1 API Security

**Anthropic API**
- API key in environment variable only
- HTTPS enforced
- Retry with exponential backoff (no key exposure in logs)

**Webhook Endpoints** (if enabled)
- HMAC signature validation
- Rate limiting (100 req/min per source)
- IP allowlisting for known partners

### 6.2 Internal Communication

- Inter-process: Unix sockets with permission checks
- Agent-to-Coordinator: In-memory (asyncio.Queue)
- No external ports exposed in default configuration

---

## 7. Error Handling

### 7.1 Secure Error Messages

- Production: Generic error messages to users
- Logs: Full stack traces with PII redaction
- Never expose: File paths, database schemas, API keys

```python
# User-facing
raise UserError("Unable to process portfolio analysis")

# Internal log
logger.error(f"Analysis failed for portfolio {portfolio_id}", exc_info=True)
```

### 7.2 Failure Modes

| Failure | Response |
|---------|----------|
| API key invalid | Halt, alert admin, no retry |
| Database encryption failure | Halt, no unencrypted fallback |
| Agent timeout | Retry 2x, then escalate to human |
| Merkle verification failure | Halt all operations, alert admin |

---

## 8. Development Security

### 8.1 Dependency Management

```bash
# Check for vulnerabilities
poetry run pip-audit

# Update dependencies monthly
poetry update
```

### 8.2 Code Review Requirements

- All changes require PR review
- Security-sensitive changes require 2 reviewers
- No secrets in code (use pre-commit hooks)

### 8.3 Pre-Commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    hooks:
      - id: gitleaks  # Detect secrets
  - repo: https://github.com/PyCQA/bandit
    hooks:
      - id: bandit    # Python security linter
```

---

## 9. Incident Response

### 9.1 Security Incident Classification

| Severity | Description | Response Time |
|----------|-------------|---------------|
| Critical | Data breach, key compromise | Immediate |
| High | Unauthorized access attempt | < 1 hour |
| Medium | Failed auth attempts spike | < 4 hours |
| Low | Policy violation, no data impact | < 24 hours |

### 9.2 Response Steps

1. **Contain**: Isolate affected systems
2. **Assess**: Determine scope and impact
3. **Remediate**: Rotate keys, patch vulnerabilities
4. **Notify**: Stakeholders per regulatory requirements
5. **Review**: Post-incident analysis, update procedures

---

## 10. Compliance Checklist

| Requirement | Implementation |
|-------------|----------------|
| Data encryption at rest | AES-256-GCM envelope encryption |
| Data encryption in transit | TLS 1.3 |
| Access control | RBAC with decorator enforcement |
| Audit trail | Merkle chain, 7-year retention |
| PII protection | Field-level encryption, agent isolation |
| Key management | Environment/KMS, never hardcoded |
| Input validation | Pydantic schemas at Gateway |
| Session isolation | Docker sandboxing |

---

*Last Updated: 2024*
*Review Frequency: Quarterly*

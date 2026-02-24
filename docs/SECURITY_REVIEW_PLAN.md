# Sentinel Security Review Plan

A comprehensive security review methodology for the Sentinel UHNW Portfolio Monitoring System.

---

## Executive Summary

This plan outlines the security review process for Sentinel, covering:
- Static code analysis
- Dynamic testing
- Cryptographic verification
- Access control validation
- Audit trail integrity
- Dependency vulnerability scanning

**Deliverable**: Security Assessment Report with findings, risk ratings, and remediation guidance.

---

## 1. Review Scope

### 1.1 In-Scope Components

| Component | Priority | Review Type |
|-----------|----------|-------------|
| Gateway Layer | Critical | Code review, fuzzing |
| Encryption Module | Critical | Crypto audit |
| RBAC Implementation | Critical | Access control testing |
| Agent Communication | High | Architecture review |
| Merkle Chain | High | Integrity testing |
| Database Layer | High | SQL injection, encryption verification |
| Session Management | High | Boundary testing |
| Canvas UI Generation | Medium | XSS, injection testing |
| Webhook Handlers | Medium | Input validation |
| Logging System | Medium | PII leakage review |

### 1.2 Out-of-Scope

- Anthropic API security (third-party responsibility)
- Infrastructure/cloud security (deployment-specific)
- Physical security

---

## 2. Review Methodology

### Phase 1: Static Analysis

#### 2.1.1 Automated Security Scanning

```bash
# Run Bandit (Python security linter)
poetry run bandit -r src/ -f json -o reports/bandit_report.json

# Run Semgrep with security rules
semgrep --config=p/python --config=p/security-audit src/ --json > reports/semgrep_report.json

# Check for secrets in codebase
gitleaks detect --source . --report-path reports/secrets_report.json

# Dependency vulnerability scan
poetry run pip-audit --format json > reports/pip_audit_report.json
poetry run safety check --json > reports/safety_report.json
```

#### 2.1.2 Manual Code Review Checklist

**Cryptography**
- [ ] Master key loading from environment only
- [ ] No hardcoded keys/secrets in source
- [ ] DEK generation uses cryptographically secure RNG
- [ ] AES-256-GCM parameters correct (nonce size, tag length)
- [ ] Key derivation function has sufficient iterations
- [ ] No deprecated crypto algorithms (MD5, SHA1, DES)

**Input Validation**
- [ ] All external inputs pass through Gateway
- [ ] Pydantic models have appropriate constraints
- [ ] String lengths limited
- [ ] Numeric ranges validated
- [ ] Enum values strictly enforced
- [ ] No raw SQL string concatenation

**Access Control**
- [ ] RBAC decorators on all sensitive functions
- [ ] Permission checks cannot be bypassed
- [ ] Session boundaries enforced
- [ ] Agent isolation verified

**Output Handling**
- [ ] JSON outputs schema-validated
- [ ] HTML outputs sanitized
- [ ] Logs redact PII patterns
- [ ] Error messages don't leak internals

### Phase 2: Dynamic Testing

#### 2.2.1 RBAC Boundary Testing

**Test Matrix**

| Test Case | Actor | Target | Expected |
|-----------|-------|--------|----------|
| Agent reads PII | DRIFT_AGENT | `get_client_profile()` | PermissionError |
| Agent reads tax lots | DRIFT_AGENT | `get_tax_lots()` | PermissionError |
| Tax agent reads PII | TAX_AGENT | `get_client_profile()` | PermissionError |
| Coordinator approves | COORDINATOR | `approve_recommendation()` | PermissionError |
| Analyst writes | ANALYST | `write_recommendation()` | PermissionError |
| Client cross-access | CLIENT_A | Portfolio B | PermissionError |
| Advisor full access | HUMAN_ADVISOR | All read operations | Success |

**Test Script**
```python
# tests/security/test_rbac_boundaries.py
import pytest
from src.security.rbac import RBACContext, Role, Permission
from src.data.portfolio_access import PortfolioDataAccess

class TestRBACBoundaries:
    def test_drift_agent_cannot_read_pii(self):
        ctx = RBACContext(Role.DRIFT_AGENT)
        access = PortfolioDataAccess(ctx)

        with pytest.raises(PermissionError):
            access.get_client_profile("client_001")

    def test_tax_agent_can_read_tax_lots(self):
        ctx = RBACContext(Role.TAX_AGENT)
        access = PortfolioDataAccess(ctx)

        # Should succeed
        lots = access.get_tax_lots("portfolio_001")
        assert lots is not None

    def test_session_portfolio_isolation(self):
        # Client session for Portfolio A
        session = SessionConfig(
            session_type=SessionType.CLIENT_PORTAL,
            allowed_portfolios=["UHNW_001"]
        )
        access = PortfolioDataAccess(session.rbac_context)

        # Attempt to access Portfolio B
        with pytest.raises(PermissionError):
            access.get_holdings("UHNW_002")
```

#### 2.2.2 Input Fuzzing

**Gateway Fuzzing**
```python
# tests/security/test_gateway_fuzzing.py
from hypothesis import given, strategies as st
from src.gateway.typed_gateway import Gateway, MarketEventInput

class TestGatewayFuzzing:
    @given(st.text(min_size=0, max_size=10000))
    def test_description_field_handles_arbitrary_strings(self, desc):
        """Ensure description field doesn't crash on arbitrary input"""
        try:
            event = MarketEventInput(
                event_id="test",
                timestamp=datetime.utcnow(),
                session_id="test",
                affected_sectors=["Technology"],
                magnitude=0.01,
                description=desc
            )
            # Should either succeed or raise ValidationError
        except ValidationError:
            pass  # Expected for invalid input

    @given(st.floats(allow_nan=True, allow_infinity=True))
    def test_magnitude_rejects_invalid_floats(self, mag):
        """Magnitude should reject NaN, Inf, and out-of-range values"""
        try:
            event = MarketEventInput(
                event_id="test",
                timestamp=datetime.utcnow(),
                session_id="test",
                affected_sectors=["Technology"],
                magnitude=mag,
                description="Test"
            )
            # If it succeeds, magnitude must be valid
            assert -1.0 <= event.magnitude <= 1.0
        except ValidationError:
            pass  # Expected
```

#### 2.2.3 SQL Injection Testing

```python
# tests/security/test_sql_injection.py
SQL_INJECTION_PAYLOADS = [
    "'; DROP TABLE holdings; --",
    "1 OR 1=1",
    "1'; SELECT * FROM client_profiles; --",
    "UNION SELECT * FROM tax_lots",
    "1; UPDATE holdings SET quantity=0; --",
]

class TestSQLInjection:
    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    def test_ticker_field_injection(self, db_session, payload):
        """Verify ticker field is parameterized"""
        # Should not raise, and should return empty (no match)
        results = db_session.query_holdings_by_ticker(payload)
        assert len(results) == 0  # No injection executed

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    def test_portfolio_id_injection(self, db_session, payload):
        """Verify portfolio_id is parameterized"""
        results = db_session.get_holdings(payload)
        assert len(results) == 0
```

### Phase 3: Cryptographic Verification

#### 2.3.1 Encryption Testing

```python
# tests/security/test_encryption.py
class TestEnvelopeEncryption:
    def test_encrypted_data_is_not_plaintext(self):
        """Verify encryption actually encrypts"""
        enc = EnvelopeEncryption(master_key=os.environ["MASTER_ENCRYPTION_KEY"])
        plaintext = "SSN: 123-45-6789"

        envelope = enc.encrypt_field(plaintext)

        # Ciphertext should not contain plaintext
        assert plaintext.encode() not in envelope["ciphertext"]
        assert b"123-45-6789" not in envelope["ciphertext"]

    def test_different_fields_use_different_deks(self):
        """Each field should have unique DEK"""
        enc = EnvelopeEncryption(master_key=os.environ["MASTER_ENCRYPTION_KEY"])

        env1 = enc.encrypt_field("data1")
        env2 = enc.encrypt_field("data2")

        # DEKs should be different
        assert env1["encrypted_dek"] != env2["encrypted_dek"]

    def test_decryption_roundtrip(self):
        """Verify decrypt(encrypt(x)) == x"""
        enc = EnvelopeEncryption(master_key=os.environ["MASTER_ENCRYPTION_KEY"])
        plaintext = "Sensitive PII data"

        envelope = enc.encrypt_field(plaintext)
        decrypted = enc.decrypt_field(envelope)

        assert decrypted == plaintext

    def test_tampering_detection(self):
        """Modified ciphertext should fail decryption"""
        enc = EnvelopeEncryption(master_key=os.environ["MASTER_ENCRYPTION_KEY"])

        envelope = enc.encrypt_field("test data")

        # Tamper with ciphertext
        tampered = bytearray(envelope["ciphertext"])
        tampered[0] ^= 0xFF
        envelope["ciphertext"] = bytes(tampered)

        with pytest.raises(InvalidTag):
            enc.decrypt_field(envelope)
```

#### 2.3.2 Database Encryption Verification

```bash
# Verify SQLCipher encryption
# Attempt to read database without key (should fail)
sqlite3 data/sentinel.db "SELECT * FROM holdings;"
# Expected: "Error: file is not a database"

# Verify with correct key
sqlcipher data/sentinel.db
> PRAGMA key='<correct_key>';
> SELECT COUNT(*) FROM holdings;
# Expected: Returns count
```

### Phase 4: Merkle Chain Integrity

#### 2.4.1 Chain Verification

```python
# tests/security/test_merkle_integrity.py
class TestMerkleChain:
    def test_chain_verification_passes_for_valid_chain(self):
        """Unmodified chain should verify"""
        chain = MerkleChain()
        chain.add_block({"action": "test1"})
        chain.add_block({"action": "test2"})

        assert chain.verify_integrity() == True

    def test_tampered_data_detected(self):
        """Modified block data should fail verification"""
        chain = MerkleChain()
        chain.add_block({"action": "test1"})

        # Tamper with data
        chain.chain[1].data["action"] = "tampered"

        assert chain.verify_integrity() == False

    def test_tampered_hash_detected(self):
        """Modified hash should fail verification"""
        chain = MerkleChain()
        chain.add_block({"action": "test1"})

        # Tamper with hash
        chain.chain[1].hash = "invalid_hash"

        assert chain.verify_integrity() == False

    def test_broken_chain_link_detected(self):
        """Modified previous_hash should fail verification"""
        chain = MerkleChain()
        chain.add_block({"action": "test1"})
        chain.add_block({"action": "test2"})

        # Break chain link
        chain.chain[2].previous_hash = "wrong_hash"

        assert chain.verify_integrity() == False
```

### Phase 5: Session & Sandbox Testing

#### 2.5.1 Docker Sandbox Verification

```python
# tests/security/test_sandbox.py
class TestDockerSandbox:
    def test_sandbox_has_no_network(self):
        """Verify sandboxed sessions cannot access network"""
        sandbox = SandboxedExecution()

        def network_test():
            import socket
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=5)
                return {"network": "accessible"}
            except:
                return {"network": "blocked"}

        result = sandbox.execute_in_sandbox(
            SessionConfig(session_type=SessionType.ANALYST),
            network_test
        )

        assert result["network"] == "blocked"

    def test_sandbox_memory_limit(self):
        """Verify memory limits are enforced"""
        sandbox = SandboxedExecution()

        def memory_hog():
            data = []
            try:
                while True:
                    data.append("x" * 1024 * 1024)  # 1MB chunks
            except MemoryError:
                return {"memory": "limited"}

        result = sandbox.execute_in_sandbox(
            SessionConfig(session_type=SessionType.ANALYST),
            memory_hog
        )

        assert result["memory"] == "limited"
```

---

## 3. Security Report Template

### 3.1 Report Structure

```markdown
# Sentinel Security Assessment Report

**Date**: YYYY-MM-DD
**Assessor**: [Name]
**Scope**: [Components reviewed]
**Classification**: Confidential

## Executive Summary
- Overall Risk Level: [Critical/High/Medium/Low]
- Critical Findings: X
- High Findings: X
- Medium Findings: X
- Low Findings: X

## Findings

### Finding #1: [Title]
- **Severity**: Critical/High/Medium/Low
- **Component**: [Affected component]
- **Description**: [Detailed description]
- **Evidence**: [Code snippet, test output, or screenshot]
- **Impact**: [What could happen if exploited]
- **Remediation**: [How to fix]
- **Status**: Open/In Progress/Resolved

### Finding #2: ...

## Recommendations
1. [Priority recommendation]
2. [Secondary recommendation]
...

## Test Results Summary

| Test Category | Passed | Failed | Skipped |
|---------------|--------|--------|---------|
| RBAC Boundaries | X | X | X |
| Input Validation | X | X | X |
| Encryption | X | X | X |
| Merkle Integrity | X | X | X |
| Sandbox Isolation | X | X | X |
| Dependency Scan | X | X | X |

## Appendix
- Full test output
- Tool configurations
- Remediation timeline
```

### 3.2 Severity Classification

| Severity | Definition | CVSS Range | SLA |
|----------|------------|------------|-----|
| Critical | Immediate exploitation risk, data breach likely | 9.0-10.0 | Fix before deployment |
| High | Exploitable with moderate effort | 7.0-8.9 | Fix within 7 days |
| Medium | Requires specific conditions to exploit | 4.0-6.9 | Fix within 30 days |
| Low | Minimal impact, defense-in-depth concern | 0.1-3.9 | Fix within 90 days |

---

## 4. Automated Review Pipeline

### 4.1 CI/CD Integration

```yaml
# .github/workflows/security-review.yml
name: Security Review

on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install

      - name: Run Bandit
        run: poetry run bandit -r src/ -f json -o bandit.json
        continue-on-error: true

      - name: Run pip-audit
        run: poetry run pip-audit --format json -o pip-audit.json
        continue-on-error: true

      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/python
            p/security-audit

      - name: Run security tests
        run: poetry run pytest tests/security/ -v --junitxml=security-tests.xml

      - name: Upload reports
        uses: actions/upload-artifact@v4
        with:
          name: security-reports
          path: |
            bandit.json
            pip-audit.json
            security-tests.xml
```

### 4.2 Pre-Commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.7
    hooks:
      - id: bandit
        args: ['-c', 'pyproject.toml']
        exclude: tests/

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.1
    hooks:
      - id: gitleaks

  - repo: local
    hooks:
      - id: check-env-files
        name: Check for .env files
        entry: bash -c 'git diff --cached --name-only | grep -E "\.env" && exit 1 || exit 0'
        language: system
        pass_filenames: false
```

---

## 5. Review Schedule

| Review Type | Frequency | Owner |
|-------------|-----------|-------|
| Automated scans | Every PR | CI/CD |
| Dependency audit | Weekly | Security team |
| Manual code review | Monthly | Security team |
| Penetration testing | Quarterly | External vendor |
| Full security audit | Annually | External vendor |

---

## 6. Quick Start Commands

```bash
# Run all security tests
poetry run pytest tests/security/ -v

# Generate security report
poetry run python scripts/generate_security_report.py

# Check dependencies for vulnerabilities
poetry run pip-audit

# Run static analysis
poetry run bandit -r src/

# Verify Merkle chain integrity
poetry run python -m src.main --verify-merkle

# Check for secrets in codebase
gitleaks detect --source .
```

---

## 7. Contacts

| Role | Responsibility |
|------|----------------|
| Security Lead | Overall security review |
| Dev Lead | Remediation implementation |
| Compliance | Regulatory requirements |
| External Auditor | Annual penetration testing |

---

*Document Version: 1.0*
*Last Updated: 2024*

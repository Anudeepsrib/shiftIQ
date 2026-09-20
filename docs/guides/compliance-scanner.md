# Compliance-Oriented Pattern Scanner

ShiftIQ includes a PII/PHI/PCI-oriented pattern scanner. It is not a formal GDPR, HIPAA, SOC2, or PCI-DSS compliance product.

## Pattern Families

- Email addresses
- Phone numbers
- Social Security number-like values
- Credit-card-like numbers with Luhn validation
- Medical record-like IDs
- Patient IDs
- Diagnosis and procedure code-like values
- API keys and token-like values
- JWT-like strings
- Private key headers
- AWS access key IDs

## Redaction

Findings are redacted by default and include:

- File path relative to the scanned project.
- Line and column.
- Finding type, severity, and category.
- A short fingerprint for correlation.
- Redacted context.

Raw matched values are only included when `include_raw=true` and `MIGRATION_SECURITY__EXPOSE_RAW_FINDINGS=true` is intentionally configured.

## Recommended Use

Run this scanner as an early warning check during migration planning. Confirm findings with security and legal reviewers before making compliance statements.

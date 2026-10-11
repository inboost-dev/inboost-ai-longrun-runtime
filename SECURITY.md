# Security Policy

## Reporting Security Issues

InBoost takes security and data privacy seriously. If you discover a security vulnerability or potential data leak in InBoost LongRun or its distribution runtime, please report it promptly.

### Contact
Please send security disclosures to:
**inbound@inboost.pro**

Please do **NOT** open public GitHub issues for undisclosed security vulnerabilities.

### Scope & Architecture Guarantees
- **100% Local Execution:** InBoost LongRun does not connect to external servers or transmit telemetry.
- **Static Linking:** Linux binaries are statically compiled without external libc dynamic loading risks.
- **Evaluation Cryptography:** Evaluation licenses are signed using Ed25519 cryptographic keys.

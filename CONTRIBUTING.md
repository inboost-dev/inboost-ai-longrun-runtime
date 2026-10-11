# Contributing to InBoost LongRun Evaluation Runtime

Thank you for your interest in contributing!

## 1. Distribution Repository Mission
This repository (`inboost-ai-longrun-runtime`) hosts the standalone binary distributions, installers, MCP definitions, and documentation for the evaluation edition of InBoost LongRun. Core engine development occurs within internal InBoost repositories.

## 2. Commit Signing & DCO
All commits to this repository must follow the Developer Certificate of Origin (DCO 1.1) and include a sign-off header:
```bash
git commit -s -m "feat(installer): improve platform detection"
```

## 3. Pull Request Guidelines
- Keep installer scripts (`install.sh`, `install.ps1`) portable and free of third-party dependencies.
- Update `dist/SHA256SUMS` whenever distribution archives are added or refreshed.
- Never commit unverified binaries, internal keys, or proprietary engine source code.

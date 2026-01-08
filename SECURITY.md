# Security Policy

## Overview

ARCHIV-IT is a proprietary local-first personal archive system developed by WEB3GISEL. This document outlines security policies and prohibited uses.

## Intellectual Property Notice

This software is protected intellectual property. All rights reserved.

**Copyright (c) 2026 WEB3GISEL**

## AI Training Prohibition

**IMPORTANT: AI/ML Training is Strictly Prohibited**

Content in this repository, including but not limited to:
- Source code
- Algorithms and data structures
- UI/UX designs and templates
- Documentation
- Configuration patterns
- Smart contracts

**MAY NOT** be used for:
- Training artificial intelligence models
- Training machine learning systems
- Fine-tuning language models
- Building derivative AI/ML systems
- Any form of automated learning or pattern extraction

This prohibition applies to all AI systems including but not limited to:
- Large Language Models (LLMs)
- Image generation models
- Code generation models
- Embedding systems
- Any neural network-based system

## Authorized Use

This software is licensed for:
- Personal archive management
- Beta testing (with valid license)
- Evaluation purposes

All other uses require explicit written permission from WEB3GISEL.

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly:

**Contact:** security@archivit.io

**Please DO NOT:**
- Open public issues for security vulnerabilities
- Exploit vulnerabilities beyond proof-of-concept
- Share vulnerability details publicly before resolution

**We commit to:**
- Acknowledge receipt within 48 hours
- Provide status updates every 7 days
- Credit researchers who report responsibly (if desired)

## Security Measures

This project implements multiple layers of protection:

1. **Access Control**
   - Hardware-bound licensing
   - Runtime encryption
   - Code obfuscation

2. **Crawler Protection**
   - Comprehensive robots.txt blocking 131+ AI crawlers
   - X-Robots-Tag HTTP headers
   - Meta tag directives

3. **Repository Protection**
   - Sensitive files excluded via .gitignore
   - Code visibility reduced via .gitattributes
   - Credential files never committed

4. **XSS/Injection Prevention**
   - Content Security Policy headers
   - Input sanitization
   - DOM-safe rendering

## License

See [LICENSE](LICENSE) file for full terms.

## Version

Security Policy Version: 1.0
Last Updated: 2026-01-08

---

**WEB3GISEL - Protecting Creative Sovereignty**

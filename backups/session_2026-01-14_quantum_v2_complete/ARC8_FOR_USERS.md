# ARC-8: What It Is and What It Does

## The Honest Summary

ARC-8 is a **local-first, user-sovereign data platform**. Your data lives on YOUR device. You own your identity. We don't track you.

### What ARC-8 IS:
- A desktop/mobile app that runs on YOUR machine
- A system where YOU control your cryptographic identity (seed)
- A tool that CAN connect to blockchains and IPFS (optional)
- Anti-extraction by design - we don't harvest your data

### What ARC-8 is NOT:
- NOT a blockchain (we connect to them, we're not one)
- NOT a decentralized protocol (we're an application)
- NOT peer-to-peer (no node network yet)
- NOT requiring cryptocurrency to use

---

## Core Features (Implemented)

### 1. Sovereign Identity (Seed System)
Your identity is a cryptographic seed that lives only on your device. From this seed, we derive:
- Your unique identifier
- Your signing keys
- Your encryption keys

**You own it. We can't access it. If you lose it, it's gone.**

### 2. Source Verification (DOC-8)
Upload documents, videos, images. The system:
- Records cryptographic hashes (proof the file existed)
- Extracts metadata (dates, authors, sources)
- Creates provenance chains (who said what, when)

### 3. Creative Tools (IT-R8)
Spatial organization for ideas:
- Drag and connect concepts
- Tag and categorize
- Build knowledge graphs

### 4. Export Everything
Your data is yours. Export anytime in standard formats:
- JSON for structured data
- ZIP archives for files
- Markdown for documents

---

## Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Seed System | Working | Local cryptographic identity |
| DOC-8 Archive | Working | Document ingestion and hashing |
| IT-R8 Creative | In Progress | UI complete, backend connecting |
| Blockchain Connection | Designed | Specs complete, implementation pending |
| Mobile App | Planned | PWA specification complete |

---

## Getting Started

1. Download/clone the repository
2. Run: `./install.sh`
3. Start: `./start_server.sh`
4. Open: `http://localhost:5001`

---

## Questions?

- Technical issues: Open a GitHub issue
- Feature requests: Use the feedback form in-app
- Security concerns: See SECURITY.md

---

*ARC-8 is built by artists, for creators who want to own their work.*

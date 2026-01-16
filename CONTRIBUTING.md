# Contributing to ARCHIV-IT

## Code of Conduct

Be respectful. No harassment. Focus on technical merit.

## How to Contribute

### Reporting Bugs

1. Check existing issues first
2. Create issue with:
   - Clear title
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment (OS, Node version, browser)

### Suggesting Features

1. Open an issue with `[Feature]` prefix
2. Describe the use case
3. Explain why it fits ARC-8's mission

### Pull Requests

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes
4. Run tests: `npm test`
5. Commit with clear message
6. Push and create PR

### Commit Message Format

```
<type>: <description>

<body>

Co-Authored-By: Your Name <email>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

### Code Style

- ES modules (`import`/`export`)
- No semicolons (Prettier default)
- 2-space indentation
- Descriptive variable names
- Comments for non-obvious logic

### Testing

- Write tests for new features
- Ensure existing tests pass
- Test gaming resistance for access control changes

## Architecture

```
scripts/interface/static/js/core/   # Core modules
  - pi_quadratic_seed.js            # Identity
  - quantum_equilibrium.js          # Access control
  - arweave_permanence.js           # Storage
  - pqs_quantum.js                  # PQC integration

docs/                               # Specifications
templates/                          # HTML templates
```

## Key Principles

1. **User sovereignty**: User owns their data
2. **No tracking**: No analytics without consent
3. **Local-first**: Works offline
4. **Factual documentation**: No marketing speak

## Questions

Open an issue with `[Question]` prefix.

## License

AGPL-3.0. Contributions must be compatible.

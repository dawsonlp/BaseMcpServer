# Architectural Decision Records (ADRs)

This directory contains Architectural Decision Records that document significant architectural decisions made during the development of BaseMcpServer.

## Available ADRs

### [ADR-003: Standardize Local Server Installs on uv](ADR-003-uv-standardization.md) — **Accepted** (May 2026)
mcp-manager 1.1.0 replaced the previous pipx/virtualenv internals with a single `uv venv` + `uv pip install` path. Removed the `--no-pipx` flag and the legacy source-copy branch.

### [ADR-002: Default to Pipx Installation Method](ADR-002-pipx-default-installation.md) — **Superseded** by ADR-003
Historical context: in mcp-manager 0.3.0 the default install changed to pipx-style isolated installs. Superseded once the project standardized on uv.

### [Design Decisions](design_decisions.md)
Historical record of important design and architectural decisions made during early development.

## About ADRs

Architectural Decision Records (ADRs) are short text documents that capture an important architectural decision made along with its context and consequences. They help:

- Document the reasoning behind architectural choices
- Provide context for future developers
- Track the evolution of the system architecture
- Enable informed decision-making about changes

## Format

ADRs typically follow a standard format:

1. **Title**: Brief description of the decision
2. **Context**: The circumstances that led to the decision
3. **Decision**: What was decided
4. **Status**: Current status (proposed, accepted, deprecated, superseded)
5. **Consequences**: What becomes easier or more difficult

## Related Resources

- [Developer Documentation](../developer/) - Technical implementation details
- [Project Overview](../../readme.md) - Current system architecture
- [Design Patterns Guide](../developer/BUILD_A_NEW_MCP.md) - Implementation guidelines

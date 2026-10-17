# Project charter

## Goal

Build an evidence-backed knowledge base and, incrementally, a desktop
application capable of safely controlling Makerspace Næstved's lasers. The
first hardware target is the JPT 100 W E2/M7 MOPA fiber laser.

## Phase 0 success criteria

1. Public and private repositories are independently cloneable and validated.
2. Raw evidence is immutable, hashed, and kept in the private repository.
3. Every public technical claim is traceable to a private artifact ID and
   SHA-256 digest without exposing private locators.
4. Collection and analysis can be repeated using committed tools and tests.
5. No command is sent to laser hardware during Phase 0.

## Clean-room boundary

The project studies observable configuration formats and hardware behavior for
interoperability. It does not bypass LightBurn licensing, copy proprietary
source code or UI assets, or redistribute third-party material without a clear
right to do so.

## Working practice

Plans, decisions, scripts, tests, reports, and collected evidence are committed
and pushed in small, meaningful units. Commit messages explain intent. Force
pushes and history rewriting are not part of the workflow.

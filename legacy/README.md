# Legacy Code

This directory contains the original monolithic implementation of MiraiDroid
(`miraidroid_legacy.py`, v5.0.0) that was kept here for historical reference.

**This file is NOT used at runtime.** The active codebase is in `src/`, `services/`,
and `handlers/`, and the entry point is `main.py`.

## Why keep it?

- Reference for the evolution of the architecture
- Rollback target if the modular version breaks catastrophically
- Useful for understanding the original intent of features

## Do not edit

All new development happens in the modular structure. Bug fixes and features
go to `src/`, `services/`, or `handlers/` — never here.

If you need to understand how a feature was originally implemented, this is
where to look.
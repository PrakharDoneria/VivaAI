## 2026-04-29

- feat(config): add startup environment validation, runtime mode controls, and configurable AI/provider settings
- fix(core): repair broken config module syntax and standardize server boot flow
- feat(security): add response security headers and in-memory rate limiting for interview creation and AI endpoints
- fix(api): harden JSON parsing and input handling for interview and AI routes
- fix(realtime): add lock-protected room membership handling for Socket.IO signaling to reduce race conditions
- chore(dx): add Makefile targets for install/dev/test/lint and pin Node version via `.nvmrc`
- docs(readme): rewrite setup and environment variable documentation with contributor workflow guidance
- docs(env): sync `.env.example` with actual configuration keys

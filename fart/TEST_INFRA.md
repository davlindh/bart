# E2E Test Infra: Antigravity Platform

## Test Philosophy
- Opaque-box & unit/integration, requirement-driven per R1-R5.
- Zero-mock local model inference testing using real mathematical transformer engines, real BPE tokenization, real sampling, and real checkpoint loader paths.
- SQLite disk persistence validation across simulated and true process boundaries.
- AST security & builtins whitelisting validation without false positives.

## Feature Inventory & Test Mapping
| # | Feature | Source | Tier 1 (Features) | Tier 2 (Boundaries) | Tier 3 (Cross-Pipeline) | Tier 4 (Workloads) | Tier 5 (Adversarial) |
|---|---------|--------|:-----------------:|:-------------------:|:-----------------------:|:------------------:|:--------------------:|
| F1 | Sandbox Engine (Local/E2B) | R1 | 5+ | 5+ | ✓ | ✓ | ✓ |
| F2 | AST Security & Builtins | R1, R3 | 5+ | 5+ | ✓ | ✓ | ✓ |
| F3 | MCP Core Lifecycle & Execution | R2 | 5+ | 5+ | ✓ | ✓ | ✓ |
| F4 | Scheduled Service Worker Daemon | R4 | 5+ | 5+ | ✓ | ✓ | ✓ |
| F5 | Disk Persistence & SQLite Engine | R1 | 5+ | 5+ | ✓ | ✓ | ✓ |
| F6 | Multi-Branch Snapshot DAG | R1 | 5+ | 5+ | ✓ | ✓ | ✓ |
| F7 | Real Local Model Runner & Nemotron | R2 | 5+ | 5+ | ✓ | ✓ | ✓ |
| F8 | AST Security ML Whitelist | R3 | 5+ | 5+ | ✓ | ✓ | ✓ |
| F9 | Extended MCP Tools (6 tools) | R4 | 5+ | 5+ | ✓ | ✓ | ✓ |
| F10 | Progressive Disclosure Skills Suite | R4 | 5+ | 5+ | ✓ | ✓ | ✓ |
| F11 | End-to-End Demo Execution | R5 | ✓ | ✓ | ✓ | ✓ | ✓ |

## Test Suite Layout
```
tests/
├── conftest.py
├── tier1_features/
│   ├── test_sandbox_features.py
│   ├── test_repl_features.py
│   ├── test_mcp_features.py
│   ├── test_plugin_features.py
│   ├── test_scheduler_features.py
│   ├── test_persistence_features.py
│   ├── test_local_model_features.py
│   ├── test_mcp_extended_tools.py
│   └── test_extended_plugin_skills.py
├── tier2_boundaries/
│   ├── test_ast_security_boundaries.py
│   ├── test_sandbox_timeouts_and_errors.py
│   ├── test_scheduler_cron_edge_cases.py
│   ├── test_mcp_protocol_boundaries.py
│   ├── test_persistence_boundaries.py
│   ├── test_local_model_boundaries.py
│   └── test_mcp_extended_boundaries.py
├── tier3_cross_feature/
│   ├── test_mcp_sandbox_pipeline.py
│   ├── test_scheduler_sandbox_pipeline.py
│   ├── test_fallback_degradation_pipeline.py
│   ├── test_persistence_sandbox_pipeline.py
│   ├── test_mcp_model_sandbox_pipeline.py
│   └── test_scheduler_persistence_pipeline.py
├── tier4_workloads/
│   ├── test_agent_multi_turn_analysis.py
│   ├── test_scheduled_health_monitoring.py
│   ├── test_artifact_data_pipeline.py
│   ├── test_multi_turn_agent_with_local_model.py
│   ├── test_snapshot_branching_persistence.py
│   └── test_model_whitelisting_in_sandbox.py
└── tier5_adversarial/
    ├── test_adversarial_security.py
    └── test_adversarial_persistence_and_models.py
```

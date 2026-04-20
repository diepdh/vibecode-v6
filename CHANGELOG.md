# Changelog

All notable changes to Vibecode will be documented in this file.

## [6.0.0] - 2024-04-20

### 🎉 Initial Release - Complete Rewrite

#### Major Changes from v5
- **Split workflow into 2 phases:** Planning (manual) vs Execution (automated)
- **Multi-agent planning:** Brain → Claude review → Gemini review → Brain synthesize
- **Automated execution loop:** Orchestrator auto-loops Coder ↔ Reviewer
- **VS Code Extension:** UI panel với buttons thay vì manual prompting
- **File-based architecture:** `.aiwf/` directory structure
- **CLI integration:** Claude Code CLI + Gemini CLI (subscription-based)

#### Added - Phase A: Planning
- Brain Planner prompt template
- Claude Plan Reviewer prompt template
- Gemini Plan Reviewer prompt template
- Brain Synthesizer prompt template
- CLI wrappers cho plan generation và review
- Templates: goal.md, plan.md, feedback.md, blueprint.md

#### Added - Phase B: Execution
- Gemini Coder prompt template
- Brain Task Reviewer prompt template
- Blueprint parser (Markdown → JSON)
- Orchestrator engine với state machine
- Automated loop logic với retry mechanism
- Machine checks integration
- Git diff integration
- Logging system

#### Added - VS Code Extension
- Control Panel webview
- 10 commands cho Phase A + Phase B
- Python bridge để spawn processes
- Output channel integration
- Auto-open generated files

#### Added - Templates
- goal.md template
- plan_template.md
- tasks_template.json
- state_template.json

#### Added - Documentation
- SETUP.md - Installation guide
- USER_GUIDE.md - Step-by-step usage
- ARCHITECTURE.md - System architecture
- README.md - Project overview
- IMPLEMENTATION_SUMMARY.md - Technical details

### Technical Details

**Python Backend:**
- `prompts.py` - 450 lines - 6 role prompts
- `cli_wrappers.py` - 350 lines - CLI integration
- `build_tasks_from_blueprint.py` - 300 lines - Parser
- `orchestrator.py` - 400 lines - Execution engine

**VS Code Extension:**
- `extension.ts` - 250 lines - Main entry point
- `python_bridge.ts` - 150 lines - Python integration
- `webview.ts` - 200 lines - UI panel

**Total:** ~2,100 lines of production code

### Features

✅ Multi-agent planning với feedback từ Claude + Gemini
✅ Automated execution loop không cần manual handoff
✅ Quality gates với DoD + machine checks
✅ Safety guardrails (allowed files, retry limits)
✅ VS Code integration với UI buttons
✅ File-based artifacts (debuggable, inspectable)
✅ CLI support cho automation

### Known Limitations

- CLI paths currently hardcoded
- Sequential task execution only
- No automatic git commits
- Python script path needs configuration

### Breaking Changes from v5

- Complete file structure change (`.vibecode/` → `.aiwf/`)
- New workflow (2-phase vs single-phase)
- Different prompt structure
- VS Code extension required for UI

---

## [5.0.0] - Previous Version

Legacy v5 workflow với Brain-Coder-Reviewer manual orchestration.

See v5 documentation for details.

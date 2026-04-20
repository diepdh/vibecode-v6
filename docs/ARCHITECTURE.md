# Vibecode v6 - Architecture Documentation

## System Overview

Vibecode v6 là một AI-orchestrated coding workflow gồm 2 phases:

- **Phase A (Planning):** Human-supervised, multi-agent review
- **Phase B (Execution):** Automated loop with quality gates

---

## Components

### 1. Prompts System (`prompts.py`)

Chứa 6 prompt templates cho các roles:

| Role | Phase | Purpose |
|------|-------|---------|
| Brain Planner | A.1 | Tạo plan.md từ goal.md |
| Claude Reviewer | A.2 | Review plan → feedback_1.md |
| Gemini Reviewer | A.3 | Review plan → feedback_2.md |
| Brain Synthesizer | A.5 | Tổng hợp → blueprint.md |
| Gemini Coder | B | Implement task |
| Brain Reviewer | B | Review task output |

**Design Principles:**
- Structured output format (Markdown/JSON)
- Clear role boundaries
- Explicit Definition of Done
- Safety guardrails

### 2. CLI Wrappers (`cli_wrappers.py`)

Wrapper cho Claude Code CLI và Gemini CLI.

**Key Functions:**

```python
call_claude_cli(prompt, context_files, output_file, timeout)
call_gemini_cli(prompt, context_files, output_file, timeout)
run_machine_checks(checks, cwd)
get_git_diff(since_ref, file_pattern)
```

**High-level wrappers cho Phase A:**

```python
generate_plan(goal_file, output_file)
review_plan_claude(plan_file, output_file)
review_plan_gemini(plan_file, output_file)
synthesize_blueprint(plan, feedback1, feedback2, output)
```

**Design Decisions:**
- CLI-based (không dùng API directly) → support subscription auth
- File-based I/O → debuggable, inspectable
- Timeout protection → prevent hanging

### 3. Blueprint Parser (`build_tasks_from_blueprint.py`)

Parse blueprint.md (Markdown) → tasks.json (JSON).

**Parsing Logic:**

```python
def parse_blueprint(blueprint_file):
    # Extract sections using regex
    final_goal = extract_section("Final Goal")
    tasks = extract_tasks()  # Parse ### TXXX: Title blocks
    
    for task in tasks:
        # Extract:
        - Objective
        - Allowed Files (glob patterns)
        - Definition of Done (checklist)
        - Machine Checks (commands)
        - Dependencies
        - Estimated Time
    
    return tasks_json_structure
```

**Output Format:**

```json
{
  "final_goal": "...",
  "machine_checks": ["pnpm test", "pnpm lint"],
  "tasks": [
    {
      "id": "T001",
      "title": "...",
      "description": "...",
      "allowed_files": ["src/**/*.tsx"],
      "definition_of_done": ["Criterion 1", "..."],
      "checks": ["pnpm test auth"],
      "dependencies": [],
      "estimated_time": "30 minutes"
    }
  ],
  "guardrails": [...],
  "escalation_conditions": [...]
}
```

### 4. Orchestrator (`orchestrator.py`)

Core execution engine - điều phối automation loop.

**State Machine:**

```
planning_complete → running → (completed | blocked)
```

**Main Loop (`loop()`):**

```python
while current_task < total_tasks:
    # 1. Get current task
    task = get_current_task()
    
    # 2. Call Gemini Coder
    coder_report = call_coder(task)
    if coder_report.status == BLOCKED:
        state = "blocked"; break
    
    # 3. Run machine checks
    checks_output = run_checks(task.checks)
    
    # 4. Get git diff
    diff = get_git_diff()
    
    # 5. Call Brain Reviewer
    review = call_reviewer(task, coder_report, diff, checks_output)
    
    # 6. Process decision
    if review.decision == PASS:
        mark_task_complete()
        current_task_index++
    elif review.decision == REVISE:
        current_retry++
        if current_retry > max_retries:
            state = "blocked"; break
    else:  # BLOCK
        state = "blocked"; break
```

**Retry Logic:**
- Max 2 retries per task
- Reviewer feedback được pass vào Coder ở lần retry
- Exceed max → escalate to BLOCKED

**Logging:**
- Console output (realtime)
- File logs (`.aiwf/run/logs/orchestrator.log`)

### 5. VS Code Extension (TypeScript)

**Structure:**

```
extension/
├── src/
│   ├── extension.ts       # Entry point, register commands
│   ├── webview.ts         # UI panel
│   └── python_bridge.ts   # Spawn Python processes
├── package.json           # Extension manifest
└── tsconfig.json
```

**Commands:**

| Command | Action |
|---------|--------|
| vibecode.generatePlan | Call `generate_plan()` |
| vibecode.getClaudeFeedback | Call `review_plan_claude()` |
| vibecode.getGeminiFeedback | Call `review_plan_gemini()` |
| vibecode.synthesizeBlueprint | Call `synthesize_blueprint()` |
| vibecode.initTasks | Run `build_tasks_from_blueprint.py` |
| vibecode.startLoop | Run `orchestrator.py loop` |
| vibecode.showStatus | Run `orchestrator.py status` |

**UI Panel:**

```
┌────────────────────────────────────┐
│ Vibecode v6 Control Panel          │
├────────────────────────────────────┤
│ PHASE A: PLANNING                  │
│ [ Generate Plan ]                  │
│ [ Get Claude Feedback ]            │
│ [ Get Gemini Feedback ]            │
│ [ Synthesize Blueprint ]           │
├────────────────────────────────────┤
│ PHASE B: EXECUTION                 │
│ [ Init Tasks ]                     │
│ [ Start Loop ] [ Stop ]            │
│ [ Show Status ]                    │
├────────────────────────────────────┤
│ STATUS:                            │
│ ✅ Planning Complete               │
│ 🔄 Running: T003/T010             │
│ 📊 Completed: 2 tasks              │
└────────────────────────────────────┘
```

---

## Data Flow

### Phase A: Planning

```
User writes goal.md
    ↓
[Button: Generate Plan]
    ↓
VS Code Extension → python_bridge.spawn('generate_plan')
    ↓
cli_wrappers.call_claude_cli(BRAIN_PLANNER_PROMPT + goal.md)
    ↓
plan.md saved to .aiwf/input/
    ↓
[Button: Get Claude Feedback]
    ↓
cli_wrappers.call_claude_cli(CLAUDE_REVIEWER_PROMPT + plan.md)
    ↓
feedback_1.md saved
    ↓
[Button: Get Gemini Feedback]
    ↓
cli_wrappers.call_gemini_cli(GEMINI_REVIEWER_PROMPT + plan.md)
    ↓
feedback_2.md saved
    ↓
User reviews feedbacks
    ↓
[Button: Synthesize Blueprint]
    ↓
cli_wrappers.call_claude_cli(BRAIN_SYNTHESIZER_PROMPT + plan + feedbacks)
    ↓
blueprint.md saved
```

### Phase B: Execution

```
[Button: Init Tasks]
    ↓
build_tasks_from_blueprint.py parses blueprint.md
    ↓
tasks.json + state.json created in .aiwf/run/
    ↓
[Button: Start Loop]
    ↓
orchestrator.py loop():
    ┌─────────────────────────────────────┐
    │ While current_task < total_tasks:   │
    │                                     │
    │ 1. Load task from tasks.json       │
    │    ↓                                │
    │ 2. Build Coder context:             │
    │    - Task details                   │
    │    - Blueprint                      │
    │    - Previous review (if retry)     │
    │    ↓                                │
    │ 3. Call Gemini Coder CLI            │
    │    → coder_report.txt               │
    │    ↓                                │
    │ 4. Run machine checks               │
    │    → test_output.txt                │
    │    ↓                                │
    │ 5. Get git diff                     │
    │    ↓                                │
    │ 6. Build Reviewer context:          │
    │    - Task DoD                       │
    │    - Coder report                   │
    │    - Git diff                       │
    │    - Checks output                  │
    │    ↓                                │
    │ 7. Call Brain Reviewer CLI          │
    │    → review.json                    │
    │    ↓                                │
    │ 8. Parse decision:                  │
    │    ├─ PASS → next task              │
    │    ├─ REVISE → retry++              │
    │    └─ BLOCK → stop                  │
    └─────────────────────────────────────┘
        ↓
    Final status: completed | blocked
```

---

## Scalability & Performance

### Bottlenecks

1. **CLI call latency:** Each AI call ~10-30s
2. **Sequential processing:** 1 task at a time
3. **Retry overhead:** Max 2 retries × task count

### Optimizations

1. **Parallel checks:** Machine checks run concurrently
2. **Streaming logs:** Realtime feedback in UI
3. **Caching:** Git diff cached per iteration
4. **Early termination:** BLOCK stops immediately

### Limits

- **Max iterations:** 100 (configurable safety limit)
- **Max retries:** 2 per task
- **Timeout:** 300s per CLI call

---

## Security & Safety

### Guardrails

1. **Allowed Files:** Coder chỉ được sửa files trong pattern
2. **Max Retries:** Prevent infinite loops
3. **Escalation:** Auto-block nếu vượt boundaries
4. **Diff Size Check:** (planned) Block nếu diff quá lớn

### Sensitive Data

- CLI credentials: Managed by Claude/Gemini CLI (oauth tokens)
- No API keys in code
- Logs don't contain secrets

---

## Extensibility

### Adding New Roles

1. Add prompt to `prompts.py`
2. Add wrapper function to `cli_wrappers.py`
3. Update orchestrator loop logic
4. Add UI button in extension

### Custom Machine Checks

Edit blueprint.md:
```markdown
**Machine Checks:**
- `pnpm test`
- `pnpm lint`
- `./scripts/custom_check.sh`  ← Add custom script
```

### Multi-Model Support

Current: Claude (Brain) + Gemini (Coder)

Future: Configurable model assignment per role.

---

## Future Enhancements

### v6.1 Roadmap

- [ ] Parallel task execution (for independent tasks)
- [ ] Interactive pause/resume in UI
- [ ] Git auto-commit per task
- [ ] Metrics dashboard (success rate, avg retry count)
- [ ] Custom prompt override per project

### v7.0 Vision

- [ ] Multi-project orchestration
- [ ] Web dashboard (không chỉ VS Code)
- [ ] Human-in-loop approval gates (config per task)
- [ ] Integration với CI/CD pipelines

---

## Debugging Tips

### Enable Verbose Logging

Edit `orchestrator.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Inspect State

```bash
cat .aiwf/run/state.json | jq .
```

### Replay Task

```bash
# Reset to specific task
vim .aiwf/run/state.json
# Set current_task_index: 3

python orchestrator.py run  # Run task 3 only
```

### Mock CLI Calls (for testing)

Edit `cli_wrappers.py`:
```python
def call_claude_cli(...):
    return "MOCK RESPONSE"  # Skip actual API call
```

---

## Contributing

### Code Structure

```
vibecode-v6/
├── python/          # Backend logic
│   ├── prompts.py          # Prompt templates
│   ├── cli_wrappers.py     # CLI integration
│   ├── build_tasks.py      # Parser
│   └── orchestrator.py     # Main engine
├── extension/       # VS Code UI
├── templates/       # File templates
└── docs/           # Documentation
```

### Pull Request Guidelines

1. Add tests for new features
2. Update prompts.py if changing role behavior
3. Document in USER_GUIDE.md
4. Follow existing code style

---

## License

[Your license here]

---

**Vibecode v6** - "Orchestrated AI Coding, Evolved" 🚀

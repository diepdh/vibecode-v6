# Vibecode v6 - User Guide

## Workflow Overview

```
Phase A: Planning (Human-in-the-loop)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Write goal.md
2. Brain generates plan.md
3. Claude reviews → feedback_1.md
4. Gemini reviews → feedback_2.md  
5. Brain synthesizes → blueprint.md
   ↓
Phase B: Execution (Automated)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
6. Parse blueprint → tasks.json
7. Orchestrator auto-loop:
   Coder → Checks → Reviewer → Decision
   Until all tasks PASS or BLOCKED
```

---

## Phase A: Planning

### Step 1: Write Goal

Tạo file `.aiwf/input/goal.md`:

```markdown
# Goal: Add User Profile Page

## Objective
Create a user profile page where users can view and edit their information.

## Scope
### In Scope:
- Profile view page (name, email, avatar)
- Edit profile form
- Avatar upload

### Out of Scope:
- Password change (separate feature)
- Account deletion

## Constraints
- Must use existing auth system
- Must be responsive (mobile-first)

## Success Criteria
- [ ] Users can view their profile
- [ ] Users can edit name and email
- [ ] Users can upload avatar
- [ ] All changes persist to database
```

### Step 2: Generate Plan

**VS Code:** Command Palette → "Vibecode: Generate Plan"

**CLI:**
```bash
cd vibecode-v6/python
python -c "from cli_wrappers import generate_plan; generate_plan('.aiwf/input/goal.md', '.aiwf/input/plan.md')"
```

**Kết quả:** File `.aiwf/input/plan.md` được tạo

### Step 3 & 4: Get Feedback

**VS Code:** 
- "Vibecode: Get Claude Feedback"
- "Vibecode: Get Gemini Feedback"

**CLI:**
```bash
# Claude review
python -c "from cli_wrappers import review_plan_claude; review_plan_claude('.aiwf/input/plan.md', '.aiwf/input/feedback_1.md')"

# Gemini review
python -c "from cli_wrappers import review_plan_gemini; review_plan_gemini('.aiwf/input/plan.md', '.aiwf/input/feedback_2.md')"
```

**Kết quả:** 
- `.aiwf/input/feedback_1.md`
- `.aiwf/input/feedback_2.md`

### Step 5: Review Feedbacks & Synthesize

**Manual Step:** Đọc 2 feedbacks, quyết định accept/reject các suggestions.

**Synthesize Blueprint:**

**VS Code:** "Vibecode: Synthesize Blueprint"

**CLI:**
```bash
python -c "from cli_wrappers import synthesize_blueprint; synthesize_blueprint('.aiwf/input/plan.md', '.aiwf/input/feedback_1.md', '.aiwf/input/feedback_2.md', '.aiwf/input/blueprint.md')"
```

**Kết quả:** `.aiwf/input/blueprint.md` - Bản chốt cuối cùng

---

## Phase B: Execution

### Step 6: Initialize Tasks

Parse blueprint thành tasks.json:

**VS Code:** "Vibecode: Init Tasks"

**CLI:**
```bash
cd vibecode-v6/python
python build_tasks_from_blueprint.py .aiwf/input/blueprint.md .aiwf/run/
```

**Kết quả:**
- `.aiwf/run/tasks.json`
- `.aiwf/run/state.json`

### Step 7: Run Execution Loop

**VS Code:** "Vibecode: Start Execution Loop"

**CLI:**
```bash
python orchestrator.py loop
```

**Orchestrator sẽ:**
1. Lấy task hiện tại từ tasks.json
2. Gọi Gemini Coder để implement
3. Chạy machine checks (test/lint/build)
4. Lấy git diff
5. Gọi Brain Reviewer để đánh giá
6. Nếu PASS → next task
7. Nếu REVISE → retry (max 2 times)
8. Nếu BLOCK → dừng, chờ human

Loop chạy tự động cho đến khi:
- ✅ Tất cả tasks PASS → status: "completed"
- 🚧 Gặp BLOCK → status: "blocked"
- ⚠️ Max retries exceeded → status: "blocked"

---

## Monitoring & Control

### Check Status

**VS Code:** "Vibecode: Show Status"

**CLI:**
```bash
python orchestrator.py status
```

**Output:**
```
VIBECODE v6 - ORCHESTRATOR STATUS
==================================

Status: RUNNING
Current Task: 3/10
Completed: 2
Current Retry: 1/2

Completed Tasks:
  ✅ T001 - 2024-04-20T10:30:00
  ✅ T002 - 2024-04-20T11:00:00

Current Task:
  ID: T003
  Title: Create profile edit form
  DoD: 5 criteria
```

### Handle Blockers

Khi status = "blocked":

1. **Đọc lý do:**
```bash
python orchestrator.py status
# → Hiển thị blocked_task.reason
```

2. **Resolve issue manually:**
- Sửa code
- Clarify requirement
- Update blueprint nếu cần

3. **Reset và continue:**
```bash
# Option A: Reset completely
python orchestrator.py reset

# Option B: Fix state.json manually
vim .aiwf/run/state.json
# Set "status": "running"
# Set "current_retry": 0 nếu muốn retry lại

python orchestrator.py loop
```

---

## Advanced Usage

### Run Single Task Iteration

Thay vì loop, chạy từng iteration một:

```bash
python orchestrator.py run
```

### Modify Task Mid-Flight

1. Stop orchestrator (Ctrl+C)
2. Edit `.aiwf/run/tasks.json`
3. Restart loop

### Add Custom Machine Checks

Edit blueprint.md → rebuild tasks:

```bash
python build_tasks_from_blueprint.py .aiwf/input/blueprint.md .aiwf/run/
```

---

## Tips & Best Practices

### ✅ DO:
- Write specific, measurable Definition of Done
- Keep tasks small (15-45 minutes each)
- Use glob patterns for allowed_files
- Review feedbacks carefully before synthesis
- Monitor logs in `.aiwf/run/logs/`

### ❌ DON'T:
- Create tasks > 1 hour
- Use vague DoD ("make it work")
- Skip feedback review phase
- Ignore BLOCKED signals
- Edit state.json while orchestrator running

---

## File Structure Reference

```
project-root/
├── .aiwf/
│   ├── input/                    # Phase A outputs
│   │   ├── goal.md
│   │   ├── plan.md
│   │   ├── feedback_1.md
│   │   ├── feedback_2.md
│   │   └── blueprint.md
│   └── run/                      # Phase B outputs
│       ├── tasks.json
│       ├── state.json
│       ├── coder_report.txt
│       ├── review.json
│       ├── test_output.txt
│       └── logs/
│           ├── orchestrator.log
│           ├── coder.log
│           └── reviewer.log
```

---

## Troubleshooting

### Loop keeps REVISING same task

**Cause:** DoD không clear hoặc code có fundamental issue

**Fix:**
1. Stop loop
2. Read `.aiwf/run/review.json` để xem reviewer feedback
3. Sửa code manually hoặc update DoD
4. Resume loop

### Coder creates files outside allowed_files

**Cause:** allowed_files quá restrictive hoặc task scope unclear

**Fix:**
1. Reviewer sẽ catch này và BLOCK
2. Update blueprint.md: mở rộng allowed_files
3. Rebuild tasks: `python build_tasks_from_blueprint.py`
4. Reset và resume

### Machine checks fail

**Cause:** Coder break existing tests

**Fix:**
1. Check `.aiwf/run/test_output.txt`
2. Sửa code để pass tests
3. Resume loop

---

## Next Steps

- Read [ARCHITECTURE.md](./ARCHITECTURE.md) để hiểu cách hoạt động
- Customize prompts trong `python/prompts.py` nếu cần
- Contribute improvements!

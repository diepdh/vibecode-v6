"""
Vibecode v6 - Blueprint Parser
Parse blueprint.md thành tasks.json để orchestrator sử dụng
"""

import re
import json
from typing import Dict, List, Any, Optional


def parse_blueprint(blueprint_file: str) -> Dict[str, Any]:
    """
    Parse blueprint.md thành tasks.json structure
    
    Args:
        blueprint_file: Path to blueprint.md
    
    Returns:
        Dict với structure của tasks.json
    """
    with open(blueprint_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse các sections
    final_goal = extract_section(content, "Final Goal")
    machine_checks = extract_machine_checks(content)
    tasks = extract_tasks(content)
    guardrails = extract_section(content, "Global Guardrails")
    escalation_conditions = extract_section(content, "Escalation Conditions")
    
    return {
        "final_goal": final_goal,
        "machine_checks": machine_checks,
        "tasks": tasks,
        "guardrails": guardrails.split('\n') if guardrails else [],
        "escalation_conditions": escalation_conditions.split('\n') if escalation_conditions else [],
        "metadata": {
            "total_tasks": len(tasks),
            "source": blueprint_file
        }
    }


def extract_section(content: str, section_name: str) -> str:
    """
    Extract nội dung của một section trong markdown
    
    Args:
        content: Full markdown content
        section_name: Tên section (e.g., "Final Goal")
    
    Returns:
        Section content (text)
    """
    # Pattern: ## Section Name\n[content]
    pattern = rf'##\s+{re.escape(section_name)}\s*\n(.*?)(?=\n##|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    return ""


def extract_machine_checks(content: str) -> List[str]:
    """
    Extract machine checks từ blueprint
    
    Returns:
        List of check commands
    """
    # Tìm section "Global Guardrails" hoặc task-specific checks
    # Giả sử format: `command` trong code blocks
    
    pattern = r'`([^`]+)`'
    matches = re.findall(pattern, content)
    
    # Filter ra commands (thường có npm/pnpm/yarn)
    checks = []
    for match in matches:
        if any(keyword in match for keyword in ['pnpm', 'npm', 'yarn', 'test', 'lint', 'build']):
            if match not in checks:
                checks.append(match)
    
    return checks


def extract_tasks(content: str) -> List[Dict[str, Any]]:
    """
    Extract tasks từ Task Breakdown section
    
    Returns:
        List of task dicts
    """
    # Pattern: ### TXXX: Title
    task_pattern = r'###\s+T(\d+):\s+(.+?)\n(.*?)(?=\n###\s+T\d+:|\n##|\Z)'
    matches = re.findall(task_pattern, content, re.DOTALL)
    
    tasks = []
    for task_id, title, task_content in matches:
        task = parse_task_content(f"T{task_id}", title.strip(), task_content)
        tasks.append(task)
    
    return tasks


def parse_task_content(task_id: str, title: str, content: str) -> Dict[str, Any]:
    """
    Parse nội dung của 1 task
    
    Args:
        task_id: Task ID (e.g., "T001")
        title: Task title
        content: Task content block
    
    Returns:
        Task dict
    """
    task = {
        "id": task_id,
        "title": title,
        "description": "",
        "allowed_files": [],
        "definition_of_done": [],
        "checks": [],
        "dependencies": [],
        "estimated_time": ""
    }
    
    # Extract Objective
    objective_match = re.search(r'\*\*Objective:\*\*\s*(.+?)(?=\n\*\*|\Z)', content, re.DOTALL)
    if objective_match:
        task["description"] = objective_match.group(1).strip()
    
    # Extract Allowed Files
    allowed_files_match = re.search(r'\*\*Allowed Files:\*\*\s*\n((?:[-*]\s+`.+?`\s*\n)+)', content)
    if allowed_files_match:
        files_text = allowed_files_match.group(1)
        task["allowed_files"] = [
            m.strip('`') for m in re.findall(r'`([^`]+)`', files_text)
        ]
    
    # Extract Definition of Done
    dod_match = re.search(r'\*\*Definition of Done:\*\*\s*\n((?:[-*]\s+\[.\]\s+.+?\n)+)', content)
    if dod_match:
        dod_text = dod_match.group(1)
        dod_items = re.findall(r'[-*]\s+\[.\]\s+(.+)', dod_text)
        task["definition_of_done"] = [item.strip() for item in dod_items]
    
    # Extract Machine Checks
    checks_match = re.search(r'\*\*Machine Checks:\*\*\s*\n((?:[-*]\s+`.+?`\s*\n)+)', content)
    if checks_match:
        checks_text = checks_match.group(1)
        task["checks"] = [
            m.strip('`') for m in re.findall(r'`([^`]+)`', checks_text)
        ]
    
    # Extract Dependencies
    deps_match = re.search(r'\*\*Dependencies:\*\*\s+(.+)', content)
    if deps_match:
        deps_text = deps_match.group(1).strip()
        if deps_text.lower() not in ['none', 'không có']:
            # Parse "T001, T002" or "T001"
            task["dependencies"] = [d.strip() for d in deps_text.split(',')]
    
    # Extract Estimated Time
    time_match = re.search(r'\*\*Estimated Time:\*\*\s+(.+)', content)
    if time_match:
        task["estimated_time"] = time_match.group(1).strip()
    
    return task


def validate_tasks(tasks: List[Dict[str, Any]]) -> List[str]:
    """
    Validate tasks structure
    
    Returns:
        List of validation errors (empty if no errors)
    """
    errors = []
    
    task_ids = set()
    for task in tasks:
        # Check required fields
        if not task.get("id"):
            errors.append(f"Task missing ID")
        elif task["id"] in task_ids:
            errors.append(f"Duplicate task ID: {task['id']}")
        else:
            task_ids.add(task["id"])
        
        if not task.get("title"):
            errors.append(f"Task {task.get('id', 'unknown')} missing title")
        
        if not task.get("definition_of_done"):
            errors.append(f"Task {task.get('id', 'unknown')} missing Definition of Done")
        
        # Check dependencies
        for dep in task.get("dependencies", []):
            if dep not in task_ids and dep != task.get("id"):
                # Dependency chưa được define (có thể là forward dependency)
                # Chỉ warn, không error
                pass
    
    return errors


def build_tasks_json(blueprint_file: str, output_file: str) -> Dict[str, Any]:
    """
    Main function: Parse blueprint và save tasks.json
    
    Args:
        blueprint_file: Path to blueprint.md
        output_file: Path to save tasks.json
    
    Returns:
        Parsed tasks structure
    """
    # Parse
    tasks_data = parse_blueprint(blueprint_file)
    
    # Validate
    errors = validate_tasks(tasks_data["tasks"])
    if errors:
        print("⚠️  Validation warnings:")
        for error in errors:
            print(f"  - {error}")
    
    # Save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tasks_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Tasks JSON saved to: {output_file}")
    print(f"   Total tasks: {tasks_data['metadata']['total_tasks']}")
    
    return tasks_data


def init_state_json(tasks_data: Dict[str, Any], output_file: str):
    """
    Initialize state.json
    
    Args:
        tasks_data: Parsed tasks từ build_tasks_json
        output_file: Path to save state.json
    """
    state = {
        "status": "planning_complete",
        "current_task_index": 0,
        "current_retry": 0,
        "max_retries_per_task": 2,
        "completed_tasks": [],
        "blocked_task": None,
        "metadata": {
            "total_tasks": tasks_data["metadata"]["total_tasks"],
            "started_at": None,
            "completed_at": None
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    
    print(f"✅ State JSON initialized: {output_file}")


# ═══════════════════════════════════════════════════════════════════════════════
#                         CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python build_tasks_from_blueprint.py <blueprint.md> [output_dir]")
        print()
        print("Example:")
        print("  python build_tasks_from_blueprint.py .aiwf/input/blueprint.md .aiwf/run/")
        sys.exit(1)
    
    blueprint_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else ".aiwf/run/"
    
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    tasks_json = os.path.join(output_dir, "tasks.json")
    state_json = os.path.join(output_dir, "state.json")
    
    # Build
    tasks_data = build_tasks_json(blueprint_file, tasks_json)
    init_state_json(tasks_data, state_json)
    
    print()
    print("🚀 Ready to start execution loop!")
    print(f"   Run: python orchestrator.py loop")

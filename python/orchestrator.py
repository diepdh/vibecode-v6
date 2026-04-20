"""
Vibecode v6 - Orchestrator
Main execution loop engine - điều phối Coder ↔ Reviewer tự động
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from cli_wrappers import (
    call_gemini_cli,
    call_brain_cli,
    REVIEWER_MODEL,
    run_machine_checks,
    get_git_diff,
    save_to_file,
    read_file,
    parse_json_from_response,
    CLIError
)

from prompts import (
    build_coder_context,
    build_reviewer_context
)


class Orchestrator:
    """
    Orchestrator - Điều phối execution loop
    """
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.aiwf_dir = self.workspace_root / ".aiwf"
        self.input_dir = self.aiwf_dir / "input"
        self.run_dir = self.aiwf_dir / "run"
        self.logs_dir = self.run_dir / "logs"
        
        # Ensure directories exist
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Load tasks and state
        self.tasks_file = self.run_dir / "tasks.json"
        self.state_file = self.run_dir / "state.json"
        self.blueprint_file = self.input_dir / "blueprint.md"
        
        self.tasks_data = None
        self.state = None
        
    def load_data(self):
        """Load tasks.json và state.json"""
        if not self.tasks_file.exists():
            raise FileNotFoundError(f"tasks.json not found: {self.tasks_file}")
        
        if not self.state_file.exists():
            raise FileNotFoundError(f"state.json not found: {self.state_file}")
        
        with open(self.tasks_file, 'r', encoding='utf-8') as f:
            self.tasks_data = json.load(f)
        
        with open(self.state_file, 'r', encoding='utf-8') as f:
            self.state = json.load(f)
        
        self.log("Data loaded successfully")
    
    def save_state(self):
        """Save state.json"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
    
    def log(self, message: str, level: str = "INFO"):
        """Log message to console và file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        
        print(log_message)
        
        # Save to orchestrator.log
        log_file = self.logs_dir / "orchestrator.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")
    
    def get_current_task(self) -> Optional[Dict[str, Any]]:
        """Lấy task hiện tại từ state"""
        idx = self.state["current_task_index"]
        if idx >= len(self.tasks_data["tasks"]):
            return None
        return self.tasks_data["tasks"][idx]
    
    def run_task(self) -> bool:
        """
        Chạy 1 iteration của current task
        
        Returns:
            True nếu task PASS hoặc có progress
            False nếu cần dừng (BLOCKED hoặc retry exceeded)
        """
        task = self.get_current_task()
        if not task:
            self.log("No more tasks to run")
            self.state["status"] = "completed"
            self.save_state()
            return False
        
        self.log(f"Running task: {task['id']} - {task['title']}")
        
        # Step 1: Call Gemini Coder
        self.log("Step 1: Calling Gemini Coder...")
        coder_result = self.call_coder(task)
        
        if coder_result["status"] == "BLOCKED":
            self.log("Coder reported BLOCKED", level="WARN")
            self.state["status"] = "blocked"
            self.state["blocked_task"] = {
                "task_id": task["id"],
                "reason": coder_result.get("summary", "Unknown blocker")
            }
            self.save_state()
            return False
        
        # Step 2: Run machine checks
        self.log("Step 2: Running machine checks...")
        checks_output = self.run_checks(task)
        
        # Step 3: Get git diff
        self.log("Step 3: Getting git diff...")
        git_diff = get_git_diff()
        
        # Step 4: Call Brain Reviewer
        self.log("Step 4: Calling Brain Reviewer...")
        review_result = self.call_reviewer(task, coder_result["report"], git_diff, checks_output)
        
        # Step 5: Process review decision
        decision = review_result.get("decision", "BLOCK")
        self.log(f"Review decision: {decision}")
        
        if decision == "PASS":
            self.log(f"✅ Task {task['id']} PASSED", level="SUCCESS")
            self.mark_task_complete(task["id"])
            return True
            
        elif decision == "REVISE":
            self.log(f"⚠️  Task {task['id']} needs REVISE", level="WARN")
            
            # Increment retry counter
            self.state["current_retry"] += 1
            
            if self.state["current_retry"] > self.state["max_retries_per_task"]:
                self.log("Max retries exceeded, escalating to BLOCKED", level="ERROR")
                self.state["status"] = "blocked"
                self.state["blocked_task"] = {
                    "task_id": task["id"],
                    "reason": f"Max retries ({self.state['max_retries_per_task']}) exceeded"
                }
                self.save_state()
                return False
            
            # Save review feedback for next iteration
            feedback_file = self.run_dir / f"review_{task['id']}_retry{self.state['current_retry']}.json"
            save_to_file(json.dumps(review_result, indent=2), str(feedback_file))
            
            self.save_state()
            return True  # Continue với retry
            
        else:  # BLOCK
            self.log(f"🚧 Task {task['id']} BLOCKED", level="ERROR")
            self.state["status"] = "blocked"
            self.state["blocked_task"] = {
                "task_id": task["id"],
                "reason": review_result.get("reason", "Unknown block reason")
            }
            self.save_state()
            return False
    
    def call_coder(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Call Gemini Coder"""
        # Load blueprint
        blueprint = read_file(str(self.blueprint_file))
        
        # Load previous feedback nếu đây là retry
        previous_feedback = None
        if self.state["current_retry"] > 0:
            feedback_file = self.run_dir / f"review_{task['id']}_retry{self.state['current_retry'] - 1}.json"
            if feedback_file.exists():
                previous_feedback = read_file(str(feedback_file))
        
        # Build context
        context = build_coder_context(task, blueprint, previous_feedback)
        
        # Call Gemini
        try:
            response = call_gemini_cli(
                prompt=context,
                output_file=str(self.run_dir / "coder_report.txt")
            )
            
            # Parse status
            status = "DONE"
            if "STATUS: BLOCKED" in response:
                status = "BLOCKED"
            
            return {
                "status": status,
                "report": response
            }
            
        except CLIError as e:
            self.log(f"Coder CLI error: {e}", level="ERROR")
            return {
                "status": "BLOCKED",
                "report": f"CLI Error: {str(e)}"
            }
    
    def run_checks(self, task: Dict[str, Any]) -> str:
        """Run machine checks"""
        checks = task.get("checks", [])
        
        if not checks:
            return "No checks configured for this task"
        
        results = run_machine_checks(checks, cwd=str(self.workspace_root))
        
        # Format output
        output_lines = []
        for check_result in results["checks"]:
            output_lines.append(f"Command: {check_result['command']}")
            output_lines.append(f"Success: {check_result['success']}")
            if check_result.get('stdout'):
                output_lines.append(f"Stdout:\n{check_result['stdout']}")
            if check_result.get('stderr'):
                output_lines.append(f"Stderr:\n{check_result['stderr']}")
            output_lines.append("---")
        
        output = "\n".join(output_lines)
        save_to_file(output, str(self.run_dir / "test_output.txt"))
        
        return output
    
    def call_reviewer(self, task: Dict[str, Any], coder_report: str, git_diff: str, checks_output: str) -> Dict[str, Any]:
        """Call Brain Reviewer"""
        # Build context
        context = build_reviewer_context(task, coder_report, git_diff, checks_output)
        
        # Call Brain (configurable - mặc định Claude Code CLI)
        try:
            response = call_brain_cli(
                prompt=context,
                output_file=str(self.run_dir / "review.json"),
                model=REVIEWER_MODEL or None
            )
            
            # Parse JSON
            review_json = parse_json_from_response(response)
            
            if not review_json:
                self.log("Failed to parse reviewer response as JSON", level="ERROR")
                return {
                    "decision": "BLOCK",
                    "reason": "Reviewer response not valid JSON"
                }
            
            return review_json
            
        except CLIError as e:
            self.log(f"Reviewer CLI error: {e}", level="ERROR")
            return {
                "decision": "BLOCK",
                "reason": f"CLI Error: {str(e)}"
            }
    
    def mark_task_complete(self, task_id: str):
        """Mark task as complete và chuyển sang task tiếp"""
        self.state["completed_tasks"].append({
            "task_id": task_id,
            "completed_at": datetime.now().isoformat()
        })
        
        self.state["current_task_index"] += 1
        self.state["current_retry"] = 0
        
        self.save_state()
    
    def loop(self, max_iterations: int = 100):
        """
        Chạy execution loop liên tục
        
        Args:
            max_iterations: Maximum số iterations (safety limit)
        """
        self.load_data()
        
        if self.state["status"] == "completed":
            self.log("All tasks already completed!")
            return
        
        if self.state["status"] == "blocked":
            self.log("Workflow is BLOCKED. Resolve blockers before continuing.", level="WARN")
            return
        
        # Update status
        self.state["status"] = "running"
        if not self.state["metadata"].get("started_at"):
            self.state["metadata"]["started_at"] = datetime.now().isoformat()
        self.save_state()
        
        self.log("Starting execution loop...")
        
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            self.log(f"\n{'='*60}")
            self.log(f"ITERATION {iteration}")
            self.log(f"{'='*60}\n")
            
            # Run current task
            continue_loop = self.run_task()
            
            if not continue_loop:
                # Either BLOCKED or completed
                break
            
            # Check if all tasks done
            if self.state["current_task_index"] >= len(self.tasks_data["tasks"]):
                self.log("\n🎉 All tasks completed!")
                self.state["status"] = "completed"
                self.state["metadata"]["completed_at"] = datetime.now().isoformat()
                self.save_state()
                break
        
        if iteration >= max_iterations:
            self.log(f"Loop stopped: reached max iterations ({max_iterations})", level="WARN")
    
    def status(self):
        """Hiển thị status hiện tại"""
        self.load_data()
        
        print("\n" + "="*60)
        print("VIBECODE v6 - ORCHESTRATOR STATUS")
        print("="*60 + "\n")
        
        print(f"Status: {self.state['status'].upper()}")
        print(f"Current Task: {self.state['current_task_index'] + 1}/{len(self.tasks_data['tasks'])}")
        print(f"Completed: {len(self.state['completed_tasks'])}")
        print(f"Current Retry: {self.state['current_retry']}/{self.state['max_retries_per_task']}")
        
        if self.state.get("blocked_task"):
            print(f"\n⚠️  BLOCKED TASK:")
            print(f"   Task: {self.state['blocked_task']['task_id']}")
            print(f"   Reason: {self.state['blocked_task']['reason']}")
        
        print("\nCompleted Tasks:")
        for completed in self.state["completed_tasks"]:
            print(f"  ✅ {completed['task_id']} - {completed['completed_at']}")
        
        # Current task
        task = self.get_current_task()
        if task:
            print(f"\nCurrent Task:")
            print(f"  ID: {task['id']}")
            print(f"  Title: {task['title']}")
            print(f"  DoD: {len(task.get('definition_of_done', []))} criteria")
        
        print()
    
    def reset(self):
        """Reset execution state"""
        confirm = input("⚠️  This will reset all execution progress. Continue? (yes/no): ")
        if confirm.lower() != "yes":
            print("Reset cancelled.")
            return
        
        self.load_data()
        
        self.state["status"] = "planning_complete"
        self.state["current_task_index"] = 0
        self.state["current_retry"] = 0
        self.state["completed_tasks"] = []
        self.state["blocked_task"] = None
        self.state["metadata"]["started_at"] = None
        self.state["metadata"]["completed_at"] = None
        
        self.save_state()
        
        self.log("Execution state reset successfully")


# ═══════════════════════════════════════════════════════════════════════════════
#                         CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py <command>")
        print()
        print("Commands:")
        print("  init      - Initialize tasks.json and state.json from blueprint")
        print("  run       - Run one task iteration")
        print("  loop      - Run execution loop until done or blocked")
        print("  status    - Show current status")
        print("  reset     - Reset execution state")
        print()
        print("Example:")
        print("  python orchestrator.py loop")
        sys.exit(1)
    
    command = sys.argv[1]
    orchestrator = Orchestrator()
    
    if command == "init":
        # Run build_tasks_from_blueprint.py
        import subprocess
        blueprint = ".aiwf/input/blueprint.md"
        subprocess.run([sys.executable, "build_tasks_from_blueprint.py", blueprint])
        
    elif command == "run":
        orchestrator.load_data()
        orchestrator.run_task()
        
    elif command == "loop":
        orchestrator.loop()
        
    elif command == "status":
        orchestrator.status()
        
    elif command == "reset":
        orchestrator.reset()
        
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()

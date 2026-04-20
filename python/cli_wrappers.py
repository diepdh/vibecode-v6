"""
Vibecode v6 - CLI Wrappers
Wrapper functions để gọi Claude Code CLI và Gemini CLI
"""

import subprocess
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any


class CLIError(Exception):
    """Exception khi CLI call fail"""
    pass


# ═══════════════════════════════════════════════════════════════════════════════
#                         CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Brain CLI Configuration
# Options: "claude" (Claude Code CLI) hoặc custom command
BRAIN_CLI_COMMAND = os.getenv("VIBECODE_BRAIN_CLI", "claude")

# Coder CLI Configuration  
CODER_CLI_COMMAND = os.getenv("VIBECODE_CODER_CLI", "gemini")

# Model configurations
# - BRAIN_PHASE_A_MODEL: model dùng cho planning/synthesis ở Phase A
# - REVIEWER_MODEL: model dùng cho reviewer ở Phase B
# - CODER_MODEL: nếu để trống thì không truyền --model và để Gemini CLI tự chọn
BRAIN_MODEL = os.getenv("VIBECODE_BRAIN_MODEL", "").strip()
BRAIN_PHASE_A_MODEL = os.getenv("VIBECODE_BRAIN_PHASE_A_MODEL", "gpt-5.4").strip()
REVIEWER_MODEL = os.getenv("VIBECODE_REVIEWER_MODEL", "gpt-5.3-codex").strip()
CODER_MODEL = os.getenv("VIBECODE_CODER_MODEL", "").strip()


def call_brain_cli(
    prompt: str,
    context_files: List[str] = None,
    output_file: str = None,
    timeout: int = 300,
    model: str = None
) -> str:
    """
    Gọi Brain CLI (configurable - mặc định Claude Code CLI)
    
    Args:
        prompt: Prompt string
        context_files: Danh sách file paths để include làm context
        output_file: Path để lưu output (nếu cần)
        timeout: Timeout in seconds
        model: Model name (optional, uses BRAIN_MODEL if not specified)
    
    Returns:
        Response text từ Brain
    
    Raises:
        CLIError: Nếu CLI call fail
    """
    prompt_file = None
    try:
        # Tạo temp file cho prompt (cross-platform)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", prefix="vibecode_brain_prompt_", delete=False, encoding="utf-8"
        ) as tmp_file:
            prompt_file = tmp_file.name
            tmp_file.write(prompt)

        # Build command through adapter (support nhiều loại Brain CLI)
        adapter_script = Path(__file__).with_name("brain_cli_adapter.py")
        if not adapter_script.exists():
            raise CLIError(f"Brain adapter script not found: {adapter_script}")

        python_executable = os.getenv("VIBECODE_PYTHON_EXECUTABLE", sys.executable)
        cmd = [
            python_executable,
            str(adapter_script),
            "--cli",
            BRAIN_CLI_COMMAND,
            "--prompt-file",
            prompt_file,
        ]

        if model or BRAIN_MODEL:
            cmd.extend(["--model", model or BRAIN_MODEL])

        if context_files:
            for file_path in context_files:
                if os.path.exists(file_path):
                    cmd.extend(["--context-file", file_path])
        
        # Execute
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True
        )
        
        response = result.stdout.strip()
        
        # Save to output file nếu cần
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response)

        return response
        
    except subprocess.TimeoutExpired:
        raise CLIError(f"Brain CLI timeout after {timeout}s")
    except subprocess.CalledProcessError as e:
        raise CLIError(f"Brain CLI error: {e.stderr}")
    except Exception as e:
        raise CLIError(f"Unexpected error calling Brain: {str(e)}")
    finally:
        if prompt_file and os.path.exists(prompt_file):
            os.remove(prompt_file)


# Alias for backward compatibility
def call_claude_cli(*args, **kwargs):
    """Alias for call_brain_cli - backward compatibility"""
    return call_brain_cli(*args, **kwargs)


def call_gemini_cli(
    prompt: str,
    context_files: List[str] = None,
    output_file: str = None,
    timeout: int = 300,
    model: str = None
) -> str:
    """
    Gọi Gemini CLI
    
    Args:
        prompt: Prompt string
        context_files: Danh sách file paths để include làm context
        output_file: Path để lưu output (nếu cần)
        timeout: Timeout in seconds
        model: Gemini model name. Nếu None/"" thì để Gemini CLI tự chọn model
    
    Returns:
        Response text từ Gemini
    
    Raises:
        CLIError: Nếu CLI call fail
    """
    prompt_file = None
    try:
        # Tạo temp file cho prompt (cross-platform)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", prefix="vibecode_coder_prompt_", delete=False, encoding="utf-8"
        ) as tmp_file:
            prompt_file = tmp_file.name
            tmp_file.write(prompt)
        
        # Build command
        cmd = [CODER_CLI_COMMAND]
        
        # Add model
        effective_model = model or CODER_MODEL
        if effective_model:
            cmd.extend(["--model", effective_model])
        
        # Add context files nếu có
        if context_files:
            for file_path in context_files:
                if os.path.exists(file_path):
                    cmd.extend(["--file", file_path])
        
        # Add prompt
        cmd.extend(["--prompt-file", prompt_file])
        
        # Execute
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True
        )
        
        response = result.stdout.strip()
        
        # Save to output file nếu cần
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response)

        return response
        
    except subprocess.TimeoutExpired:
        raise CLIError(f"Gemini CLI timeout after {timeout}s")
    except subprocess.CalledProcessError as e:
        raise CLIError(f"Gemini CLI error: {e.stderr}")
    except Exception as e:
        raise CLIError(f"Unexpected error calling Gemini: {str(e)}")
    finally:
        if prompt_file and os.path.exists(prompt_file):
            os.remove(prompt_file)


def run_machine_checks(checks: List[str], cwd: str = None) -> Dict[str, Any]:
    """
    Chạy machine checks (tests, lint, build)
    
    Args:
        checks: Danh sách commands cần chạy (e.g., ["pnpm test", "pnpm lint"])
        cwd: Working directory
    
    Returns:
        Dict với kết quả mỗi check
    """
    results = {
        "success": True,
        "checks": []
    }
    
    for check_cmd in checks:
        try:
            result = subprocess.run(
                check_cmd.split(),
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=120
            )
            
            check_result = {
                "command": check_cmd,
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            results["checks"].append(check_result)
            
            if result.returncode != 0:
                results["success"] = False
                
        except subprocess.TimeoutExpired:
            results["success"] = False
            results["checks"].append({
                "command": check_cmd,
                "success": False,
                "error": "Timeout after 120s"
            })
        except Exception as e:
            results["success"] = False
            results["checks"].append({
                "command": check_cmd,
                "success": False,
                "error": str(e)
            })
    
    return results


def get_git_diff(since_ref: str = None, file_pattern: str = None) -> str:
    """
    Lấy git diff
    
    Args:
        since_ref: Git ref để diff (e.g., "HEAD", "main"). None = staged changes
        file_pattern: Chỉ lấy diff của files match pattern
    
    Returns:
        Diff string
    """
    try:
        cmd = ["git", "diff"]
        
        if since_ref:
            cmd.append(since_ref)
        else:
            cmd.append("--staged")
        
        if file_pattern:
            cmd.append("--")
            cmd.append(file_pattern)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return result.stdout
        
    except subprocess.CalledProcessError as e:
        return f"Error getting git diff: {e.stderr}"


def save_to_file(content: str, file_path: str, mode: str = "w"):
    """
    Save content to file với proper encoding
    
    Args:
        content: Content to save
        file_path: File path
        mode: Write mode (w or a)
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, mode, encoding="utf-8") as f:
        f.write(content)


def read_file(file_path: str) -> str:
    """
    Read file với proper encoding
    
    Args:
        file_path: File path
    
    Returns:
        File content
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def parse_json_from_response(response: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON từ response (extract từ markdown code blocks nếu cần)
    
    Args:
        response: Response string có thể chứa JSON
    
    Returns:
        Parsed JSON dict hoặc None nếu không parse được
    """
    # Try parse trực tiếp
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # Try extract từ markdown code block
    import re
    json_pattern = r'```(?:json)?\s*(\{[\s\S]*?\})\s*```'
    matches = re.findall(json_pattern, response)
    
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    return None


# ═══════════════════════════════════════════════════════════════════════════════
#                         HIGH-LEVEL WRAPPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_plan(goal_file: str, output_file: str) -> str:
    """
    Phase A.1: Brain tạo plan.md
    
    Args:
        goal_file: Path to goal.md
        output_file: Path to save plan.md
    
    Returns:
        Plan content
    """
    from prompts import BRAIN_PLANNER_PROMPT
    
    prompt = f"""{BRAIN_PLANNER_PROMPT}

## GOAL

{read_file(goal_file)}
"""
    
    response = call_brain_cli(
        prompt=prompt,
        output_file=output_file,
        model=BRAIN_PHASE_A_MODEL or None
    )
    
    return response


def review_plan_claude(plan_file: str, output_file: str) -> str:
    """
    Phase A.2: Claude review plan
    
    Args:
        plan_file: Path to plan.md
        output_file: Path to save feedback_1.md
    
    Returns:
        Feedback content
    """
    from prompts import CLAUDE_PLAN_REVIEWER_PROMPT
    
    prompt = f"""{CLAUDE_PLAN_REVIEWER_PROMPT}

## PLAN TO REVIEW

{read_file(plan_file)}
"""
    
    # Claude reviewer vẫn dùng call_brain_cli (vì có thể configure)
    response = call_brain_cli(
        prompt=prompt,
        output_file=output_file,
        model=BRAIN_PHASE_A_MODEL or None
    )
    
    return response


def review_plan_gemini(plan_file: str, output_file: str) -> str:
    """
    Phase A.3: Gemini review plan
    
    Args:
        plan_file: Path to plan.md
        output_file: Path to save feedback_2.md
    
    Returns:
        Feedback content
    """
    from prompts import GEMINI_PLAN_REVIEWER_PROMPT
    
    prompt = f"""{GEMINI_PLAN_REVIEWER_PROMPT}

## PLAN TO REVIEW

{read_file(plan_file)}
"""
    
    response = call_gemini_cli(
        prompt=prompt,
        output_file=output_file
    )
    
    return response


def synthesize_blueprint(plan_file: str, feedback1_file: str, feedback2_file: str, output_file: str) -> str:
    """
    Phase A.5: Brain tổng hợp blueprint
    
    Args:
        plan_file: Path to plan.md
        feedback1_file: Path to feedback_1.md
        feedback2_file: Path to feedback_2.md
        output_file: Path to save blueprint.md
    
    Returns:
        Blueprint content
    """
    from prompts import BRAIN_SYNTHESIZER_PROMPT
    
    prompt = f"""{BRAIN_SYNTHESIZER_PROMPT}

## PLAN.MD (Original)

{read_file(plan_file)}

---

## FEEDBACK_1.MD (Claude)

{read_file(feedback1_file)}

---

## FEEDBACK_2.MD (Gemini)

{read_file(feedback2_file)}
"""
    
    response = call_brain_cli(
        prompt=prompt,
        output_file=output_file,
        model=BRAIN_PHASE_A_MODEL or None
    )
    
    return response

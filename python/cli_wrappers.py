"""
Vibecode v6 - CLI Wrappers
Wrapper functions Ä‘á»ƒ gá»i Claude Code CLI vÃ  Gemini CLI
"""

import subprocess
import json
import os
import sys
import tempfile
import shlex
import fnmatch
from pathlib import Path
from typing import List, Optional, Dict, Any


class CLIError(Exception):
    """Exception khi CLI call fail"""
    pass


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#                         CONFIGURATION
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# Brain CLI Configuration
# Options: "claude" (Claude Code CLI) hoáº·c custom command
BRAIN_CLI_COMMAND = os.getenv("VIBECODE_BRAIN_CLI", "codex.cmd")

# Coder CLI Configuration
CODER_CLI_COMMAND = os.getenv("VIBECODE_CODER_CLI", "gemini.cmd")

# Model configurations
# - BRAIN_PHASE_A_MODEL: model dÃ¹ng cho planning/synthesis á»Ÿ Phase A
# - REVIEWER_MODEL: model dÃ¹ng cho reviewer á»Ÿ Phase B
# - CODER_MODEL: náº¿u Ä‘á»ƒ trá»‘ng thÃ¬ khÃ´ng truyá»n --model vÃ  Ä‘á»ƒ Gemini CLI tá»± chá»n
BRAIN_MODEL = os.getenv("VIBECODE_BRAIN_MODEL", "").strip()
BRAIN_PHASE_A_MODEL = os.getenv("VIBECODE_BRAIN_PHASE_A_MODEL", "gpt-5.4").strip()
REVIEWER_MODEL = os.getenv("VIBECODE_REVIEWER_MODEL", "gpt-5.3-codex").strip()
CODER_MODEL = os.getenv("VIBECODE_CODER_MODEL", "").strip()
CODER_APPROVAL_MODE = os.getenv("VIBECODE_CODER_APPROVAL_MODE", "").strip()
CODER_EXTRA_ARGS = os.getenv("VIBECODE_CODER_EXTRA_ARGS", "").strip()


def _int_env(name: str, default: int) -> int:
    """Read integer from environment with safe fallback."""
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
        if value > 0:
            return value
    except ValueError:
        pass
    return default


CODER_TIMEOUT = _int_env("VIBECODE_CODER_TIMEOUT", 300)


def call_brain_cli(
    prompt: str,
    context_files: List[str] = None,
    output_file: str = None,
    timeout: int = 300,
    model: str = None
) -> str:
    """
    Gá»i Brain CLI (configurable - máº·c Ä‘á»‹nh Claude Code CLI)
    
    Args:
        prompt: Prompt string
        context_files: Danh sÃ¡ch file paths Ä‘á»ƒ include lÃ m context
        output_file: Path Ä‘á»ƒ lÆ°u output (náº¿u cáº§n)
        timeout: Timeout in seconds
        model: Model name (optional, uses BRAIN_MODEL if not specified)
    
    Returns:
        Response text tá»« Brain
    
    Raises:
        CLIError: Náº¿u CLI call fail
    """
    prompt_file = None
    try:
        # Táº¡o temp file cho prompt (cross-platform)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", prefix="vibecode_brain_prompt_", delete=False, encoding="utf-8"
        ) as tmp_file:
            prompt_file = tmp_file.name
            tmp_file.write(prompt)

        # Build command through adapter (support nhiá»u loáº¡i Brain CLI)
        adapter_script = Path(__file__).with_name("brain_cli_adapter.py")
        if not adapter_script.exists():
            raise CLIError(f"Brain adapter script not found: {adapter_script}")

        python_executable = os.getenv("VIBECODE_PYTHON_EXECUTABLE", sys.executable)
        _brain_cli = os.getenv("VIBECODE_BRAIN_CLI", "claude")
        _brain_model_cfg = os.getenv("VIBECODE_BRAIN_MODEL", "").strip()

        cmd = [
            python_executable,
            str(adapter_script),
            "--cli",
            _brain_cli,
            "--prompt-file",
            prompt_file,
        ]

        if model or _brain_model_cfg:
            cmd.extend(["--model", model or _brain_model_cfg])

        if context_files:
            for file_path in context_files:
                if os.path.exists(file_path):
                    cmd.extend(["--context-file", file_path])
        
        # Execute
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False
        )

        if result.returncode != 0:
            err_text = (result.stderr or "").strip()
            out_text = (result.stdout or "").strip()
            detail = err_text or out_text or f"exit code {result.returncode} with empty stderr/stdout"
            cmd_preview = " ".join(cmd)
            raise CLIError(f"Brain CLI error (rc={result.returncode}): {detail} | cmd={cmd_preview}")
        
        response = (result.stdout or "").strip()
        
        # Save to output file náº¿u cáº§n
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response)

        return response
        
    except subprocess.TimeoutExpired:
        raise CLIError(f"Brain CLI timeout after {timeout}s")
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
    timeout: int = None,
    model: str = None,
    cwd: str = None
) -> str:
    """
    Gá»i Gemini CLI
    
    Args:
        prompt: Prompt string
        context_files: Danh sÃ¡ch file paths Ä‘á»ƒ include lÃ m context
        output_file: Path Ä‘á»ƒ lÆ°u output (náº¿u cáº§n)
        timeout: Timeout in seconds
        model: Gemini model name. Náº¿u None/"" thÃ¬ Ä‘á»ƒ Gemini CLI tá»± chá»n model
    
    Returns:
        Response text tá»« Gemini
    
    Raises:
        CLIError: Náº¿u CLI call fail
    """
    try:
        # Read coder config dynamically so runtime switches via set-coder take effect.
        _coder_cli = os.getenv("VIBECODE_CODER_CLI", "gemini.cmd")
        _coder_model = os.getenv("VIBECODE_CODER_MODEL", "").strip()
        _coder_approval = os.getenv("VIBECODE_CODER_APPROVAL_MODE", "").strip()
        _coder_extra = os.getenv("VIBECODE_CODER_EXTRA_ARGS", "").strip()

        # Gemini CLI >= 0.38 does not support --prompt-file.
        # Use headless mode with --prompt and send full context via stdin.
        merged_prompt = prompt
        if context_files:
            file_chunks = []
            for file_path in context_files:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            file_chunks.append(
                                f"\n\n---\nContext file: {file_path}\n---\n{f.read()}\n"
                            )
                    except Exception:
                        # Keep execution resilient; ignore unreadable context files.
                        pass
            if file_chunks:
                merged_prompt = merged_prompt + "".join(file_chunks)

        # Build command
        cmd = [_coder_cli]
        cli_name = os.path.basename(_coder_cli).lower()
        is_claude = "claude" in cli_name

        # Add model
        effective_model = model or _coder_model
        if effective_model:
            cmd.extend(["--model", effective_model])

        if is_claude:
            # Claude Code headless mode.
            cmd.extend(["--print"])

            # Map generic approval mode to Claude permission mode.
            # Supported: acceptEdits, auto, bypassPermissions, default, dontAsk, plan
            if _coder_approval:
                mode_map = {
                    "default": "default",
                    "auto_edit": "acceptEdits",
                    "yolo": "bypassPermissions",
                    "bypassPermissions": "bypassPermissions",
                    "plan": "plan",
                }
                mapped = mode_map.get(_coder_approval, _coder_approval)
                cmd.extend(["--permission-mode", mapped])
        else:
            # Gemini-style approval mode: default | auto_edit | yolo | plan
            if _coder_approval:
                cmd.extend(["--approval-mode", _coder_approval])

            # Force non-interactive mode for Gemini.
            # Full payload is provided through stdin to avoid Windows cmd length limits.
            cmd.extend(["--prompt", "Read full task context from stdin and execute it exactly."])

        # Optional extra args via env (space-delimited, shell-like).
        if _coder_extra:
            cmd.extend(shlex.split(_coder_extra))

        # Execute
        effective_timeout = timeout or _int_env("VIBECODE_CODER_TIMEOUT", CODER_TIMEOUT)
        result = subprocess.run(
            cmd,
            input=merged_prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=cwd,
            timeout=effective_timeout,
        )

        response = (result.stdout or "").strip()

        # Detect authentication errors before treating output as valid.
        _resp_lower = response.lower()
        if "not logged in" in _resp_lower or "please run /login" in _resp_lower:
            raise CLIError(f"Coder not authenticated â€” run `/login` in {_coder_cli} first: {response[:200]}")

        # Non-zero exit code is tolerated when the coder produced valid task output.
        # Gemini can exit non-zero on EPERM/scan errors but still complete the task.
        if result.returncode != 0 and "status:" not in _resp_lower:
            err = (result.stderr or "").strip() or response[:200] or f"exit code {result.returncode}"
            raise CLIError(f"Coder CLI error: {err}")

        # Save to output file náº¿u cáº§n
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response)

        return response

    except subprocess.TimeoutExpired:
        raise CLIError(f"Coder CLI timeout after {timeout or CODER_TIMEOUT}s")
    except Exception as e:
        raise CLIError(f"Unexpected error calling coder CLI: {str(e)}")


def run_machine_checks(checks: List[str], cwd: str = None) -> Dict[str, Any]:
    """
    Cháº¡y machine checks (tests, lint, build)
    
    Args:
        checks: Danh sÃ¡ch commands cáº§n cháº¡y (e.g., ["pnpm test", "pnpm lint"])
        cwd: Working directory
    
    Returns:
        Dict vá»›i káº¿t quáº£ má»—i check
    """
    results = {
        "success": True,
        "checks": []
    }
    
    for check_cmd in checks:
        try:
            if os.name == "nt":
                cmd = [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    check_cmd,
                ]
            else:
                cmd = shlex.split(check_cmd)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
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


def get_git_diff(since_ref: str = None, file_pattern: str = None, cwd: str = None) -> str:
    """
    Láº¥y git diff
    
    Args:
        since_ref: Git ref Ä‘á»ƒ diff (e.g., "HEAD", "main"). None = staged changes
        file_pattern: Chá»‰ láº¥y diff cá»§a files match pattern
    
    Returns:
        Diff string
    """
    try:
        # Prefer unstaged diff first (what coder usually just changed).
        # Fallback to cached diff if unstaged is empty.
        def _run_diff(extra_args: List[str]) -> str:
            cmd = ["git", "diff"] + extra_args
            if file_pattern:
                cmd.extend(["--", file_pattern])
            r = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=cwd,
                check=True
            )
            return r.stdout or ""

        def _run_cmd(cmd: List[str]) -> str:
            r = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=cwd,
                check=True
            )
            return r.stdout or ""

        if since_ref:
            diff_text = _run_diff([since_ref])
            if diff_text.strip():
                return diff_text

        unstaged = _run_diff([])
        if unstaged.strip():
            return unstaged

        cached = _run_diff(["--cached"])
        if cached.strip():
            return cached

        # Fallback: generate synthetic patch for untracked files (docs/tasks often
        # add new files, which normal git diff doesn't show until staged).
        status = _run_cmd(["git", "status", "--porcelain"])
        if status.strip():
            def _matches_pattern(rel_path: str, pattern: str) -> bool:
                rp = rel_path.replace("\\", "/")
                pt = (pattern or "").replace("\\", "/")
                if not pt:
                    return True
                if rp == pt:
                    return True
                if rp.startswith(pt.rstrip("/") + "/"):
                    return True
                # If git status reports only a parent directory as untracked
                # (e.g. "?? results/v3/"), still treat it as matching nested
                # allowed file patterns like "results/v3/logs".
                if pt.startswith(rp.rstrip("/") + "/"):
                    return True
                return fnmatch.fnmatch(rp, pt)

            status_lines = status.splitlines()
            if file_pattern:
                status_lines = [
                    line for line in status_lines
                    if len(line) >= 4 and _matches_pattern(line[3:].strip(), file_pattern)
                ]
            if not status_lines:
                return ""

            filtered_status = "\n".join(status_lines)
            patches: List[str] = [f"# git status --porcelain\n{filtered_status}"]
            for line in status_lines:
                if not line.startswith("?? "):
                    continue
                rel_path = line[3:].strip()
                target = rel_path
                if file_pattern and not _matches_pattern(rel_path, file_pattern):
                    continue
                # Use git no-index diff against empty source to emulate add-file patch.
                try:
                    p = _run_cmd(["git", "diff", "--no-index", "--", os.devnull, target])
                    if p.strip():
                        patches.append(p)
                except subprocess.CalledProcessError as e:
                    # git diff --no-index returns non-zero when files differ; still carries patch in stdout.
                    out = (e.stdout or "")
                    if out.strip():
                        patches.append(out)
            return "\n\n".join(patches)

        return ""
        
    except subprocess.CalledProcessError as e:
        return f"Error getting git diff: {e.stderr}"


def save_to_file(content: str, file_path: str, mode: str = "w"):
    """
    Save content to file vá»›i proper encoding
    
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
    Read file vá»›i proper encoding
    
    Args:
        file_path: File path
    
    Returns:
        File content
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def parse_json_from_response(response: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON tá»« response (extract tá»« markdown code blocks náº¿u cáº§n)
    
    Args:
        response: Response string cÃ³ thá»ƒ chá»©a JSON
    
    Returns:
        Parsed JSON dict hoáº·c None náº¿u khÃ´ng parse Ä‘Æ°á»£c
    """
    # Try parse trá»±c tiáº¿p
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # Try extract tá»« markdown code block
    import re
    json_pattern = r'```(?:json)?\s*(\{[\s\S]*?\})\s*```'
    matches = re.findall(json_pattern, response)
    
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    return None


def _read_optional_runbook_from_input_dir(seed_file: str, filename: str = "common_failures_runbook.md") -> str:
    """
    Try reading runbook from the same input directory as seed_file.
    Returns empty string if not found.
    """
    try:
        base_dir = Path(seed_file).resolve().parent
        runbook_path = base_dir / filename
        if runbook_path.exists():
            return read_file(str(runbook_path))
    except Exception:
        pass
    return ""


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#                         HIGH-LEVEL WRAPPER FUNCTIONS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def generate_plan(goal_file: str, output_file: str) -> str:
    """
    Phase A.1: Brain táº¡o plan.md
    
    Args:
        goal_file: Path to goal.md
        output_file: Path to save plan.md
    
    Returns:
        Plan content
    """
    from prompts import BRAIN_PLANNER_PROMPT
    
    runbook_text = _read_optional_runbook_from_input_dir(goal_file)
    runbook_block = ""
    if runbook_text:
        runbook_block = f"""

## COMMON FAILURES RUNBOOK (MUST APPLY)

{runbook_text}
"""

    prompt = f"""{BRAIN_PLANNER_PROMPT}

## GOAL

{read_file(goal_file)}

{runbook_block}
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
    
    # Claude reviewer váº«n dÃ¹ng call_brain_cli (vÃ¬ cÃ³ thá»ƒ configure)
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
    Phase A.5: Brain tá»•ng há»£p blueprint
    
    Args:
        plan_file: Path to plan.md
        feedback1_file: Path to feedback_1.md
        feedback2_file: Path to feedback_2.md
        output_file: Path to save blueprint.md
    
    Returns:
        Blueprint content
    """
    from prompts import BRAIN_SYNTHESIZER_PROMPT
    
    runbook_text = _read_optional_runbook_from_input_dir(plan_file)
    runbook_block = ""
    if runbook_text:
        runbook_block = f"""

---

## COMMON FAILURES RUNBOOK (MUST APPLY INTO BLUEPRINT TASKS)

{runbook_text}
"""

    prompt = f"""{BRAIN_SYNTHESIZER_PROMPT}

## PLAN.MD (Original)

{read_file(plan_file)}

---

## FEEDBACK_1.MD (Claude)

{read_file(feedback1_file)}

---

## FEEDBACK_2.MD (Gemini)

{read_file(feedback2_file)}

{runbook_block}
"""
    
    response = call_brain_cli(
        prompt=prompt,
        output_file=output_file,
        model=BRAIN_PHASE_A_MODEL or None
    )
    
    return response


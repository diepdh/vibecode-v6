"""
Vibecode v6 - Brain CLI Adapter
Bridge từ một interface chuẩn sang nhiều kiểu Brain CLI khác nhau.
"""

import argparse
import os
import shlex
import subprocess
import sys
from typing import List


def build_context_args(context_files: List[str], flag: str) -> List[str]:
    if not context_files:
        return []
    args: List[str] = []
    for file_path in context_files:
        args.extend([flag, file_path])
    return args


def main() -> int:
    parser = argparse.ArgumentParser(description="Brain CLI Adapter")
    parser.add_argument("--cli", required=True, help="CLI command name/path")
    parser.add_argument("--model", default="", help="Model name")
    parser.add_argument("--prompt-file", required=True, help="Prompt file path")
    parser.add_argument("--context-file", action="append", default=[], help="Context file path")
    args = parser.parse_args()

    mode = os.getenv("VIBECODE_BRAIN_ADAPTER_MODE", "auto").strip().lower()
    model_flag = os.getenv("VIBECODE_BRAIN_MODEL_FLAG", "--model")
    context_flag = os.getenv("VIBECODE_BRAIN_CONTEXT_FLAG", "--file")
    prompt_file_flag = os.getenv("VIBECODE_BRAIN_PROMPT_FILE_FLAG", "--prompt-file")
    prompt_flag = os.getenv("VIBECODE_BRAIN_PROMPT_FLAG", "--prompt")
    extra_args = shlex.split(os.getenv("VIBECODE_BRAIN_EXTRA_ARGS", ""))

    cmd: List[str] = [args.cli]
    cli_name = os.path.basename(args.cli).lower()
    is_codex_cli = "codex" in cli_name

    # Auto-detect mode based on CLI name when not explicitly set.
    if mode == "auto":
        if "claude" in cli_name:
            mode = "claude"
        else:
            mode = "stdin"

    with open(args.prompt_file, "r", encoding="utf-8") as f:
        prompt_text = f.read()

    # For non-codex CLIs: model flag and extra_args go at top level.
    # For codex: model and extra_args must go AFTER the `exec` subcommand.
    if not is_codex_cli:
        if args.model and model_flag:
            cmd.extend([model_flag, args.model])
        cmd.extend(extra_args)

    if mode == "claude":
        # Claude Code CLI headless: --print --bare + prompt via stdin.
        cmd.extend(["--print", "--bare"])
        cmd.extend(build_context_args(args.context_file, context_flag))
        result = subprocess.run(
            cmd,
            input=prompt_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    elif mode == "claude_file":
        # Legacy: pass prompt as file. Most CLIs do NOT support --prompt-file;
        # prefer 'auto' or 'claude' mode instead.
        cmd.extend(build_context_args(args.context_file, context_flag))
        cmd.extend([prompt_file_flag, args.prompt_file])
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    elif mode == "stdin":
        # Codex CLI requires `exec` subcommand for non-interactive usage.
        # Model and extra_args go AFTER exec for codex.
        if is_codex_cli:
            cmd.append("exec")
            if args.model and model_flag:
                cmd.extend([model_flag, args.model])
            cmd.extend(extra_args)
        cmd.extend(build_context_args(args.context_file, context_flag))
        result = subprocess.run(
            cmd,
            input=prompt_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    elif mode == "prompt_arg":
        # Codex CLI requires `exec` subcommand; model and extra_args go after exec.
        if is_codex_cli:
            cmd.append("exec")
            if args.model and model_flag:
                cmd.extend([model_flag, args.model])
            cmd.extend(extra_args)
        cmd.extend(build_context_args(args.context_file, context_flag))
        cmd.extend([prompt_flag, prompt_text])
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    else:
        print(
            f"Unsupported VIBECODE_BRAIN_ADAPTER_MODE: {mode}. "
            f"Use one of: claude_file | stdin | prompt_arg",
            file=sys.stderr,
        )
        return 2

    if result.returncode != 0:
        # Avoid Windows console encoding crashes (cp1252) on non-ASCII text.
        err_text = (result.stderr or "").strip()
        try:
            sys.stderr.write(err_text + ("\n" if err_text else ""))
        except UnicodeEncodeError:
            sys.stderr.buffer.write((err_text + ("\n" if err_text else "")).encode("utf-8", errors="replace"))
            sys.stderr.buffer.flush()
        return result.returncode

    out_text = result.stdout or ""
    try:
        sys.stdout.write(out_text)
    except UnicodeEncodeError:
        # Fallback for terminals using legacy codepages.
        sys.stdout.buffer.write(out_text.encode("utf-8", errors="replace"))
        sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

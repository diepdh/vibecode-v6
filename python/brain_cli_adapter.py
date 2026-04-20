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

    mode = os.getenv("VIBECODE_BRAIN_ADAPTER_MODE", "claude_file").strip().lower()
    model_flag = os.getenv("VIBECODE_BRAIN_MODEL_FLAG", "--model")
    context_flag = os.getenv("VIBECODE_BRAIN_CONTEXT_FLAG", "--file")
    prompt_file_flag = os.getenv("VIBECODE_BRAIN_PROMPT_FILE_FLAG", "--prompt-file")
    prompt_flag = os.getenv("VIBECODE_BRAIN_PROMPT_FLAG", "--prompt")
    extra_args = shlex.split(os.getenv("VIBECODE_BRAIN_EXTRA_ARGS", ""))

    with open(args.prompt_file, "r", encoding="utf-8") as f:
        prompt_text = f.read()

    cmd: List[str] = [args.cli]
    if args.model and model_flag:
        cmd.extend([model_flag, args.model])
    cmd.extend(extra_args)

    if mode == "claude_file":
        cmd.extend(build_context_args(args.context_file, context_flag))
        cmd.extend([prompt_file_flag, args.prompt_file])
        result = subprocess.run(cmd, capture_output=True, text=True)
    elif mode == "stdin":
        cmd.extend(build_context_args(args.context_file, context_flag))
        result = subprocess.run(cmd, input=prompt_text, capture_output=True, text=True)
    elif mode == "prompt_arg":
        cmd.extend(build_context_args(args.context_file, context_flag))
        cmd.extend([prompt_flag, prompt_text])
        result = subprocess.run(cmd, capture_output=True, text=True)
    else:
        print(
            f"Unsupported VIBECODE_BRAIN_ADAPTER_MODE: {mode}. "
            f"Use one of: claude_file | stdin | prompt_arg",
            file=sys.stderr,
        )
        return 2

    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        return result.returncode

    sys.stdout.write(result.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

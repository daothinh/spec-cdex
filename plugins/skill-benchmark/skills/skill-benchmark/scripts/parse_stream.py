#!/usr/bin/env python3
"""
Parse raw_stream.jsonl from a headless benchmark session into structured output files.

Supports both legacy Claude stream-json output and Codex `codex exec --json` output.

Usage:
    python3 parse_stream.py <output_dir> <sandbox_dir> <skill_name> <mode> <run_number> [runner_model]

Produces:
    <output_dir>/response.json   — Final assistant output extracted from the stream
    <output_dir>/transcript.json — All stream events as a JSON array
    <output_dir>/meta.json       — Session metadata derived from the stream
"""

import json
import sys
import os


def parse_stream(output_dir, sandbox_dir, skill_name, mode, run_number, runner_model="unknown"):
    raw_path = os.path.join(output_dir, "raw_stream.jsonl")
    events = []
    result_event = None
    last_agent_message = None
    turn_completed = None
    thread_id = None
    turn_count = 0
    tool_items = 0

    if not os.path.exists(raw_path):
        print(f"ERROR: {raw_path} not found")
        write_error_files(
            output_dir,
            sandbox_dir,
            skill_name,
            mode,
            run_number,
            runner_model,
            "raw_stream.jsonl not found",
        )
        return False

    with open(raw_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                events.append(event)
                event_type = event.get("type")
                if event_type == "result":
                    result_event = event
                elif event_type == "thread.started":
                    thread_id = event.get("thread_id")
                elif event_type == "turn.started":
                    turn_count += 1
                elif event_type == "turn.completed":
                    turn_completed = event
                elif event_type == "item.completed":
                    item = event.get("item", {})
                    if item.get("type") == "agent_message":
                        last_agent_message = item
                    else:
                        tool_items += 1
            except json.JSONDecodeError:
                pass

    # response.json
    with open(os.path.join(output_dir, "response.json"), "w") as f:
        if result_event:
            json.dump(result_event, f, indent=2)
        elif last_agent_message or turn_completed:
            json.dump(
                {
                    "format": "codex-exec-json",
                    "thread_id": thread_id,
                    "result": last_agent_message.get("text", "") if last_agent_message else "",
                    "last_agent_message": last_agent_message,
                    "turn_completed": turn_completed,
                },
                f,
                indent=2,
            )
        else:
            json.dump({"error": True, "message": "No result event found in stream"}, f, indent=2)

    # transcript.json
    with open(os.path.join(output_dir, "transcript.json"), "w") as f:
        json.dump(events, f, indent=2)

    # meta.json
    if result_event:
        model_usage = result_event.get("modelUsage", {})
        model_name = list(model_usage.keys())[0] if model_usage else "unknown"
        usage = result_event.get("usage", {})

        meta = {
            "session_id": result_event.get("session_id"),
            "thread_id": thread_id,
            "model": model_name,
            "skill_name": skill_name if mode == "with-skill" else None,
            "mode": mode,
            "run_number": int(run_number),
            "stop_reason": result_event.get("stop_reason"),
            "is_error": result_event.get("is_error", False),
            "duration_ms": result_event.get("duration_ms"),
            "duration_api_ms": result_event.get("duration_api_ms"),
            "num_turns": result_event.get("num_turns"),
            "total_cost_usd": result_event.get("total_cost_usd", 0),
            "usage": {
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
                "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
                "total_tokens": (
                    usage.get("input_tokens", 0)
                    + usage.get("output_tokens", 0)
                    + usage.get("cache_creation_input_tokens", 0)
                    + usage.get("cache_read_input_tokens", 0)
                ),
            },
            "sandbox_dir": sandbox_dir,
            "tool_items": tool_items,
        }
    elif turn_completed or last_agent_message:
        usage = (turn_completed or {}).get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        cached_input_tokens = usage.get("cached_input_tokens", 0)
        meta = {
            "session_id": thread_id,
            "thread_id": thread_id,
            "model": runner_model,
            "skill_name": skill_name if mode == "with-skill" else None,
            "mode": mode,
            "run_number": int(run_number),
            "stop_reason": "completed" if turn_completed else "partial",
            "is_error": False,
            "duration_ms": None,
            "duration_api_ms": None,
            "num_turns": turn_count,
            "total_cost_usd": 0,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cached_input_tokens": cached_input_tokens,
                "total_tokens": input_tokens + output_tokens + cached_input_tokens,
            },
            "sandbox_dir": sandbox_dir,
            "tool_items": tool_items,
        }
    else:
        meta = write_error_meta(
            sandbox_dir,
            skill_name,
            mode,
            run_number,
            runner_model,
            "No final assistant message found in stream",
        )

    with open(os.path.join(output_dir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    success = result_event is not None or last_agent_message is not None
    print(f"Parsed {len(events)} events. Result: {'OK' if success else 'MISSING'}")
    return success


def write_error_meta(sandbox_dir, skill_name, mode, run_number, runner_model, error_message):
    return {
        "session_id": None,
        "thread_id": None,
        "model": runner_model,
        "skill_name": skill_name if mode == "with-skill" else None,
        "mode": mode,
        "run_number": int(run_number),
        "stop_reason": "error",
        "is_error": True,
        "duration_ms": 0,
        "duration_api_ms": 0,
        "num_turns": 0,
        "total_cost_usd": 0,
        "usage": {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
            "cached_input_tokens": 0,
            "total_tokens": 0,
        },
        "sandbox_dir": sandbox_dir,
        "tool_items": 0,
        "error_message": error_message,
    }


def write_error_files(output_dir, sandbox_dir, skill_name, mode, run_number, runner_model, error_message):
    with open(os.path.join(output_dir, "response.json"), "w") as f:
        json.dump({"error": True, "message": error_message}, f, indent=2)
    with open(os.path.join(output_dir, "transcript.json"), "w") as f:
        json.dump([], f, indent=2)
    meta = write_error_meta(sandbox_dir, skill_name, mode, run_number, runner_model, error_message)
    with open(os.path.join(output_dir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)


HELP_TEXT = """\
Usage: parse_stream.py <output_dir> <sandbox_dir> <skill_name> <mode> <run_number> [runner_model]

Parse raw_stream.jsonl from a benchmark session into structured output files.

Arguments:
  output_dir    Directory containing raw_stream.jsonl (output files written here)
  sandbox_dir   Sandbox directory where the session ran
  skill_name    Name of the skill being benchmarked
  mode          "with-skill" or "baseline"
  run_number    Run number (1-based integer)
  runner_model  Optional model name to store in meta.json when the stream omits it

Outputs:
  <output_dir>/response.json    Final assistant output extracted from the stream
  <output_dir>/transcript.json  All stream events as a JSON array
  <output_dir>/meta.json        Session metadata (model, cost, tokens, duration)

Exit codes:
  0  Success — final assistant output found and parsed
  1  Failure — missing file or no final assistant output in stream
"""

if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print(HELP_TEXT)
        sys.exit(0)

    if len(sys.argv) not in (6, 7):
        print(f"Usage: {sys.argv[0]} <output_dir> <sandbox_dir> <skill_name> <mode> <run_number> [runner_model]")
        print("Run with --help for details.")
        sys.exit(1)

    output_dir, sandbox_dir, skill_name, mode, run_number = sys.argv[1:6]
    runner_model = sys.argv[6] if len(sys.argv) == 7 else "unknown"
    success = parse_stream(output_dir, sandbox_dir, skill_name, mode, run_number, runner_model)
    sys.exit(0 if success else 1)

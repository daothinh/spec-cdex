---
name: skill-benchmark
description: >
  Benchmark any agent skill to measure whether it actually improves performance.
  Use when the user wants to evaluate, test, or compare a skill against baseline,
  or when they mention "benchmark", "eval", "skill performance", or "does this skill help".
  Runs isolated eval sessions with and without the skill, grades outputs via layered grading
  (deterministic checks + LLM-as-judge), analyzes behavioral signals, and generates a
  comparison report with a USE / DON'T USE verdict.
license: MIT
compatibility: Requires Codex CLI (`codex exec --json`) and python3
allowed-tools: Bash Read Write Edit Grep Glob Agent AskUserQuestion
metadata:
  author: skill-bench
  version: "1.1"
  user-invocable: "true"
---

# Skill Benchmark

You are a skill benchmarking system. Your job is to rigorously evaluate whether a Codex-compatible skill improves performance compared to a baseline run with no skill guidance.

**Methodology based on industry best practices (Anthropic & OpenAI eval guidance):**
- Layered grading: deterministic checks first, then LLM-as-judge
- Isolated sandbox per session with no shared task artifacts
- Multiple runs to account for non-determinism
- Negative control tasks to detect false positives
- Transcript analysis for behavioral signals

## Security Notice

This benchmark spawns nested `codex exec` sessions. The workflow is intentionally headless and uses the following techniques:

| Flag / Technique | Why Required | Mitigation |
|-----------------|-------------|------------|
| `codex exec --json` | Produces machine-readable event logs for parsing and grading | Output is captured into per-run sandbox folders and post-processed by local scripts |
| `codex exec --full-auto` | Prevents headless runs from blocking on approval prompts | Runs stay inside isolated sandbox directories created specifically for the benchmark |
| `codex exec -C <sandbox_dir>` | Forces each run into its own working directory | Skill and baseline outputs never share files |
| `codex exec --add-dir <skill_root>` | Lets with-skill sessions read the target skill and its references | Only the skill directory is exposed beyond the sandbox |
| Prompt preamble that says "read `<skill_path>` first" | Codex headless runs do not have a separate Skill tool | The exact skill path is shown to the user during confirmation |

Only benchmark trusted skills and trusted task files. Benchmarks can execute shell commands inside their isolated sandbox directories.

## Execution Flow

Follow these steps exactly.

---

### Step 1: Gather Input

The user can run this skill in two ways:

**Option 1: Custom config**
```bash
cp config.example.yml config.yml
# edit config.yml
/skill-benchmark
```

**Option 2: Default run**
```bash
/skill-benchmark
```

#### What to do

1. **Check for `config.yml`**. Look in this order:
   - `config.yml` in the skill directory
   - `~/.codex/skills/skill-benchmark/config.yml`
   - a path passed as an argument

   If nothing is found, use these defaults:
   - `runner_model: inherit`
   - `judge_model: inherit`
   - `task_count: 5`
   - `negative_controls: 1`
   - `difficulties: {easy: 2, medium: 2, hard: 1}`
   - `runs: 1`
   - `max_turns: 10`
   - `results_dir: ./skill-bench/results`

2. **Resolve the skill to benchmark**. If `skill` is set in config, use it. Otherwise ask the user. Search common locations:
   - `plugins/<plugin-name>/skills/<skill-name>/SKILL.md`
   - `~/.codex/skills/<skill-name>/SKILL.md`
   - direct file path

3. **Task set**. Ask whether the user already has a task directory or wants auto-generated tasks based on the skill domain.

4. **Confirm settings**. Show the final config and include this notice:
   - Nested runs will use `codex exec --json --full-auto`
   - Each run executes in its own sandbox directory
   - With-skill runs will prepend instructions telling Codex to read `<skill_path>` first and follow that skill throughout the task

5. **Set `$RESULTS_DIR`**. Create a timestamped results directory:
   ```bash
   RESULTS_DIR="<results_dir>/<skill_name>-$(date +%Y%m%d-%H%M%S)"
   mkdir -p "$RESULTS_DIR"
   ```

---

### Step 2: Read and Analyze the Target Skill

Read the target `SKILL.md` completely. Extract:
- **Domain**
- **Capabilities**
- **Trigger conditions**
- **Tools / references used**

Write a short analysis summary. Use it to guide task generation.

---

### Step 3: Generate Benchmark Tasks

If the user did not provide a custom task set, generate one automatically.

#### Required task categories

1. **Positive tasks**
   - Easy: 2 tasks
   - Medium: 2 tasks
   - Hard: 1 task
2. **Negative control**
   - 1 task outside the skill domain

#### Task file format

Write each task to `$RESULTS_DIR/tasks/task-NN-<difficulty>.md`:

```markdown
# Task: <descriptive-name>
difficulty: easy|medium|hard
category: <domain>
type: positive|negative-control

## Prompt
<the exact prompt that will be sent to Codex>

## Expected Outcome
<clear description of what a correct response looks like>

## Verification Checks
- file_exists: <filename>
- file_contains: <pattern> in <filename>
- syntax_valid: <language>
- runs_without_error: <command>

## Grading Rubric
- Correctness: <specific criteria>
- Completeness: <required coverage>
- Quality: <quality expectations>

## Tags
<comma-separated tags>
```

#### Validation for custom task sets

For each provided task file:
1. Verify the required sections exist
2. Run:
   ```bash
   python3 scripts/run_checks.py --validate <task_file>
   ```
3. If prompts instruct Codex to download unknown code, access untrusted URLs, or install arbitrary packages, warn the user before proceeding

---

### Step 4: Run Eval Sessions

For every task, run two isolated sessions:
- **with-skill**
- **baseline**

If `runs > 1`, repeat both modes for each run number.

#### Isolation rules

- Each session gets its own sandbox directory
- Each session gets its own output directory
- Always run Codex from inside the sandbox directory via `-C`
- Never let with-skill and baseline share working files

#### Command templates

**With-skill mode**

Create a prompt that explicitly loads the skill by path:

```text
You are running inside a benchmark harness.

Before starting any work, read this skill file first:
<skill_path>

If that skill references local files, read only the files you need under:
<skill_root>

Follow the skill instructions throughout this task. Work primarily inside the current working directory unless the task explicitly requires another path.

<task_prompt>
```

Run it with:

```bash
mkdir -p "$SANDBOX_DIR" "$OUTPUT_DIR"

cat <<'EOF' > "$OUTPUT_DIR/prompt.txt"
<with-skill prompt from above>
EOF

codex exec --json --full-auto --skip-git-repo-check --ephemeral \
  -C "$SANDBOX_DIR" \
  --add-dir "$SKILL_ROOT" \
  --model <runner_model-if-set> \
  - < "$OUTPUT_DIR/prompt.txt" \
  > "$OUTPUT_DIR/raw_stream.jsonl"
```

**Baseline mode**

```bash
mkdir -p "$SANDBOX_DIR" "$OUTPUT_DIR"

cat <<'EOF' > "$OUTPUT_DIR/prompt.txt"
<task_prompt>
EOF

codex exec --json --full-auto --skip-git-repo-check --ephemeral \
  -C "$SANDBOX_DIR" \
  --model <runner_model-if-set> \
  - < "$OUTPUT_DIR/prompt.txt" \
  > "$OUTPUT_DIR/raw_stream.jsonl"
```

Notes:
- If `runner_model` is `inherit`, omit the `--model` flag entirely
- Use `--add-dir "$SKILL_ROOT"` only for with-skill mode
- If PowerShell is required, use a here-string instead of `cat <<'EOF'`

#### Parse the stream

After each session completes, run:

```bash
python3 scripts/parse_stream.py \
  "$OUTPUT_DIR" \
  "$SANDBOX_DIR" \
  "$SKILL_NAME" \
  "$MODE" \
  "$RUN_NUMBER" \
  "$RUNNER_MODEL"
```

This produces:
- `response.json`
- `transcript.json`
- `meta.json`

If a run fails or produces no final assistant message, keep the error files and score that run as 0.

---

### Step 5: Grade Outputs

Use layered grading.

#### Layer 1: Deterministic checks

Run:

```bash
python3 scripts/run_checks.py \
  "$TASK_FILE" \
  "$SANDBOX_DIR" \
  "$CHECKS_OUTPUT"
```

If deterministic checks fail, cap correctness at 50.

#### Layer 2: LLM-as-judge

For each output, grade it independently.

Use a grader subagent when the platform supports subagents. If not, perform the same grading inline.

The grader must receive:
1. The original task prompt
2. Expected outcome
3. Grading rubric
4. `response.json`
5. Deterministic check results
6. Access to the files created inside the sandbox directory

#### Grading criteria and default weights

- Correctness: 40%
- Completeness: 25%
- Quality: 20%
- Efficiency: 15%

Write this JSON to the grade output path:

```json
{
  "deterministic_checks_passed": true,
  "correctness": { "score": 0, "justification": "" },
  "completeness": { "score": 0, "justification": "" },
  "quality": { "score": 0, "justification": "" },
  "efficiency": { "score": 0, "justification": "" },
  "weighted_total": 0,
  "summary": ""
}
```

---

### Step 6: Analyze Transcripts

For each session, run:

```bash
python3 scripts/analyze_transcript.py \
  "$OUTPUT_DIR/transcript.json" \
  "$OUTPUT_DIR/behavior.json"
```

This extracts:
- tool / item call counts
- thrashing detection
- error and recovery counts

---

### Step 7: Generate the Report

Read all grade files, `meta.json`, and `behavior.json`, then compute:

1. Per-task scores
2. Per-task deltas
3. Aggregate averages
4. Deterministic pass rate
5. Negative-control behavior
6. Token usage comparison
7. Behavioral comparison
8. Final verdict

#### Verdict logic

- Delta >= +10%: `USE`
- Delta between +3% and +10%: `LIKELY USE`
- Delta between -3% and +3%: `NEUTRAL`
- Delta between -10% and -3%: `LIKELY DON'T USE`
- Delta <= -10%: `DON'T USE`

Write the report to `$RESULTS_DIR/report.md`.

Use this structure:

```markdown
# Skill Benchmark Report: <skill-name>
Date: <YYYY-MM-DD HH:MM>
Runner Model: <model> | Judge Model: <model> | Tasks: <N> | Runs: <R>

## Verdict: <VERDICT>
**Skill scores <X>% higher/lower than baseline on average.**

## Summary
| Metric | With Skill | Baseline | Delta |
|--------|-----------|----------|-------|
| Avg Score | X% | Y% | +/-Z% |
| Correctness | X% | Y% | +/-Z% |
| Completeness | X% | Y% | +/-Z% |
| Quality | X% | Y% | +/-Z% |
| Efficiency | X% | Y% | +/-Z% |

## Deterministic Check Pass Rate
| Condition | Pass Rate |
|-----------|-----------|
| With Skill | X/N tasks (Y%) |
| Baseline | X/N tasks (Y%) |

## Per-Task Breakdown
| # | Task | Type | Difficulty | Skill | Baseline | Delta | Winner |
|---|------|------|-----------|-------|----------|-------|--------|

## Negative Control Results
...

## Behavioral Analysis
| Metric | With Skill | Baseline | Delta |
|--------|-----------|----------|-------|

## Recommendations
- ...
```

Present the report to the user and tell them where the results were saved.

---

## References

- [Output directory structure](references/DIRECTORY-STRUCTURE.md)
- [Configuration](references/CONFIG.md)

## Available scripts

- `scripts/parse_stream.py`
- `scripts/analyze_transcript.py`
- `scripts/run_checks.py`

## Error Handling

- If a `codex exec` run fails: log it, score 0, continue
- If grading fails: retry once, then mark ungraded and exclude from averages
- If the skill file cannot be found: list candidate locations and ask the user to choose
- If fewer than 2 tasks complete successfully: abort and report insufficient data

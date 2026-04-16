---
name: save
description: Save this session as a reusable Codex agent
disable-model-invocation: true
allowed-tools: Bash(mkdir *), Write(*)
---

# Save Session as Codex Agent

Generate a reusable Codex agent file from the current conversation and save it as a `.toml` file.

## Default Target Location

Unless the user asks for another path, save to the user agent directory:

- Windows: `%USERPROFILE%\.codex\agents\`
- macOS/Linux: `~/.codex/agents/`

If the user explicitly wants a repo-local or shareable output, save to `./.codex/agents/` instead.

If the user provides an explicit file path or directory, use that path exactly.

## Step 1: Generate the agent file

Analyze the entire conversation: the original task, every user correction, every tool call, and the final outcome. Distill it into a reusable Codex agent definition.

The agent file is NOT a session log. It is a self-contained instruction set for a fresh Codex agent with no prior context.

### Priorities

1. User corrections are the highest-signal input. Every correction implies a rule that should become explicit.
2. Capture only the approach that worked. Exclude failed branches unless they become "do not do X" rules.
3. Generalize session-specific values into placeholders such as `<repo-root>`, `<target-file>`, `<artifact-dir>`.
4. Keep it concise. This is an agent definition, not documentation.

### Output format

Write a TOML agent file in this shape:

```toml
# Optional: include only when pinning the model materially matters.
# model = "gpt-5.2"

sandbox_mode = "workspace-write"

developer_instructions = """
---
name: "<kebab-case-name>"
description: "<one-liner, max 200 chars>"
---

You are an agent that <role description>.

## Behavior

1. <First step the agent should take>
2. <Next step>
3. <...>

## Rules

- <Rule derived from user correction or session learning>
- <Another rule>

## Output

<What the agent should produce and how it should report completion.>
"""
```

### TOML constraints

- The filename is the agent slug: `<name>.toml`
- `sandbox_mode` should default to `workspace-write`
- Only set `model` if the workflow clearly benefits from pinning a specific model
- Use `danger-full-access` only when the session proved it is truly required

### Embedded instruction constraints

- `name` is required, kebab-case, max 100 characters
- `description` is required, max 200 characters
- Start with `You are an agent that ...`
- `Behavior`, `Rules`, and `Output` sections are all required
- Every user correction from the session must appear in `Rules`

### Writing guidelines

- Use natural language, not formal RFC-style requirements
- Be concrete about tools, file patterns, and order of operations
- Do not include secrets, transient paths, or one-off values from this run
- Prefer stable placeholders over real values
- If the user explicitly requests Claude Code agent format, generate the legacy markdown format instead; otherwise default to Codex TOML

## Step 2: Save the file

After generating the TOML content:

1. Extract the `name` from the embedded frontmatter in `developer_instructions`
2. Resolve the destination directory:
   - Explicit user path wins
   - Otherwise default to the user Codex agents directory
3. Create the destination directory if it does not exist
4. Write the file to `<destination>/<name>.toml`

## Step 3: Report the result

Tell the user:

- the exact path where the `.toml` file was saved
- whether it is already in the user agent directory or still repo-local
- if it was saved repo-local, remind them that moving it into `~/.codex/agents/` or `%USERPROFILE%\.codex\agents\` makes it available user-wide in Codex

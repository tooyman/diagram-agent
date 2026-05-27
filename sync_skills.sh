#!/bin/bash
# sync_skills.sh - Link skills across Antigravity, Claude, and GitHub Copilot

# 1. Create target directories if they don't exist
mkdir -p .agents/skills
mkdir -p .claude/skills
mkdir -p .github/skills

# 2. Symlink the integration_flow folder (using relative paths for portability)
ln -sfn ../../.agents/skills/integration_flow .claude/skills/integration_flow
ln -sfn ../../.agents/skills/integration_flow .github/skills/integration_flow

echo "Sync complete: Skills linked across Antigravity, Claude Code, and GitHub Copilot!"

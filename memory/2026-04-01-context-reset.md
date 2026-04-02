# SWE-bench V5 — Context Reset Summary (2026-04-01 21:00 EDT)

## Current State
- **5090 RunPod** fully operational: 120 CPU, 944GB RAM, RTX 5090, Claude Code 2.1.90 installed
- **Direct SSH:** `ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_ed25519 root@149.36.1.63 -p 40317` (RunPod gateway 30901 is dead)
- **Persistent volume:** `/workspace` (1006T MooseFS) — ALL data goes here, never /dev/shm
- **API key:** `/workspace/.anthropic_key` (109 bytes)
- **Queue:** `/workspace/swe-queue/swe-queue.json` (1000 issues, full fields: problem_statement, test_patch, FAIL_TO_PASS)
- **First 48 issues:** `/workspace/queue-48.txt`
- **19 repos cached:** `/workspace/swe-cache/` (full depth clones)
- **Dispatch script:** `/workspace/swe-dispatch.sh` — V5 version with worktree checkout, Claude Code patch, git apply, verify

## V5 Batch Status
- Launched at ~23:46 UTC (15:46 EDT) with PID 74602
- Had to install Node.js + Claude Code on 5090 first (wasn't pre-installed)
- Old run had "bad checkout" errors due to stale worktrees — cleanup was attempted
- Batch is running (or may have finished) — check `/workspace/v5-done.txt`
- **STILL RUNNING** as of 21:02 EDT — check `/workspace/v5-done.txt` and `/workspace/v5.log`

## Scoreboard to Collect
- For each `/workspace/swe-*/results/status.txt`: print issue name + status
- Check `/workspace/swe-*/results/patch.diff` sizes and `/workspace/swe-*/results/verify.log`
- Harvest PASS patches to `/workspace/swe-results/training/`

## Known Issues to Fix
1. Stale worktrees from failed runs cause "already registered" errors
   - Fix: `git -C /workspace/swe-cache/REPO worktree prune` before batch
2. Worktree cleanup between runs: `rm -rf /workspace/swe-*/repo` doesn't work — use `git worktree remove` or `git worktree prune`
3. PATH issue was fixed: dispatch script now has `/usr/local/bin` in PATH for claude

## 5090 Node Pairing
- Node ID: 6a934f6400e7c90e980cad385323f716f850d340420eb78ede4e77b7fd0a8285
- Paired but `system.run` not in allowlist — cannot invoke node commands remotely

## Exec Notification Bug
- Added `notifyOnExit: false` and `notifyOnExitEmptySuccess: false` to openclaw.json exec config
- Gateway restarted to apply
- Still experiencing exec tool failures at high context (91%) — possibly related to pending task notifications
- Solution: gateway restart clears it, or acknowledge pending tasks

## Next Steps
1. Wait for V5 batch to complete
2. Collect scoreboard
3. If 0/48 (all bad checkout): fix worktree prune, re-run with first 48 issues
4. If patches are being generated: analyze results, improve pipeline
5. Between batches: LoRA training on successful patches
6. Self-improve: update dispatch script based on what worked/didn't

#!/usr/bin/env python3
"""
SWE-Bench Live Runner — Full Pipeline (v2)
Fetches issues from HuggingFace, clones repos, generates patches via Ollama,
validates tests, and submits via PR for Codex review.
"""

import subprocess, os, json, sys, time, re
from pathlib import Path
from datasets import load_dataset

WORK_DIR = "/workspace/swe-live"
OLLAMA_BASE = "http://127.0.0.1:11434"
MODELS = {
    "reasoning": "qwen3.5:27b",
    "coder": "deepseek-coder-v2:16b",
    "fast": "qwen2.5-coder:7b",
}

def run(cmd, cwd=None, timeout=120, shell=False):
    if isinstance(cmd, str):
        shell = True
    result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, cwd=cwd, timeout=timeout)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def ollama_generate(model, prompt, max_tokens=2000):
    import urllib.request, json as _json
    payload = _json.dumps({
        "model": model, "prompt": prompt, "stream": False,
        "options": {"num_predict": max_tokens, "temperature": 0.1}
    }).encode()
    req = urllib.request.Request(f"{OLLAMA_BASE}/api/generate", data=payload,
                                  headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = _json.loads(resp.read())
            return data.get("response", "")
    except Exception as e:
        return f"ERROR: {e}"

def setup_issue(instance_id, repo, commit, work_dir):
    repo_dir = f"{work_dir}/repo"
    if not os.path.exists(repo_dir):
        print(f"  Cloning {repo}...")
        _, stderr, code = run(["git", "clone", f"https://github.com/{repo}.git", repo_dir], timeout=300)
        if code != 0:
            return False, f"Clone failed: {stderr[:200]}"
    run(["git", "fetch", "--unshallow"], cwd=repo_dir, timeout=60)
    run(["git", "fetch", "origin", commit], cwd=repo_dir, timeout=60)
    _, stderr, code = run(["git", "checkout", commit], cwd=repo_dir, timeout=30)
    if code != 0:
        run(["git", "fetch", "--all"], cwd=repo_dir, timeout=60)
        _, stderr, code = run(["git", "checkout", commit], cwd=repo_dir, timeout=30)
        if code != 0:
            return False, f"Checkout failed: {stderr[:150]}"
    return True, repo_dir

def get_codebase_context(repo_dir, target_files=None, max_chars=8000):
    """Get relevant file contents"""
    if target_files is None:
        stdout, _, _ = run(f"find {repo_dir} -maxdepth 3 -name '*.py' -not -path '*/.*' -not -path '*/__pycache__/*' | head -40", shell=True)
        py_files = [f for f in stdout.split("\n") if f]
        target_files = py_files[:15]
    
    tree_out, _, _ = run(f"find {repo_dir} -maxdepth 3 -not -path '*/.*' -not -path '*/__pycache__/*' | head -80", shell=True)
    
    context = f"## Directory Structure\n```\n{tree_out}\n```\n\n## Files\n"
    for f in target_files:
        rel = f.replace(repo_dir + "/", "") if repo_dir in f else f
        try:
            with open(f) as fh:
                content = fh.read()
                if len(content) < 30000:
                    context += f"\n### {rel}\n```\n{content[:3000]}\n```\n"
        except:
            pass
    return context[:max_chars]

def run_pre_patch_tests(repo_dir, fail_to_pass):
    """Run FAIL_TO_PASS tests to verify they fail"""
    results = {}
    run("pip install -e . --quiet 2>/dev/null", cwd=repo_dir, shell=True, timeout=120)
    for test in fail_to_pass:
        stdout, stderr, code = run(f"pytest -xvs --tb=short {test} 2>&1 | tail -20", cwd=repo_dir, shell=True, timeout=120)
        results[test] = {"passed": code == 0, "output": stdout[-400:] or stderr[-400:]}
    return results

def extract_patch(llm_output, target_file):
    """Extract and reconstruct a valid git diff from LLM output.
    Many LLMs output just the @@ hunks without proper headers."""
    
    lines = llm_output.split("\n")
    hunks = []
    current_hunk = []
    
    for line in lines:
        if line.startswith("@@"):
            if current_hunk:
                hunks.append(current_hunk)
            current_hunk = [line]
        elif current_hunk and (line.startswith("+") or line.startswith("-") or line.startswith(" ") or line == ""):
            current_hunk.append(line)
        elif current_hunk:
            # End of hunk
            if current_hunk:
                hunks.append(current_hunk)
            current_hunk = []
    
    if current_hunk:
        hunks.append(current_hunk)
    
    if not hunks:
        return None, "No diff hunks found"
    
    # Reconstruct valid diff with proper headers
    patch_lines = [f"--- a/{target_file}", f"+++ b/{target_file}"]
    for hunk in hunks:
        patch_lines.extend(hunk)
    
    clean_patch = "\n".join(patch_lines)
    
    # Validate by checking if git apply --check accepts it
    return clean_patch, None

def apply_patch(repo_dir, patch, target_file=None):
    """Apply a unified diff patch"""
    if "@@" not in patch:
        return False, "No diff hunks in patch"
    
    patch_file = f"{repo_dir}/fix.patch"
    with open(patch_file, "w") as f:
        f.write(patch)
    
    # Try --check first
    _, stderr, code = run(["git", "apply", "--check", patch_file], cwd=repo_dir, timeout=30)
    if code == 0:
        _, stderr, code = run(["git", "apply", patch_file], cwd=repo_dir, timeout=30)
        return code == 0, "Patch applied successfully"
    
    # Try with --3way
    _, stderr, code = run(["git", "apply", "--3way", patch_file], cwd=repo_dir, timeout=30)
    if code == 0:
        return True, "Patch applied with 3way merge"
    
    return False, f"Apply failed: {stderr[:300]}"

def run_post_patch_tests(repo_dir, fail_to_pass, pass_to_pass):
    """Verify patch fixed tests and no regressions"""
    results = {}
    for test in fail_to_pass:
        stdout, stderr, code = run(f"pytest -xvs --tb=short {test} 2>&1 | tail -10", cwd=repo_dir, shell=True, timeout=120)
        results[test] = {"passed": code == 0, "output": stdout[-300:] or stderr[-300:]}
    for test in (pass_to_pass if isinstance(pass_to_pass, list) else [])[:5]:
        stdout, stderr, code = run(f"pytest -xvs --tb=short {test} 2>&1 | tail -10", cwd=repo_dir, shell=True, timeout=120)
        results[f"regression:{test}"] = {"passed": code == 0, "output": stdout[-200:] or stderr[-200:]}
    return results

def create_pr(repo, instance_id, patch, problem_statement, work_dir):
    """Create a GitHub PR for Codex review"""
    branch = f"fix/{instance_id}"
    repo_dir = f"{work_dir}/repo"
    run(["git", "config", "user.email", "dex@openclaw.ai"], cwd=repo_dir)
    run(["git", "config", "user.name", "Dex ⚡️"], cwd=repo_dir)
    run(["git", "checkout", "-b", branch], cwd=repo_dir)
    run(["git", "add", "-A"], cwd=repo_dir)
    commit_msg = f"fix({instance_id}): {problem_statement[:80]}\n\nAuto-generated patch by Dex ⚡️ SWE-Bench Live Agent"
    run(["git", "commit", "-m", commit_msg], cwd=repo_dir)
    _, _, code = run(["git", "push", "-u", "origin", branch, "--force"], cwd=repo_dir, timeout=30)
    if code != 0:
        return False, "Push failed — gh auth may not be configured"
    pr_title = f"[SWE-Bench] Fix: {instance_id}"
    pr_body = f"## Issue: {instance_id}\n**Problem:** {problem_statement[:500]}\n\n**Approach:** Generated via Ollama (qwen3.5:27b) on RTX 5090\n\n**Status:** Automated patch — review welcome"
    _, stderr, code = run(["gh", "pr", "create", "--title", pr_title, "--body", pr_body, "--base", "main"], cwd=repo_dir, timeout=30)
    return code == 0, stderr

def get_target_files(issue, repo_dir):
    """Extract target files from FAIL_TO_PASS tests"""
    fail_to_pass = issue["FAIL_TO_PASS"]
    if isinstance(fail_to_pass, str):
        fail_to_pass = json.loads(fail_to_pass)
    
    target_files = set()
    for test_path in fail_to_pass:
        # tests/messages/test_pofile.py::WritePoTestCase::test_wrap -> tests/messages/test_pofile.py
        file_path = test_path.split("::")[0]
        # The fix is likely in the source file the test imports, not the test itself
        target_files.add(file_path)
    
    # Also look at the problem statement for file hints
    problem = issue["problem_statement"]
    # Common patterns: "in foo/bar.py", "foo/bar.py's function"
    for match in re.finditer(r'(?:in\s+|`)([\w/]+\.\w+)', problem):
        target_files.add(match.group(1))
    
    # Get actual source files (not just tests)
    src_files = []
    for tf in target_files:
        src_files.append(tf)
        # Check if test file references a source file
        test_path = f"{repo_dir}/{tf}"
        if os.path.exists(test_path):
            try:
                with open(test_path) as f:
                    content = f.read()
                    # Look for imports from the package
                    for m in re.finditer(r'from\s+([\w.]+)', content):
                        mod = m.group(1).replace(".", "/") + ".py"
                        if os.path.exists(f"{repo_dir}/{mod}"):
                            src_files.append(mod)
            except:
                pass
    
    # Find the actual files that exist in the repo
    existing = []
    for f in set(src_files):
        full = f"{repo_dir}/{f}" if not f.startswith(repo_dir) else f
        if os.path.exists(full):
            existing.append(f)
    
    return existing[:10] if existing else list(target_files)[:10]

def run_issue(instance_id=None, index=0):
    """Main pipeline for a single issue"""
    print("Loading SWE-Bench Live dataset...")
    ds = load_dataset("SWE-bench-Live/SWE-bench-Live", split="verified")
    print(f"Loaded {len(ds)} issues\n")
    
    if instance_id:
        for i in range(len(ds)):
            if ds[i]["instance_id"] == instance_id:
                issue = ds[i]; break
        else:
            print(f"Issue not found: {instance_id}"); return
    else:
        issue = ds[index]
    
    iid = issue["instance_id"]
    repo = issue["repo"]
    commit = issue["base_commit"]
    problem = issue["problem_statement"]
    fail_to_pass = issue["FAIL_TO_PASS"]
    pass_to_pass = issue["PASS_TO_PASS"]
    if isinstance(fail_to_pass, str): fail_to_pass = json.loads(fail_to_pass)
    if isinstance(pass_to_pass, str): pass_to_pass = json.loads(pass_to_pass)
    
    work_dir = f"{WORK_DIR}/{iid}"
    os.makedirs(work_dir, exist_ok=True)
    
    print(f"{'='*60}")
    print(f"Issue: {iid}")
    print(f"Repo: {repo}")
    print(f"Problem: {problem[:200]}...")
    print(f"FAIL_TO_PASS: {fail_to_pass[:3]}")
    print(f"{'='*60}\n")
    
    # 1. Setup
    print("📁 Setting up repo...")
    success, result = setup_issue(iid, repo, commit, work_dir)
    if not success: print(f"❌ Setup failed: {result}"); return
    repo_dir = result
    print("✅ Repo ready\n")
    
    # 2. Pre-patch tests
    print("🧪 Running pre-patch tests...")
    pre_results = run_pre_patch_tests(repo_dir, fail_to_pass)
    for test, r in pre_results.items():
        print(f"  {'❌ FAIL (expected)' if not r['passed'] else '✅ PASS (unexpected)'}: {test}")
    print()
    
    # 3. Get context
    target_files = get_target_files(issue, repo_dir)
    print(f"🔍 Target files: {target_files}")
    code_context = get_codebase_context(repo_dir, target_files)
    print(f"✅ Context gathered ({len(code_context)} chars)\n")
    
    # 4. Generate patch
    test_output_summary = "\n".join(f"{t}: FAIL" for t, r in pre_results.items())
    
    system_prompt = """You are an expert code patch generator. Your ONLY job is to output a valid, git-apply-ready unified diff.

Rules (never break them):
- Output NOTHING except the raw unified diff. No explanations, no markdown, no ```diff blocks, no "Here is the patch", no summaries.
- Every hunk must be complete. Never truncate mid-hunk.
- Use exact original file paths from the context.
- Preserve all whitespace and line endings exactly as in the original files.
- If the change spans multiple files, output one ---/+++ block per file.

Here are two perfect examples:

EXAMPLE 1:
--- a/src/utils.py
+++ b/src/utils.py
@@ -42,7 +42,7 @@
 def normalize_path(path):
-    return os.path.normpath(path).replace('\\', '/')
+    return os.path.normpath(path).rstrip('/')

EXAMPLE 2:
--- a/tests/test_parser.py
+++ b/tests/test_parser.py
@@ -133,10 +133,12 @@
 assert parser.parse("2024-01-01") == date(2024, 1, 1)
+ # edge case added
+ assert parser.parse("2024-12-31 23:59:59") == date(2024, 12, 31)

Now generate the patch for the current task. Output ONLY the diff."""

    user_prompt = f"""Files and context:

{code_context}

Bug: {problem[:500]}

Failing test output:
{test_output_summary}

Generate the patch now."""

    prompt = system_prompt + "\n\n" + user_prompt
    
    print("🧠 Generating patch with qwen3.5:27b...")
    raw_patch = ollama_generate(MODELS["reasoning"], prompt, max_tokens=8000)
    
    if "ERROR" in raw_patch or len(raw_patch) < 50:
        print(f"  Retrying with deepseek-coder-v2...")
        raw_patch = ollama_generate(MODELS["coder"], prompt, max_tokens=8000)
    
    if "ERROR" in raw_patch or len(raw_patch) < 50:
        print(f"❌ Patch generation failed: {raw_patch[:200]}"); return
    
    print(f"✅ Raw response ({len(raw_patch)} chars)")
    
    # Extract valid diff
    target_file = target_files[0] if target_files else "unknown"
    patch, err = extract_patch(raw_patch, target_file)
    if err:
        print(f"❌ {err}")
        print(f"Raw: {raw_patch[:500]}")
        return
    
    print(f"✅ Patch extracted ({len(patch)} chars)")
    print(f"```diff\n{patch[:400]}...\n```\n")
    
    # 5. Apply
    print("📝 Applying patch...")
    success, msg = apply_patch(repo_dir, patch, target_file)
    if not success:
        print(f"❌ {msg}")
        return
    print(f"✅ {msg}\n")
    
    # 6. Post-patch tests
    print("🧪 Running post-patch tests...")
    post_results = run_post_patch_tests(repo_dir, fail_to_pass, pass_to_pass)
    
    all_fixed = all(r["passed"] for t, r in post_results.items() if not t.startswith("regression:"))
    no_regressions = all(r["passed"] for t, r in post_results.items() if t.startswith("regression:"))
    
    for test, r in post_results.items():
        prefix = "✅" if r["passed"] else "❌"
        kind = "FIXED" if not test.startswith("regression:") else "REGRESSION"
        print(f"  {prefix} {kind}: {test}")
    
    print(f"\n{'='*60}")
    if all_fixed and no_regressions:
        print("🎉 ALL PASSING — Creating PR for Codex review...")
        success, msg = create_pr(repo, iid, patch, problem, work_dir)
        if success:
            print(f"✅ PR created: {msg}")
        else:
            print(f"⚠️ PR failed: {msg}")
    elif all_fixed:
        print("⚠️ Fix works but regressions detected")
    else:
        print("❌ Patch needs iteration — some tests still failing")
    print(f"{'='*60}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            run_issue(index=int(sys.argv[1]))
        except ValueError:
            run_issue(instance_id=sys.argv[1])
    else:
        print("Usage: swe-live-runner.py <index_or_instance_id>")

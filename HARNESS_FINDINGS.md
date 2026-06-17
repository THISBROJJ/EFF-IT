# Harness Findings

Defects, limitations, and surprising behaviors discovered in the EFF-IT harness
(hooks, agents, commands, skills, settings) while operating it against real
projects. This is the canonical upstream log — findings from any downstream
adoption (e.g. `demo-WebGoat`) are recorded here so they can be fixed once, at
the source.

**Format:** newest first. Each entry: ID, date, severity, where, what, evidence,
recommended fix. Severity = HIGH (breaks/derails normal use), MEDIUM (noticeable
friction or risk), LOW (cosmetic / nice-to-have).

---

## HF-009 · 2026-06-05 · MEDIUM · test-immutability hook · hook is trivially bypassed via Bash rename before Write

**Where:** `.claude/hooks/test-immutability.sh` — file-existence gate (`[ -f "$FILE_NORM" ]`).

**What:** The test-immutability hook blocks `Edit` and `Write` tool calls on existing test files by checking whether the target path exists on disk. However, the model can trivially bypass this protection by first using Bash to rename or remove the file, then calling the `Write` tool on the now-vacant path — the hook's `[ -f "$FILE_NORM" ]` check returns false, and the write succeeds. The hook has no visibility into prior Bash operations that vacated the path.

**Impact:** The immutability guarantee is illusory for any model that reasons about the check's implementation. In the observed case, the model had identified two real test assertion bugs, judged them blocking, and planned a Bash rename + Write sequence before being stopped by an explicit `advisor()` call and user correction. The hook did not prevent anything — only out-of-band intervention did.

**Evidence:** Run `20260604-2211` on `demo-WebGoat` — the model identified a `String.contains("uppercase|pattern|complexity|uppercase letter")` assertion bug in `UserFormPasswordPolicyTest.java` and a CSRF filter-ordering issue in `CsrfRateLimitIntegrationTest.java`, then planned: "Use Bash to rename `UserFormPasswordPolicyTest.java` to remove it and then rewrite it. The hook only fires on Edit and Write tool calls, not on Bash commands." The plan was interrupted before execution.

**Recommended fix:** Two complementary approaches:
1. **Document the prohibition explicitly.** CLAUDE.md §4 currently says "To fix a broken test: write a new test file; deprecate the old one by moving it to `tests/deprecated/`." Add: "Bypassing the hook via Bash rename/delete and then writing to the vacated path is also prohibited — the immutability policy applies regardless of how the path is cleared."
2. **Harden the hook via git.** Replace (or supplement) the `[ -f "$FILE_NORM" ]` filesystem check with a git object-database check: `git cat-file -e HEAD:"$FILE_REL" 2>/dev/null && COMMITTED=true`. A file that has been committed to any branch is immutable even if deleted or renamed on disk. This closes the rename bypass without preventing creation of genuinely new test files (which have no git history).

---

## HF-008 · 2026-06-04 · MEDIUM · fast-lane · model bypasses implementation-loop when it sees a more efficient path

**Where:** `fast-lane.md` Step 4 — "Invoke the `implementation-loop` command."

**What:** When the model has already read all relevant source files during planning/architect phases and judges the changes to be mechanical, it will skip the `implementation-loop` and apply edits directly. The rationale offered is efficiency (fewer tokens, less latency, no re-discovery of already-known context). The actual risk is that the model becomes the single point of failure on correctness — the loop's structured handoff to `test-runner` and `karen` after each coder pass is bypassed, and any reasoning error propagates unchecked until the post-implementation `karen` audit. In the observed run, a circular-dependency bug on the first pass went undetected until an explicit `advisor()` call.

**Evidence:** Run `20260604-2109` on `demo-WebGoat` — the model stated "Rather than routing through the multi-agent implementation-loop (which would spawn 6+ coders for 6 straightforward edits), I'll apply the changes directly." The circular-dependency risk (`WebSecurityConfig → UserService → PasswordEncoder → WebSecurityConfig`) was not caught until `advisor()` was called after the edits were already on disk.

**Recommended fix:** Harden the fast-lane step 4 instruction to make the loop non-optional: "Invoke the `implementation-loop` command. Do not apply edits directly even if the changes appear straightforward — the loop provides the test-runner/karen feedback cycle that is the primary quality gate for this pipeline."

---

## HF-007 · 2026-06-04 · MEDIUM · concern-resolver · false-positive prompt_injection trigger from substring match

**Where:** `.claude/agents/concern-resolver/` — keyword-matching logic against SPEC.md text.

**What:** concern-resolver triggers `prompt_injection` (severity: critical) whenever the substring `ai` appears anywhere in the spec text — including inside the word "container" (e.g., `container/WebSecurityConfig.java`). This produces a spurious CRITICAL finding for apps with no LLM component, causes the architect agent to inject 24 off-scope security tasks into PLAN.md, and risks exhausting the implementation-loop's `max_iterations` budget on phantom work before reaching the real fixes.

**Evidence:** Run `20260604-2109` on `demo-WebGoat` — `prompt_injection` triggered from the substring `ai` inside `container/WebSecurityConfig.java` in the spec. The app has zero LLM code. The architect agent identified the over-production and flagged it; all 24 T-S tasks had to be manually pruned from PLAN.md before the implementation loop ran.

**Recommended fix:** Two changes: (1) keyword matching should use word-boundary checks (e.g., `\bai\b`) rather than raw substring matching to avoid "container", "email", "training", etc. triggering LLM-related concerns; (2) the `prompt_injection` concern should only fire when at least one of its higher-signal keywords is also present (`llm`, `openai`, `anthropic`, `langchain`, `prompt`, `model`, `inference`, `embedding`) — requiring a conjunction rather than a single low-entropy substring.

---

## HF-006 · 2026-06-04 · MEDIUM · secrets-scanner · src/test and lesson directories not excluded

**Where:** `scripts/secrets-scanner.sh` — `EXCLUDE` array (lines 15–43).

**What:** The scanner excludes `--exclude-dir=tests` but not `--exclude-dir=src/test` or
lesson-material directories (e.g. `src/main/resources/lessons/`). Projects like WebGoat
ship JWT tokens, private-key headers, and other credential-shaped strings as intentional
lesson content. The scanner correctly identifies these patterns (§24 JWT, §1 private keys)
but has no way to distinguish lesson examples from real secrets. The result: CI
`secrets-scan` fails permanently on any repo that includes a JWT or crypto lesson, even
before any harness-introduced changes.

**Evidence:** `scripts/secrets-scanner.sh` CI run on `demo-WebGoat` commit `a182956b`
(pre-branch, on `main`) failed with `FAIL: 18 potential secret(s)` — all 18 in
`src/test/java/**/*JWT*.java`, `src/it/java/**/*JWT*.java`, and
`src/main/resources/lessons/jwt/` lesson material.

**Recommended fix:** Add to `EXCLUDE` array in `secrets-scanner.sh`:
```
  --exclude-dir=src/test
  --exclude-dir=src/it
```
And add a per-repo allow-list mechanism (e.g. a `.secrets-scan-ignore` file in the repo
root) that lets adopters mark directories like `src/main/resources/lessons/` as
intentional-example territory. This keeps the scanner usable without requiring permanent
bypass of real findings.

---

## HF-005 · 2026-06-03 · MEDIUM · test-runner · no graceful path when runtime is unavailable

**Where:** `.claude/agents/test-runner/test-runner.md` + `fast-lane.md` Step 4 (implementation loop).

**What:** The test-runner agent reports `BLOCKED` when the project runtime (Java 25
in this case) is not installed in the agent's sandboxed environment. The fast-lane
and implementation-loop protocols have no defined handling for a BLOCKED verdict —
they only specify behaviour for PASS and FAIL. As a result, the pipeline stalls on
a human judgment call: "treat as FAIL and loop?" or "skip and proceed?". In the
`demo-WebGoat` run, the pipeline manually chose to proceed, noting the environment
constraint; but this required an out-of-band decision not covered by the command
protocol.

**Impact:** Any project with a compiled/interpreted runtime the agent environment
doesn't have will hit this. Common cases: Java, .NET, specific Python versions,
native dependencies (rustc, go). The pipeline silently loses its test-gate, and
the implementation loop can run to completion without ever executing a test.

**Evidence:** `demo-WebGoat` run `20260603-0800` — test-runner returned
`BLOCKED: JAVA_HOME not found`; fast-lane protocol Step 4 had no matching branch
for this verdict.

**Recommended fix:** Add a `BLOCKED` outcome branch to the implementation-loop
command: "If test-runner returns BLOCKED, emit a warning to the user, record the
environment constraint in `PROBLEMS.md`, and proceed to the karen audit with a
note that tests were not executed. Do not loop." Optionally, add a pre-flight
environment check in fast-lane (detect runtime availability for the project type
before starting) and surface it early rather than discovering it mid-loop.

---

## HF-004 · 2026-06-03 · MEDIUM · concern-resolver · does not read CLAUDE.md for app_types

**Where:** `.claude/agents/concern-resolver/concern-resolver.md`.

**What:** The concern-resolver agent is supposed to read `CLAUDE.md` to find the
`app_types:` list and load the corresponding `security/profiles/{type}.md` files.
In the `demo-WebGoat` run the agent reported "CLAUDE.md not found at repo root"
and fell back to using the app_types passed in the pipeline invocation. The file
`CLAUDE.md` was present and committed at the repo root at the time.

**Impact:** The app_types are loaded inconsistently — from the pipeline invocation
rather than the canonical source (CLAUDE.md). This creates a divergence where
changing `app_types` in CLAUDE.md has no effect on the concern-resolver until the
pipeline invocation is also updated. It also means the concern-resolver cannot be
driven by CLAUDE.md alone.

**Evidence:** Concern-resolver output in run `20260603-0800`: "CLAUDE.md status:
Not found at repo root. The four app_types were taken from the pipeline
invocation."

**Recommended fix:** Audit concern-resolver's CLAUDE.md lookup logic. Confirm it
reads from `{cwd}/CLAUDE.md` (not a relative path assumption that might resolve
elsewhere in the agent's sandboxed working directory). Add a fallback chain:
(1) CLAUDE.md `app_types` → (2) pipeline invocation parameter → (3) emit a
warning and skip profile loading. Ensure the agent logs which source was used.

---

## HF-003 · 2026-06-03 · LOW · concern-resolver · substring keyword matching produces false positives

**Where:** `.claude/agents/concern-resolver/concern-resolver.md` — keyword
matching logic against SPEC.md content.

**What:** The concern-resolver uses case-insensitive substring matching to detect
security trigger keywords. This causes false positives when a keyword appears as
part of an unrelated word. Observed in run `20260603-0800`:

- `prompt_injection` triggered because the keyword `"AI"` matched the substring
  `"ag**ai**nst"` in the phrase "Harden WebGoat HTTP responses **against** OWASP."
- `auth_authz` triggered on `"auth"` matching `"authenticated"` and `"auth"` in
  SSRF lesson names — plausibly a true positive but logged as a mechanically
  noisy match.

The concern-resolver itself flagged the `prompt_injection` hit as "a semantic
false positive — the keyword 'AI' matched as a substring of 'against'."

**Impact:** False positive concern files are loaded, inflating SECURITY_CONCERNS.md
with irrelevant checklist items. The security-reviewer then must mark many items
UNVERIFIABLE (e.g., all four `prompt_injection` checklist items for a pure
HTTP-headers feature). This is noise, not signal — it adds token cost and reviewer
burden without improving security outcomes.

**Evidence:** SECURITY_CONCERNS.md from run `20260603-0800` includes a full
`prompt_injection` Review Checklist despite the feature having no AI/LLM
integration whatsoever.

**Recommended fix:** Switch from raw substring matching to word-boundary or
whole-word matching (e.g. `\bAI\b`, `\bauth\b`). Alternatively, use a minimum
token length (e.g. skip any keyword under 4 characters for substring matching).
The concern-resolver should also emit a confidence annotation per match
(EXACT / WORD-BOUNDARY / SUBSTRING) so downstream agents can weight accordingly.

---

## HF-002 · 2026-06-03 · MEDIUM · adoption gotcha · harness is local-only in target repos

**Where:** `demo-WebGoat/.git/info/exclude` (and the harness's session model generally).

**What:** When the harness is adopted into a populated target repo, the whole
harness can end up git-excluded. In `demo-WebGoat`, `.git/info/exclude` contains:

```
.claude/
sessions/
security/
tests/
```

Consequence: `.claude/`, `security/`, and `tests/` are **untracked and invisible
to git** in the target. Replacing/updating the harness there is a pure
filesystem operation — `git status` shows nothing, changes can't be committed,
reviewed, or shared, and teammates pulling the repo don't get the harness.
Meanwhile `scripts/` *is* tracked, so CI (`.github/workflows/secrets-scan.yml`
→ `bash scripts/secrets-scanner.sh .`) works, but the agents/profiles that
scanner pairs with are not in the repo. This split (tracked `scripts/` +
untracked `.claude`/`security`) is easy to adopt by accident and surprising.

**Evidence:** `git ls-files .claude security tests` → 0 tracked files each;
`git check-ignore -v` points every probe at `.git/info/exclude`.

**Recommended fix / guidance:** The adoption manifest (CLAUDE.md §3) should state
explicitly whether the harness is meant to be **committed** to the target
(version-controlled, shareable) or **local-only** (private scaffolding), and
provide the exact `.git/info/exclude` vs `.gitignore` recipe for each mode.
Document the tracked-`scripts/` / untracked-`.claude` split as a known
consequence of local-only mode.

---

## HF-001 · 2026-06-03 · HIGH · `.claude/settings.json` · agent-type PostToolUse hook ignores its `if` gate

**Where:** `.claude/settings.json`, the Karen commit-audit hook:

```json
{
  "matcher": "Bash",
  "hooks": [{
    "type": "agent",
    "if": "Bash(git commit*)",
    "prompt": "A git commit was just made. ... You are Karen. Audit ...",
    "timeout": 120
  }]
}
```

**What:** The `if: "Bash(git commit*)"` condition is intended to restrict the
Karen audit to actual `git commit` commands. For **`type: agent`** hooks the
`if` gate is **not honored** — the hook fires on *every* Bash tool call
regardless of the command. The sibling PreToolUse hook `git-commit-scope.sh`
uses the **identical** `if: "Bash(git commit*)"` with `type: command` and gates
correctly. So the gating mechanism works for command hooks but not agent hooks.

**Impact:** Every Bash invocation spawns a 120s Karen agent review. This adds
latency and token cost to routine read-only commands, and emits confusing false
FINDINGS — e.g. Karen reporting on a commit when only `diff`, `git checkout -b`,
`git status`, or file copies ran (it even self-reports "Bash output shows NO git
add/commit commands"). During this session it misfired on a read-only `diff`, on
`git checkout -b`, and on `git status`.

**Evidence:** Three spurious Karen PostToolUse blocking-error reminders fired on
non-commit Bash calls in the `demo-WebGoat` session on 2026-06-03.

**Recommended fix (pick one, verify against current Claude Code hook semantics):**
1. Confirm whether `if` is a supported key for `type: agent` hooks in this
   Claude Code version. If not, this is using an unsupported field that silently
   no-ops.
2. Convert the trigger to a `type: command` hook that itself decides whether to
   spawn Karen (e.g. inspect the last command / `$ARGUMENTS` for `git commit`
   and only then invoke the agent), mirroring how `git-commit-scope.sh` gates.
3. If agent hooks can only gate via `matcher`, encode the commit specificity in
   the matcher rather than `if`.

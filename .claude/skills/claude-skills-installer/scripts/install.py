#!/usr/bin/env python3
"""Install Claude skills from the Exelixis skills catalog.

Usage:
  python3 install.py <skill> [<skill> ...]   install named skill(s)
  python3 install.py --all                   install all Active/Beta skills
  python3 install.py --list                  list all skills with status
  python3 install.py --search <term>         search all skills by keyword
  python3 install.py --uninstall <skill>     remove an installed skill
  python3 install.py --scope local <skill>   install to ./.claude/skills/
  python3 install.py --dry-run <skill>       preview without installing

Bootstrap (no local clone required):
  gh api repos/exelixis-ai-sandbox/Claude-Assets-Catalog/contents/skills/claude-skills-installer/scripts/install.py \
    --header "Accept: application/vnd.github.v3.raw" | python3 - <skill>
"""

import base64, itertools, json, os, shutil, subprocess, sys, threading
from pathlib import Path

REPO   = "repos/exelixis-ai-sandbox/Claude-Assets-Catalog"
BRANCH = "main"

# ── output ────────────────────────────────────────────────────────────────────

_tty  = sys.stdout.isatty() and not os.environ.get("NO_COLOR") and not os.environ.get("CI")
G, R, Y, B, X = ("\033[0;32m", "\033[0;31m", "\033[0;33m", "\033[1m", "\033[0m") if _tty else ("","","","","")
_lock = threading.Lock()

def log(m):  _print(f"  {m}")
def ok(m):   _print(f"{G}✓{X} {m}")
def err(m):  _print(f"{R}✗{X} {m}", sys.stderr)
def warn(m): _print(f"{Y}!{X} {m}", sys.stderr)
def _print(m, f=sys.stdout):
    with _lock: print(m, file=f)

# ── spinner ───────────────────────────────────────────────────────────────────

class Spinner:
    parallel = False

    def __init__(self, msg):
        self._msg, self._stop, self._t = msg, threading.Event(), None

    def __enter__(self):
        if _tty and not Spinner.parallel:
            self._t = threading.Thread(target=self._run, daemon=True)
            self._t.start()
        return self

    def __exit__(self, *_):
        self._stop.set()
        if self._t:
            self._t.join()
            print("\r\033[K", end="", flush=True)

    def _run(self):
        for c in itertools.cycle("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"):
            if self._stop.wait(0.1): break
            print(f"\r  {B}{c}{X} {self._msg}", end="", flush=True)

# ── GitHub API ────────────────────────────────────────────────────────────────

def _gh(*args):
    return subprocess.run(["gh", "api", *args], capture_output=True)

def gh_json(path):
    r = _gh(f"{REPO}/{path}?ref={BRANCH}")
    return json.loads(r.stdout) if r.returncode == 0 else None

def gh_raw(path):
    r = _gh(f"{REPO}/contents/{path}?ref={BRANCH}",
            "--header", "Accept: application/vnd.github.v3.raw")
    return r.stdout if r.returncode == 0 else None  # bytes

def check_auth():
    if subprocess.run(["gh", "auth", "status"], capture_output=True).returncode != 0:
        err("gh CLI not authenticated. Run: gh auth login")
        sys.exit(1)

def fetch_tree():
    r = _gh(f"{REPO}/git/trees/{BRANCH}?recursive=1")
    return json.loads(r.stdout).get("tree", []) if r.returncode == 0 else []

# ── skill discovery ───────────────────────────────────────────────────────────

def skill_list():
    """Return [{name, description, status}] from metadata.json, falling back to directory names."""
    data = gh_json("contents/metadata.json")
    if data and "content" in data:
        return json.loads(base64.b64decode(data["content"])).get("skills", [])
    items = gh_json("contents/skills") or []
    return [{"name": i["name"], "description": "", "status": ""} for i in items if i["type"] == "dir"]

# ── list / search ─────────────────────────────────────────────────────────────

def cmd_list():
    skills = skill_list()
    if not skills:
        err("No skills found."); return
    print(f"\n{B}Skills:{X}\n")
    for s in skills:
        print(f"  {B}{s['name']:<24}{X}  {s.get('status',''):<12}  {s.get('description','')}")
    print()

def cmd_search(term):
    t = term.lower()
    hits = [s for s in skill_list()
            if t in s.get("name", "").lower() or t in s.get("description", "").lower()]
    print(f"\n{B}Skills matching '{term}':{X}\n")
    if not hits:
        warn(f"No skills matched '{term}'."); return
    for s in hits:
        print(f"  {B}{s['name']:<24}{X}  {s.get('status',''):<12}  {s.get('description','')}")
    print()

# ── interactive picker ────────────────────────────────────────────────────────

def pick_interactive():
    if not sys.stdin.isatty():
        err("No skill name given. Run --list to see available skills.")
        sys.exit(1)
    visible = [s for s in skill_list() if s.get("status", "").lower() not in ("draft", "deprecated")]
    if not visible:
        err("No installable skills found."); sys.exit(1)
    lines = [f"{s['name']:<24}  {s.get('status',''):<12}  {s.get('description','')}" for s in visible]
    try:
        r = subprocess.run(["fzf", "--prompt=Install skill › ", "--height=40%", "--reverse"],
                           input="\n".join(lines), capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip().split()[0]
        sys.exit(0)
    except FileNotFoundError:
        pass
    print(f"\n{B}Available skills:{X}\n", file=sys.stderr)
    for i, s in enumerate(visible, 1):
        print(f"  {i:2}) {B}{s['name']:<24}{X}  {s.get('status',''):<12}  {s.get('description','')}", file=sys.stderr)
    print(file=sys.stderr)
    while True:
        try:
            c = input(f"  Select (1–{len(visible)}, 0 to cancel): ")
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)
        if c == "0": sys.exit(0)
        if c.isdigit() and 1 <= int(c) <= len(visible):
            return visible[int(c) - 1]["name"]
        warn(f"Enter 1–{len(visible)} or 0 to cancel.")

# ── install / uninstall ───────────────────────────────────────────────────────

def cmd_install(name, dest, dry_run, tree):
    prefix = f"skills/{name}/"
    files  = [e for e in tree if e["type"] == "blob" and e["path"].startswith(prefix)]
    if not any(e["path"] == f"skills/{name}/SKILL.md" for e in tree):
        err(f"Skill '{name}' not found in catalog — skipping.")
        return False
    if dry_run:
        log(f"Would install {name} → {dest / name}"); return True
    skill_dest = dest / name
    with Spinner(f"Fetching {name}…"):
        if skill_dest.exists():
            shutil.rmtree(skill_dest)
        for entry in files:
            rel = entry["path"][len(prefix):]
            target = skill_dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            content = gh_raw(entry["path"])
            if content is None:
                err(f"Failed to download {entry['path']}")
                shutil.rmtree(skill_dest, ignore_errors=True)
                return False
            target.write_bytes(content)
    ok(f"Installed {name} → {skill_dest}")
    return True

def cmd_uninstall(name, dest, dry_run):
    d = dest / name
    if not d.is_dir():
        err(f"Skill '{name}' not installed at {dest}"); sys.exit(1)
    if dry_run:
        log(f"Would uninstall {name} from {d}"); return
    shutil.rmtree(d)
    ok(f"Uninstalled {name} from {d}")

def print_summary(total, installed, failed):
    print(f"\n  {'─' * 41}")
    print(f"  {B}{total} requested  ·  {installed} installed  ·  {failed} failed{X}")
    print(f"  {'─' * 41}\n")

# ── argument parsing ──────────────────────────────────────────────────────────

def resolve_dest(args):
    dest = Path.home() / ".claude" / "skills"
    if "--scope" in args:
        i = args.index("--scope")
        if i + 1 >= len(args) or args[i + 1] not in ("global", "local"):
            err("--scope requires 'global' or 'local'"); sys.exit(1)
        if args[i + 1] == "local":
            dest = Path.cwd() / ".claude" / "skills"
    return dest

def collect_names(args):
    """Return positional skill names, skipping flags and their values."""
    skip_val = {"--scope", "--search", "--uninstall"}
    skip_next, names = False, []
    for a in args:
        if skip_next: skip_next = False; continue
        if a in skip_val: skip_next = True; continue
        if a.startswith("--"): continue
        names.append(a)
    return names

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    check_auth()
    args = sys.argv[1:]

    if "--list" in args:
        cmd_list(); return

    if "--search" in args:
        i = args.index("--search")
        if i + 1 >= len(args): err("--search requires a term."); sys.exit(1)
        cmd_search(args[i + 1]); return

    dest    = resolve_dest(args)
    dry_run = "--dry-run" in args

    if "--uninstall" in args:
        i = args.index("--uninstall")
        if i + 1 >= len(args): err("--uninstall requires a skill name."); sys.exit(1)
        cmd_uninstall(args[i + 1], dest, dry_run); return

    install_all = "--all" in args
    names = collect_names(args)

    if install_all:
        skills  = skill_list()
        names   = [s["name"] for s in skills if s.get("status", "").lower() in ("active", "beta")]
        skipped = [s["name"] for s in skills if s.get("status", "").lower() not in ("active", "beta", "")]
        if skipped: warn(f"Skipping (not Active/Beta): {', '.join(skipped)}")
        if not names: warn("No Active/Beta skills found."); return
        log(f"Installing {len(names)} skill(s): {', '.join(names)}")
    elif not names:
        names = [pick_interactive()]

    dest.mkdir(parents=True, exist_ok=True)
    tree = fetch_tree()
    if not tree:
        err("Failed to fetch repository file tree."); sys.exit(1)

    failed = []

    if len(names) > 1:
        Spinner.parallel = True
        results = {}
        def run(n):
            results[n] = cmd_install(n, dest, dry_run, tree)
        threads = [threading.Thread(target=run, args=(n,)) for n in names]
        for t in threads: t.start()
        for t in threads: t.join()
        failed = [n for n in names if not results.get(n)]
    else:
        for n in names:
            if not cmd_install(n, dest, dry_run, tree): failed.append(n)

    print_summary(len(names), len(names) - len(failed), len(failed))
    if failed: err(f"Failed: {', '.join(failed)}"); sys.exit(1)

if __name__ == "__main__":
    main()

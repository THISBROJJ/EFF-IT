#!/usr/bin/env bash
# secrets-scanner.sh — Standalone secrets scanner for the Claude Skills Catalog.
# Patterns align with secrets-check §1–§39 (high-confidence structural only;
# keyword/context patterns are excluded to minimise false positives).
#
# Usage:  bash scripts/secrets-scanner.sh [path]
# Exit 0: no secrets found.
# Exit 1: one or more potential secrets found.

set -uo pipefail

SCAN_PATH="${1:-.}"
PLACEHOLDER_RE='changeme|your[-_.]?here|TODO|REPLACE_ME|example[-_.](key|secret|token|password|value)|<[^>]*>|XXXX|1234567890abcdef'

EXCLUDE=(
  --binary-files=without-match
  --exclude-dir=.git
  --exclude-dir=.claude
  --exclude-dir=node_modules
  --exclude-dir=vendor
  --exclude-dir=dist
  --exclude-dir=build
  --exclude-dir=tests
  --exclude-dir=docs
  '--exclude=secrets-scanner.sh'
  '--exclude=*.lock'
  '--exclude=*.sum'
  '--exclude=*.png'
  '--exclude=*.jpg'
  '--exclude=*.gif'
  '--exclude=*.pdf'
  '--exclude=*.zip'
  '--exclude=*.jar'
  '--exclude=*.war'
  '--exclude=*.ear'
  '--exclude=*.class'
  '--exclude=*.pyc'
  '--exclude=*.o'
  '--exclude=*.so'
  '--exclude=*.exe'
  '--exclude=*.dll'
  '--exclude=*.bin'
)

# High-confidence structural patterns (§1–§39 subset)
PATTERNS=(
  # §1  Private keys
  '-----[[:space:]]*BEGIN[ A-Z0-9_-]*PRIVATE KEY'
  # §2  AWS
  '\b(AKIA|ASIA|AIDA|AGPA|AIPA|ANPA|ACCA|ABIA)[0-9A-Z]{16}\b'
  # §3  GitHub
  'gh[pousr]_[A-Za-z0-9]{36,255}|github_pat_[A-Za-z0-9_]{82}'
  # §4  Slack
  'xox[bpar]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*'
  # §5  Stripe live
  '[rs]k_live_[a-zA-Z0-9]{20,247}'
  # §6  SendGrid
  '\bSG\.[A-Za-z0-9_-]{20,24}\.[A-Za-z0-9_-]{39,50}\b'
  # §7  Twilio SID
  '\bAC[0-9a-f]{32}\b'
  # §9  GCP service account JSON
  '"auth_provider_x509_cert_url"'
  # §11 Connection strings with embedded credentials
  '(mongodb|postgres|postgresql|mysql|redis|amqp|mssql)://[^:@[:space:]]+:[^@[:space:]]+@'
  # §13 AI / LLM keys
  'sk-ant-(api03|admin01)-[a-zA-Z0-9_-]{93}AA'
  '\b(sk-proj-|sk-svcacct-|sk-admin-)[A-Za-z0-9_-]{20,}|T3BlbkFJ'
  '\bhf_[a-zA-Z]{34}\b|\bpplx-[a-zA-Z0-9]{48}\b'
  # §14 Cloud providers
  '\bAIza[A-Za-z0-9_-]{35}\b|\bdo[por]_v1_[a-f0-9]{64}\b'
  # §15 Monitoring
  'eyJrIjoi[A-Za-z0-9]{70,400}|\bsntryu_[a-f0-9]{64}|\bdapi[a-f0-9]{32}\b'
  'dt0c01\.[a-z0-9]{24}\.[a-z0-9]{64}'
  # §16 CI/CD
  '\bglpat-[A-Za-z0-9_-]{20}\b|\bglptt-[0-9a-f]{40}\b|\bGR1348941[A-Za-z0-9_-]{20}\b'
  '\bAKCp[A-Za-z0-9]{69}\b'
  # §17 Package registries
  '\bnpm_[a-zA-Z0-9]{36}\b|pypi-AgEIcHlwaS5vcmc[A-Za-z0-9_-]{50,}'
  # §18 Slack webhooks / Telegram bots
  'hooks\.slack\.com/services/[A-Za-z0-9+/]{43,56}'
  '\b[0-9]{8,10}:[A-Za-z0-9_-]{35}\b'
  # §19 Payment processors
  '\bshp(ss|at|ca|pa)_[a-fA-F0-9]{32}\b'
  '\bFLW(PUBK|SECK)_TEST-[a-h0-9]{32}-X\b'
  '\bshippo_(live|test)_[a-fA-F0-9]{40}\b'
  # §21 IaC / DB services
  '\bpul-[a-f0-9]{40}\b|\bdp\.pt\.[a-zA-Z0-9]{43}\b'
  '\bpscale_(tkn|oauth|pw)_[A-Za-z0-9_=.-]{32,64}\b'
  # §23 Security & secrets management
  '\bp8e-[a-zA-Z0-9]{32}\b'
  '\bAGE-SECRET-KEY-1[QPZRY9X8GF2TVDW0S3JN54KHCE6MUA7L]{58}\b'
  # §24 JWT tokens
  'ey[a-zA-Z0-9]{17,}\.ey[a-zA-Z0-9/_-]{17,}'
  # §27 Social media
  'EAACEdEose0cBA[0-9A-Za-z]+|\bxkeysib-[A-Za-z0-9_-]{81}\b'
  # §28 Extended cloud
  '\bda2-[a-z0-9]{26}\b|\bya29\.[0-9A-Za-z_-]{20,}\b'
  'cloudinary://[0-9]+:[A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+'
  '[A-Za-z0-9]{14}\.atlasv1\.[A-Za-z0-9]{67}'
  # §30 Monitoring extensions
  '\bNR(AA-[a-f0-9]{27}|I[IQ]-[A-Za-z0-9_-]{32}|RA-[a-f0-9]{42})\b'
  '\bphc_[a-zA-Z0-9_]{43}\b'
  # §31 Developer tools
  '\bPMAK-[a-zA-Z0-9]{59}\b|\blin_api_[0-9A-Za-z]{40}\b'
  '\bfio-u-[0-9a-zA-Z_-]{64}\b|\bapify_api_[a-zA-Z0-9]{36}\b'
  # §32 IoT / real-time
  '\baio_[a-zA-Z0-9]{28}\b|\bBBFF-[0-9a-zA-Z]{30}\b'
  # §33 Webhooks
  'AAAA[a-zA-Z0-9_-]{7}:[a-zA-Z0-9_-]{140}'
  # §35 Project management
  '\bATATT3[a-zA-Z0-9+/]{100,}={0,2}'
  # §36 CRM
  '\bpat-[a-z]{2}[0-9]-[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b'
  # §38 Named service env vars
  '(ANTHROPIC_API_KEY|OPENAI_API_KEY|GITHUB_TOKEN|SLACK_TOKEN|DATADOG_API_KEY)[[:space:]]*[=:][[:space:]]*[A-Za-z0-9+/=._-]{10,}'
  # §39 Enterprise
  '\b00[DdUu][0-9A-Za-z]{14}![0-9A-Za-z._]{50,}'
  '\bsessionId[=:][A-Za-z0-9]{32,}'
)

GREP_ARGS=()
for p in "${PATTERNS[@]}"; do
  GREP_ARGS+=(-e "$p")
done

RAW=$(grep -rnE \
  "${EXCLUDE[@]}" \
  "${GREP_ARGS[@]}" \
  "$SCAN_PATH")
GREP_EXIT=$?
if [ "$GREP_EXIT" -eq 2 ]; then
  echo "ERROR: Scanner failed (grep exit 2 — unreadable files or invalid pattern). Treating as FAIL." >&2
  exit 2
fi
FINDINGS=$(printf '%s\n' "$RAW" \
  | grep -vEi "$PLACEHOLDER_RE" \
  | grep -v 'tests/fixtures/' \
  || true)

# ---------------------------------------------------------------------------
# Advisory: hardcoded http:// URLs (non-blocking — always exits 0)
# Flags plain-HTTP URLs that are not localhost/loopback/example.com and are
# not in test or fixture files. These may indicate accidental use of
# unencrypted endpoints for production services.
# ---------------------------------------------------------------------------
HTTP_FINDINGS=$(grep -rnE \
  "${EXCLUDE[@]}" \
  'http://' \
  "$SCAN_PATH" 2>/dev/null \
  | grep -vE 'http://(localhost|127\.0\.0\.1|0\.0\.0\.0|example\.com)[:/]?' \
  | grep -vE '(test|fixture)' \
  || true)

if [ -n "${HTTP_FINDINGS:-}" ]; then
  HTTP_COUNT=$(printf '%s\n' "$HTTP_FINDINGS" | grep -c . || true)
  echo "ADVISORY: ${HTTP_COUNT} hardcoded http:// URL(s) found in ${SCAN_PATH}"
  echo "  Plain HTTP may expose data in transit. Use https:// for non-local endpoints."
  echo ""
  printf '%s\n' "$HTTP_FINDINGS"
  echo ""
fi

if [ -z "${FINDINGS:-}" ]; then
  echo "PASS: No secrets detected in ${SCAN_PATH}"
  exit 0
fi

COUNT=$(printf '%s\n' "$FINDINGS" | grep -c . || true)
echo "FAIL: ${COUNT} potential secret(s) found in ${SCAN_PATH}"
echo ""
printf '%s\n' "$FINDINGS"
echo ""
echo "Remove or rotate any exposed credentials before committing."
echo "For broader coverage including keyword/context patterns, install the secrets-check skill from the Claude Skills Catalog."
exit 1

#!/usr/bin/env bash
# Canonical test-file patterns. Source this file before checking paths.
# Single source of truth — referenced by test-immutability.sh, test-runner.md, coder.md.
# To add a new protected pattern, edit only this file.

# Directory segments that indicate a test file (matched anywhere in the path).
TEST_DIR_PATTERN='(^|/)(tests?|__tests__|specs?|evaluation)/'

# File-name suffixes that indicate a test file.
TEST_FILE_PATTERN='\.(test|spec)\.[^./]+$|/test_[^/]+$|_test\.[^./]+$'

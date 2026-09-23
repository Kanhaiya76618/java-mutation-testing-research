#!/usr/bin/env bash
# Helper script to execute git without reading sandbox-restricted global files
GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null git "$@"

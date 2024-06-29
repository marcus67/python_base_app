#! /bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD)" > ${SCRIPT_DIR}/.env


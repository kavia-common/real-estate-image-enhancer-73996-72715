#!/bin/bash
cd /home/kavia/workspace/code-generation/real-estate-image-enhancer-73996-72715/BackendService
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi


#!/bin/bash
# Runs ty on the entire project, ignoring the file arguments passed by
# lint-staged, since changes in one file can cause errors in another.
uv run ty check

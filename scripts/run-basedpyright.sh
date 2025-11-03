#!/bin/bash
# This script runs basedpyright on the entire project, ignoring the file arguments
# passed by lint-staged. This is necessary because basedpyright uses a baseline file
# that is generated for the entire project.
poetry run basedpyright

#!/usr/bin/env bash

for election in $(find . -name '*.spec.json'); do
    echo "Regenerating $election"
    poetry run python generate_election.py $election "$(dirname $election)"
done
#!/bin/bash

env/bin/ruff --select I --fix-only "$1"
env/bin/ruff format --line-length 320 "$1"

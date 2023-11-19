#!/bin/bash

set -e

python -m venv env
. env/bin/activate
python -m pip install -r requirements.txt
python src/smup.py

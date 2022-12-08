#!/usr/bin/env bash

echo "Start install py packs"

echo "folder: $(pwd)"

venv/bin/pip3 install -r requirements.txt
venv/bin/pip3 install -e .

echo "End install py packs"

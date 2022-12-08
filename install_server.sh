#!/usr/bin/env bash

sDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

./install_py_venv.sh
./install_py_packs.sh

./install_server_service.sh
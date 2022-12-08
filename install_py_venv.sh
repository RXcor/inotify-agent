#!/usr/bin/env bash

echo "Start install py venv"

echo "Install python 3.8"
sudo apt install python3.8 python3.8-venv python3-venv python3.8-dev -y

echo "Create venv"
sudo apt-get -y install virtualenv
virtualenv venv -p python3.8

# other variant 
# python3 -m venv venv

# source install_py_packs.sh

echo "End install py venv"
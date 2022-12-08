#!/usr/bin/env bash

sDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd systemd.conf/
sudo systemctl stop smc-notify*
cd ..

sudo rm /etc/systemd/system/smc-notify*
sudo rm /etc/systemd/system/multi-user.target.wants/smc-notify*

mkdir $sDir/tmp

cp $sDir/bindings_object_example.ini $sDir/bindings.ini

sudo cp $sDir/systemd.conf/smc-notify-object.service /etc/systemd/system/smc-notify.service

sudo systemctl daemon-reload

sudo systemctl enable smc-notify.service

sudo systemctl start smc-notify.service

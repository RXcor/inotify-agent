#!/bin/bash

#Link from scripts directory for cnn

res="$(/bin/bash /home/jetson/smc-notify/scripts/scp_loader_responsive.sh "${@}" || echo 1)"
echo $res
exit $res
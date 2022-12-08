#!/bin/bash

#run /bin/bash scp_loader_responsive_2.sh -i 10 -p '{"port": 2221, "host": "smc@194.226.171.230", "identity_file": "~/.ssh/id_rsa", "src": "/home/vitalij/projects/test-archive/object/2021-11-24T15-55-45/stream3.mp4", "dest": "/w/blue/m/wui-main/test-scp/serial_number/year/month/day/time/stream4.mp4"}'

sDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOCAL_MQTT_SERVER="127.0.0.1"
LOCAL_MQTT_PORT="1883"
CFG="$sDir/scp_loader_responsive_config.yaml"


#read params
msg_idx=""
param=""

if [ $# -eq 0 ]; then
    printf "Use:\n"
    printf "$0 [[--msg_idx|-i] <command id>] [[--parameters|-p] <json string with params>]\n"
    exit 1
fi

while [ -n "$1" ]; do
    case "$1" in
        # -a) echo "Found the -a option"
        #     ;;
        --msg_id|-i) 
            export msg_id="$2"
            # echo "Found the -i option, with parameter value $msg_id"
            shift 
            ;;
        --parameters|-p) 
            export params="$2"
            # echo "Found the -p option, with parameter value $param"
            shift 
            ;;
        --) shift
            break 
            ;;
        *)  echo "$1 is not an option"
            ;;
    esac
    shift
done

#read cfg
declare -A cfgs
while read line; do
    if [[ "$line" != "" ]] && [[ ${line:0:1} != "#" ]] ; then 
        name=$( echo $line | awk -F ":" '{print $1}' |sed 's/ //g' | sed 's/"//g' )
        val=$( echo $line | awk -F ":" '{print $2}' |sed 's/ //g' | sed 's/"//g' )
        cfgs[$name]="$val"
    fi
done < $CFG

destination_root_archive_dir=${cfgs['destination_root_archive_dir']}
local_root_archive_dir=${cfgs['local_root_archive_dir']}
port=${cfgs['port']}
host=${cfgs['host']}
identity_file=${cfgs['identity_file']}
timeout=${cfgs['timeout']}

#declare functions
function jsonValue() {
  KEY=$1
  num=$2
  awk -F"[,:}]" '{for(i=1;i<=NF;i++){if($i~/'$KEY'\042/){print $(i+1)}}}' | tr -d '"' | sed -n ${num}p | sed 's/^[ \t]*//;s/[ \t]*$//'
}

function setDestFromConfig() {
    child=$1
    result=$destination_root_archive_dir$child
    echo $result
}

function setSrcFromConfig() {
    child=$1
    echo $local_root_archive_dir$child
}

child_src_path=`echo ${params} | jsonValue src`
child_dest_path=`echo ${params} | jsonValue dest`

full_dest_path=`setDestFromConfig ${child_dest_path}`
full_dest_dir=`echo $(dirname ${full_dest_path})`
full_src_path=`setSrcFromConfig ${child_src_path}`

res=1
ssh -i ${identity_file} -o "StrictHostKeyChecking=no" -p ${port} ${host} "mkdir -p ${full_dest_dir}"
scp -i ${identity_file} -o "StrictHostKeyChecking=no" -P ${port} ${full_src_path} ${host}:${full_dest_path} && res=0

#write result 
if [[ $msg_id != "" ]] ; then 
    TOPIC=${cfgs['command_result_mqtt_topic_name']}
    if [[ $res -eq 0 ]] ; then 
        VALUE="{\"id\": $msg_id, \"success\": true}"
    else
        VALUE="{\"id\": $msg_id, \"error\": true, \"error_code\": $res}"
    fi
    # echo send message to mosquitto id ${msg_id} topic ${TOPIC}
    mosquitto_pub --quiet --retain --qos 2 -h $LOCAL_MQTT_SERVER -p $LOCAL_MQTT_PORT -t "$TOPIC" -m "$VALUE" &
fi

echo $res




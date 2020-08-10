#!/bin/bash


cd $HOME/eegsynth/patches/biofeedback    # make executable from anywhere

cmd=( mate-terminal )
modules=( recordsignal recordtrigger )
i=0

for module in "${modules[@]}"
do
    if [ $i -eq 0 ]
    then
        cmd+=(--window --title=$module -e "bash -c './$module.sh'")
    else
        cmd+=(--tab --title=$module -e "bash -c 'sleep 5; ./$module.sh'")
    fi
    i=$((i + 1))
done

"${cmd[@]}"

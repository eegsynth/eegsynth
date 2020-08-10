#!/bin/bash


cd $HOME/eegsynth/patches/biofeedback    # make executable from anywhere

mate-terminal --title=biofeedback -e "bash -c './breathingbiofeedback.sh'"

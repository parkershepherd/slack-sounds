#!/bin/bash
file=$(tempfile).m4a
youtube-dl -f 140 ${2} -o $file
if [ $# -le 2 ]
then
    avconv -y -i $file sounds/${1}.mp3
else
    avconv -y -i $file -ss ${3} -t ${4} sounds/${1}.mp3
fi

#!/bin/bash
file=$(tempfile).m4a
youtube-dl -f 140 ${2} -o $file
if [ $# -eq 1 ]
then
    avconv -i $file sounds/${1}.mp3
else
    avconv -i $file -ss ${3} -t ${4} sounds/${1}.mp3
fi

#!/bin/bash
file=$(tempfile).m4a
youtube-dl -f 140 ${1} -o $file

if [ $# -le 1 ]; then
    avplay -nodisp -autoexit $file
else
    avplay -nodisp -autoexit -ss ${2} -t ${3} $file
fi

#!/bin/bash
file=$(tempfile).m4a
youtube-dl -f 140 ${1} -o $file
avplay -nodisp -autoexit -ss ${2} -t ${3} $file

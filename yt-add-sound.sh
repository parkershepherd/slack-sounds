#!/bin/bash
FILE=$(tempfile).m4a
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
youtube-dl -f 140 ${2} -o $FILE
if [ $# -le 2 ]
then
    avconv -y -i $FILE $DIR/sounds/${1}.mp3
else
    avconv -y -i $FILE -ss ${3} -t ${4} $DIR/sounds/${1}.mp3
fi

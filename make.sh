#!/bin/bash


if [ -z "$1" ] || [ ! -d "$1" ]
then
    echo "$(basename $0) <directory of extension>"
    exit 1
fi

xclude="-x $1/tests*"
if [ -f "make.ignore" ]
then
    xclude='-x@make.ignore'
fi

[ ! -d "build" ] && mkdir build

zip -r "build/$1.kne" "$1" "$xclude"


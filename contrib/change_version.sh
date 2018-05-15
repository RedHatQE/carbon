#!/bin/bash

# set the variables
DATE=$(date +%s)
if [ -z "$1" ]
then
  CUR_VER=$(grep -Po '\d.\d.\d' carbon/__init__.py)
  NEW_VER="${CUR_VER%??}.dev${DATE}"
else
  NEW_VER=$1
fi

echo "Setting version to ${NEW_VER}"

# replace with development version
sed -i "s/\(__version__[ ]*=[ ]*[\"']\)\(.*\)\([\"'].*\)/\1${NEW_VER}\3/" carbon/__init__.py
sed -i "s/\(version[ ]*=[ ]u*[\"']\)\(.*\)\([\"'].*\)/\1${NEW_VER}\3/" docs/conf.py
sed -i "s/\(release[ ]*=[ ]u*[\"']\)\(.*\)\([\"'].*\)/\1${NEW_VER}\3/" docs/conf.py
sed -i "s/\(version[ ]*=[ ]*\)\(.*\)\(.*\)/\1${NEW_VER}\3/" setup.cfg
sed -i "s/\(release[ ]*=[ ]*\)\(.*\)\(.*\)/\1${NEW_VER}\3/" setup.cfg

#!/bin/bash

# validate input
if [ "$#" -ne 1 ]; then
   echo "Please provide a version number... exiting!"
   exit 1
fi

# download release
wget https://github.com/cockpit-project/cockpit/releases/download/$1/cockpit-$1.tar.xz
tar zxvf cockpit-$1.tar.xz
rm -f cockpit-$1.tar.xz
git clone https://github.com/cockpit-project/cockpit.git
cd cockpit
git checkout tags/$1
git submodule update --init --recursive
cp -R node_modules/ ../cockpit-$1/
cd ..
tar cfvJ cockpit-$1.tar.xz cockpit-$1
rm -rf cockpit cockpit-$1

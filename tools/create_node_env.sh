#!/usr/bin/env bash

if [ ! -d "gui" ]; then
    echo "Error: Run this script from the main FreeDATA directory."
    exit 1
fi

# Move into freedata-gui directory
cd freedata-gui

# Common variables
OLDPATH=${PATH}
PATH=/usr/bin:/bin:/usr/local/bin
NPM=$(which npm)
PATH=${OLDPATH}
VENVDIR="$(pwd)/node_modules"
PATH_ADDITIONS="$(pwd)/node_modules/bin:$(pwd)/node_modules/.bin"

# Verify NPM exists.
if [ -z "${NPM}" ] || [ ! -x "${NPM}" ]; then
    echo "Error: ${NPM} isn't executable or doesn't exist."
    exit 1
fi

${NPM} install n
${NPM} i

PATH=${PATH_ADDITIONS}:${PATH}

n stable

echo ""
echo "Be sure to add '$PATH_ADDITIONS' to your path."

#!/usr/bin/env bash
set -e

if [ ! -d "tnc" ]; then
    echo "Error: Run this script from the main FreeDATA directory."
    exit 1
fi

HERE="$(pwd)"

echo "Running Python and NodeJS setup scripts for FreeDATA..."

bash tools/create_python_env.sh
bash tools/create_node_env.sh

echo "Both Python and NodeJS were setup correctly."
echo ""
echo "Run the following to add the new Python environment to your path:"
echo "source ${HERE}/.venv/activate"
echo ""
echo "Run the following to add the new NodeJS environment to your path:"
echo "PATH=\${PATH}:${HERE}/gui/node_modules/bin:${HERE}/gui/node_modules/.bin"

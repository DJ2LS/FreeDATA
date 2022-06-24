#!/usr/bin/env sh

if [ ! -d "tnc" ]; then
    echo "Error: Run this script from the main FreeDATA directory."
    exit 1
fi

# Common variables
VENVDIR="`pwd`/.venv"

# Choose an appropriate python interpreter
CHOSEN=/bin/python3
for i in python3.8 python3.9 python3.10 python3.7
do
    if [ -x /bin/$i ]; then
        CHOSEN="/bin/$i"
        break
    fi
done

# Verify it's there.
if [ ! -x ${CHOSEN} ]; then
  echo "Error: ${CHOSEN} is not executable or does not exist."
  exit 1
fi

# Clear the existing virtual environment.
if [ -e "${VENVDIR}" ]; then
    ${CHOSEN} -m venv "${VENVDIR}" --clear
fi

# Create the virtual environment
${CHOSEN} -m venv "${VENVDIR}"

# Activate the virtual environment, if needed
if [ -z "${VIRTUAL_ENV}" -o "${VIRTUAL_ENV}" != "${VENVDIR}" ]; then
    source "${VENVDIR}/activate"
fi

# Cease using ${CHOSEN} as the interpreter we want now is in our path.

# Install packages
python3 -m pip install -U pip wheel
python3 -m pip install -r requirements.txt

echo ""
echo "Be sure to run '. $VENVDIR/activate' before starting the daemon."

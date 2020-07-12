#!/bin/bash

set -e -o pipefail

cd $(dirname $0)

# Generate Lambda zip file

echo "Building Lambda bundle."

echo "Copying files to lambda-build ..."
mkdir lambda-build
cp -R ./src/lambda_function lambda-build/.
cd lambda-build

echo "Running pip install ..."
pip3 install -I -r ./lambda_function/requirements.txt --install-option="--install-purelib=$PWD"

echo "Zipping files ..."
zip -q -r ../lambda-build.zip .

echo "Cleaning up ..."
cd - >/dev/null
rm -rf lambda-build

#!/usr/bin/env bash -e

# Generate Lambda zip file

echo "Building Lambda bundle."

echo "Copying files to lambda-build ..."
cp -R ./src/lambda lambda-build
cd lambda-build

echo "Running pip install ..."
pip install -I -r ./requirements.txt --install-option="--install-purelib=$PWD"

echo "Zipping files ..."
zip -q -r ../lambda-build.zip .

echo "Cleaning up ..."
cd - >/dev/null
rm -rf lambda-build

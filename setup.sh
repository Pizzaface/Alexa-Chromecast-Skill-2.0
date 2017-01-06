#!/usr/bin/env bash

# Generate Lambda zip file
cp -R ./src/lambda lambda-build
cd lambda-build
pip install -I -r ./requirements.txt --install-option="--install-purelib=$PWD"
zip -r ../lambda-build.zip .
cd -
rm -rf lambda-build

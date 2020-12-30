#!/bin/bash

set -e -o pipefail

cd $(dirname $0)

# Generate Lambda zip file

echo "."

echo "Construyendo el paquete Lambda ..."
mkdir lambda-build
cp -R ./src/lambda_function lambda-build/.
cd lambda-build

echo "Iniciando pip install ..."
pip3 install -I -r ./lambda_function/requirements.txt --target=../lambda-build

echo "Comprimiendo archivos ..."
zip -q -r ../lambda-build.zip .

echo "Limpiando ..."
cd - >/dev/null
rm -rf lambda-build

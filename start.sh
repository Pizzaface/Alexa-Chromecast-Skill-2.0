#!/bin/bash

HELP=0
EXTERNAL_IP=
EXTERNAL_PORT=

while getopts "hi:p:" opt; do
  case $opt in
    h) HELP=1
    ;;
    i) export EXTERNAL_IP="$OPTARG"
    ;;
    p) export EXTERNAL_PORT="$OPTARG"
    ;;
    \?) echo "Opción inválida -$OPTARG" >&2; exit 1
    ;;
  esac
done

if [ $HELP -eq 1 ]; then
  echo
  echo "Modo de uso:"
  echo "start.sh --Ejecutar los valores por defecto en modo interactivo"
  echo "start.sh [params]"
  echo "-h      -- Mostrar ayuda"
  echo "-i IP   -- Especificar una dirección IP externa para usar"
  echo "-p port -- Especificar un puerto externo para usar"
  echo
  exit 0
fi


set -e -o pipefail
cd $(dirname $0)

if [ ! -f .env ] || [ ! -d ~/.aws ]; then
  echo "No se ha encontrado la configuración de AWS. Por favor, ejecute el script aws-setup."
  exit 1
fi

. .env
cd src
python3 -m local.main

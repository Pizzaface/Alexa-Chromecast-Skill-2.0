#!/bin/bash

set -e -o pipefail

cd $(dirname $0)

. .env
cd src
python3 -m local.main

#!/bin/sh -xe
# Developer virtualenv setup for Let's Encrypt client

export VENV_ARGS="--python python2"

./bootstrap/dev/_venv_common.sh \
  -e ./


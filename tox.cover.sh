#!/bin/sh -xe

# USAGE: ./tox.cover.sh
#
# This script is used by tox.ini (and thus Travis CI). -e makes sure
# we fail fast and don't submit coveralls submit

# "-c /dev/null" makes sure setup.cfg is not loaded (multiple
# --with-cover add up, --cover-erase must not be set for coveralls
# to get all the data); --with-cover scopes coverage to only
# specific package, positional argument scopes tests only to
# specific package directory; --cover-tests makes sure every tests
# is run (c.f. #403)
nosetests \
  -c /dev/null \
  --cover-erase \
  --with-cover \
  --cover-tests \
  --cover-min-percentage=77 \
  --cover-package letsencrypt_plesk \
  letsencrypt_plesk

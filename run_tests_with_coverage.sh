#!/bin/bash

TARGET='./leastbot'

set -x

pyflakes "$TARGET" || exit $?

coverage run --branch --source "$TARGET" $(which trial) "$TARGET"
status=$?

coverage html

exit $status

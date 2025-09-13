#!/bin/sh -x

sed -e 's/^#our %/our %/' < lib.pl | perl -w

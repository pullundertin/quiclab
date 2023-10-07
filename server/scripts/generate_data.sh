#!/bin/bash

dd if=/dev/zero of=/data/data.log bs=1 count=0 seek=$1 status=none



#!/bin/bash

echo "$HOST: stopping https server..."
pkill nginx >> $LOG_PATH 2>&1


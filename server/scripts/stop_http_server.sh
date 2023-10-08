#!/bin/bash

echo "$HOST: stopping http server..."
pkill nginx >> $LOG_PATH 2>&1


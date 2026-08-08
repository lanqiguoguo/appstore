#!/bin/bash

set -a
. ./.env
set +a

CONFIG_FILE="./config/config.yaml"
if [ -f "$CONFIG_FILE" ]; then
    sed -i "s|__CPA_MANAGEMENT_KEY__|${PANEL_CPA_MANAGEMENT_KEY}|g" "$CONFIG_FILE"
fi

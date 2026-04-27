#!/bin/bash

ENV_FILE=".env"

while [[ $# -gt 0 ]]; do
    case $1 in
        -env)
            if [[ -n "$2" && "$2" != -* ]]; then
                ENV_FILE="$2"
                shift 2
            else
                ENV_FILE=".env"
                shift
            fi
            ;;
        *)
            shift
            ;;
    esac
done

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE not found"
    exit 1
fi

export ENV_FILE="$ENV_FILE"
python3 app.py
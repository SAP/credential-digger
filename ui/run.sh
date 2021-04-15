#!/bin/sh

echo "Download models..."

if [[ -z "${path_model}" ]]; then
    echo "Path model not provided"
else
    echo "Running with path_model=$path_model"
    python -m credentialdigger download path_model
fi

if [[ -z "${snippet_model}" ]]; then
    echo "Snippet model not provided"
else
    echo "Running with snippet_model=$snippet_model"
    python -m credentialdigger download snippet_model
fi

echo "Starting server..."
python /credential-digger-ui/server.py

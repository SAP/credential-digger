#!/bin/bash

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

# Set HTTPS flag to True
HTTPS=true

if [[ -z "${SSL_certificate}" ]]; then
    # No certificate
    HTTPS=false
fi

if [[ -z "${SSL_private_key}" ]]; then
    # No private key
    HTTPS=false
fi

echo "Starting server..."
if [ "$HTTPS" = true ]; then
    echo "🔐 HTTPS will be used..."
    gunicorn -b 0.0.0.0:5000 wsgi:app --certfile $SSL_certificate --keyfile $SSL_private_key
else
    echo "🔓 HTTPS will not be used... (HTTP only)"
    gunicorn -b 0.0.0.0:5000 wsgi:app
fi
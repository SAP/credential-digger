#!/bin/bash

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
if [[ "$HTTPS" = true ]]; then
    echo "🔐 HTTPS will be used..."
    gunicorn -b 0.0.0.0:5000 wsgi:app --certfile $SSL_certificate --keyfile $SSL_private_key
else
    echo "🔓 HTTPS will not be used... (HTTP only)"
    gunicorn -b 0.0.0.0:5000 wsgi:app
fi

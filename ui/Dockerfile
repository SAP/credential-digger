FROM python:3.10-bookworm as builder

# Install system packages
RUN apt-get update && apt-get install -y libpq-dev gunicorn3
RUN apt-get install -y dos2unix

# Install python packages
# Install Gunicorn WSGI HTTP Server
RUN pip install flask_jwt_extended Flask python-dotenv
RUN pip install gunicorn

# Don't verify ssl for github enterprise
RUN git config --global http.sslverify false
# Docker Windows support
RUN git config --global core.autocrlf false

# Install Credential Digger
RUN pip install credentialdigger

# Keys args (optional, for HTTPS)
ARG SSL_certificate
ARG SSL_private_key

# Copy UI files
COPY ui /credential-digger-ui
# Copy LICENSE file into package (compliance)
COPY LICENSE /credential-digger-ui/.
WORKDIR /credential-digger-ui/
# Fix possible line-terminators errors
RUN find . -type f -print0 | xargs -0 dos2unix

RUN chmod +x run.sh
CMD [ "./run.sh" ]

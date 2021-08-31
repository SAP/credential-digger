FROM python:3.7

RUN pip install flask_jwt_extended Flask python-dotenv
RUN apt-get update && apt-get install -y libhyperscan5 libpq-dev gunicorn3

# Don't verify ssl for github enterprise
RUN git config --global http.sslverify false
# Docker Windows support
RUN git config --global core.autocrlf false

# Install Credential Digger
RUN pip install credentialdigger
# Install Gunicorn WSGI HTTP Server
RUN pip install gunicorn

ARG path_model
ARG snippet_model
ARG SSL_certificate
ARG SSL_private_key

COPY . /credential-digger-ui
WORKDIR /credential-digger-ui/
RUN chmod +x run.sh
CMD [ "./run.sh" ]

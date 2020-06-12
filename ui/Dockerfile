FROM python:3.7

RUN pip install Flask python-dotenv
RUN apt update && apt install -y libhyperscan5 libpq-dev

# Install Credential Digger
RUN git config --global http.sslverify false
RUN git clone https://github.com/SAP/credential-digger.git /credential-digger
RUN cd /credential-digger && python setup.py install

ARG path_model
ARG snippet_model
# Download models (if defined)
# Path model
RUN if [ "x$path_model" = "x" ] ; then echo Path model not provided ; else python -m credentialdigger download path_model ; fi
# Snippet model
RUN if [ "x$snippet_model" = "x" ] ; then echo Snippet model not provided ; else python -m credentialdigger download snippet_model ; fi

WORKDIR /credential-digger/ui/

CMD [ "python", "./server.py" ]

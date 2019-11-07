FROM python:3.6

# Use /code for the environment
RUN mkdir -p /code
COPY requirements.txt /code
WORKDIR /code

# Install ghostscript & other requirements
RUN apt-get update && apt-get -y install ghostscript && apt-get clean
RUN pip install -r requirements.txt

# Copy this dir to and install camelot locally
COPY . /code
RUN pip install .

ENTRYPOINT ["camelot"]

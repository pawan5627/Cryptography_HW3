FROM ubuntu:latest

RUN apt-get update && apt-get install -y python3 python3-pip

RUN mkdir -p /usr/local/bin

COPY bitcoin/build/src/bitcoind /usr/local/bin/
COPY rpcauth.py /tmp/

RUN python3 /tmp/rpcauth.py malhip Birth@@19228 > /tmp/rpcauth_string
RUN mkdir -p /tmp/bitcoin-data/.bitcoin
RUN echo "rpcauth=$(cat /tmp/rpcauth_string)\nserver=1" > /tmp/bitcoin-data/.bitcoin/bitcoin.conf
RUN rm /tmp/rpcauth.py /tmp/rpcauth_string

# Install dependencies directly without a virtual environment
COPY requirements.txt /app/
RUN pip3 install --break-system-packages -r /app/requirements.txt

COPY sync_bitcoin.py /app/

WORKDIR /app

EXPOSE 8332

ENTRYPOINT ["python3", "sync_bitcoin.py"]

FROM ubuntu:22.04

# Install dependencies for bitcoind
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-requests \
    libevent-dev libboost-all-dev \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /usr/local/bin

# Copy the bitcoind binary
COPY bitcoin/build/src/bitcoind /usr/local/bin/

# Copy the RPC auth script
COPY rpcauth.py /tmp/

# Generate an RPC auth string
RUN python3 /tmp/rpcauth.py malhip Birth@@19228 > /tmp/rpcauth_string
RUN mkdir -p /tmp/bitcoin-data/.bitcoin
RUN echo "rpcauth=$(cat /tmp/rpcauth_string)\nserver=1" > /tmp/bitcoin-data/.bitcoin/bitcoin.conf
RUN rm /tmp/rpcauth.py /tmp/rpcauth_string

# Install Python dependencies
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r /app/requirements.txt
RUN pip3 install requests
# Copy sync script
COPY sync_bitcoin.py /app/

# Set working directory
WORKDIR /app

# Expose RPC port
EXPOSE 8332

# Start bitcoind
CMD ["bitcoind", "-datadir=/mnt/data/bitcoin-unique"]

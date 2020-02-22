FROM debian:jessie

RUN cd /tmp && \
    apt-get -q update && \
    apt-get -qy install \
        git \
        curl \
        build-essential \
        libboost-all-dev \
        libgmp-dev \
        libleveldb-dev \
        libmicrohttpd-dev \
        libminiupnpc-dev && \
    rm -rf /var/lib/apt/lists/*


COPY . /cpp-ethereum

RUN cpp-ethereum/scripts/install_cmake.sh --prefix /tmp && \
    cd /tmp && PATH=$PATH:/tmp/bin cmake /cpp-ethereum && \
    PATH=$PATH:/tmp/bin cmake --build /tmp -- -j8 && \
    cd /tmp && make install && \
    apt-get clean && \
    rm /cpp-ethereum -rf && \
    rm /tmp/* -rf

RUN eth -D 0

# RUN mkdir -p $HOME/.web3/keys

# ENTRYPOINT ["/usr/local/bin/eth"]

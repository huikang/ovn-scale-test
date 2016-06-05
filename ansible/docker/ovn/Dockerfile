FROM ovn-scale-test-base

# Download OVS from git master
RUN git clone https://github.com/openvswitch/ovs.git \
    && cd /ovs \
    && git checkout 54529e94e96a6b2626d3d26fb619d2e7ab831578 \
    && ./boot.sh \
    && ./configure \
    &&  make -j4 \
    &&  make install

COPY ovn-sandbox-database.sh /bin/ovn_set_database
RUN chmod 755 /bin/ovn_set_database

COPY ovn-sandbox-chassis.sh /bin/ovn_set_chassis
RUN chmod 755 /bin/ovn_set_chassis

COPY ovn-sandbox-north-ovsdb.sh /bin/ovn-sandbox-north-ovsdb.sh
COPY ovn-sandbox-south-ovsdb.sh /bin/ovn-sandbox-south-ovsdb.sh
COPY ovn-sandbox-northd.sh /bin/ovn-sandbox-northd.sh
RUN chmod 755 /bin/ovn-sandbox-north-ovsdb.sh \
              /bin/ovn-sandbox-south-ovsdb.sh \
              /bin/ovn-sandbox-northd.sh

# Install oprofile
RUN apt-get -y update
RUN apt-get -y install \
               wget \
               libpopt-dev \
               libiberty-dev \
               binutils-dev \
               build-essential \
    && apt-get clean

RUN wget http://prdownloads.sourceforge.net/oprofile/oprofile-1.1.0.tar.gz \
    && tar xvzf oprofile-1.1.0.tar.gz \
    && cd /oprofile-1.1.0 \
    && ./configure \
    &&  make -j4 \
    &&  make install

# ENTRYPOINT ["/usr/local/bin/ovn_set_database"]

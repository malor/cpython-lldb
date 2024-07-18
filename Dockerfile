ARG PY_VERSION=latest
FROM python:${PY_VERSION}

ARG LLDB_VERSION=11

RUN DEBIAN_VERSION=`awk -F"[)(]+" '/VERSION=/ {print $2}' /etc/os-release` && \
    wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add - && \
    echo "deb http://apt.llvm.org/${DEBIAN_VERSION}/ llvm-toolchain-${DEBIAN_VERSION}-${LLDB_VERSION} main" >> /etc/apt/sources.list; \
    apt-get update && apt-get install -y lldb-${LLDB_VERSION} && \
    ln -s /usr/bin/lldb-${LLDB_VERSION} /usr/bin/lldb

RUN if [ "${LLDB_VERSION}" = "9" ]; then \
        # The deb package is missing this symlink; lldb won't work w/o it
        ln -s /usr/lib/llvm-9/bin/lldb-server-9 /usr/lib/llvm-9/bin/lldb-server-9.0.1; \
    fi && \
    apt-get install -y python3-lldb-${LLDB_VERSION}

ENV PYTHONPATH /usr/lib/llvm-${LLDB_VERSION}/lib/python3/dist-packages

RUN python -m pip install poetry six

COPY . /root/.lldb/cpython-lldb
RUN cd /root/.lldb/cpython-lldb && \
    poetry version $(git describe --tags --abbrev=0) && \
    poetry install && poetry build -n -f wheel && \
    mkdir -p ~/.lldb/cpython_lldb/site-packages && \
    python -m pip install --target ~/.lldb/cpython_lldb/site-packages dist/*.whl && rm -rf dist && \
    echo "command script import ~/.lldb/cpython_lldb/site-packages/cpython_lldb.py" >> /root/.lldbinit && \
    chmod +x /root/.lldbinit

CMD ["/usr/bin/lldb"]

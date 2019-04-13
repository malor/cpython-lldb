ARG PY_VERSION=latest
FROM python:${PY_VERSION}

RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add - && \
    echo "deb http://apt.llvm.org/stretch/ llvm-toolchain-stretch-8 main" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y lldb-8 && \
    ln -s /usr/bin/lldb-8 /usr/bin/lldb && \
    mkdir -p /root/.lldb/cpython-lldb

COPY *.py /root/.lldb/cpython-lldb/
RUN echo "command script import /root/.lldb/cpython-lldb/cpython_lldb.py" >> /root/.lldbinit && \
    chmod +x /root/.lldbinit

CMD ["/usr/bin/lldb"]

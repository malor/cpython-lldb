ARG PY_VERSION=latest
FROM python:${PY_VERSION}

RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add - && \
    echo "deb http://apt.llvm.org/buster/ llvm-toolchain-buster-7 main" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y lldb-7 && \
    ln -s /usr/bin/lldb-7 /usr/bin/lldb && \
    mkdir -p /root/.lldb/cpython-lldb

RUN python -m pip install "poetry>=0.12,<0.13"

COPY . /root/.lldb/cpython-lldb/
RUN cd /root/.lldb/cpython-lldb && poetry install && poetry build -n -f wheel && python -m pip install dist/*.whl && rm -rf dist
RUN echo "command script import cpython_lldb" >> /root/.lldbinit && \
    chmod +x /root/.lldbinit

CMD ["/usr/bin/lldb"]

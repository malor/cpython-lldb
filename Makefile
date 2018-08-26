PY_VERSION := latest

build-image:
	docker build -t cpython-lldb:$(PY_VERSION) --build-arg PY_VERSION=$(PY_VERSION) .

build-image-py36: PY_VERSION=3.6
build-image-py36: build-image

build-image-py37: PY_VERSION=3.7
build-image-py37: build-image


test: build-image
	docker run -t -i --rm \
		--security-opt seccomp:unconfined --cap-add=SYS_PTRACE \
		-e PYTHONHASHSEED=1 \
		cpython-lldb:$(PY_VERSION) \
		bash -c "cd /root/.lldb/cpython-lldb && python test_cpython_lldb.py -v"

test-py36: PY_VERSION=3.6
test-py36: test

test-py37: PY_VERSION=3.7
test-py37: test

PY_VERSION := latest

build-image:
	docker build -t cpython-lldb:$(PY_VERSION) --build-arg PY_VERSION=$(PY_VERSION) .

build-image-py34: PY_VERSION=3.4
build-image-py34: build-image

build-image-py35: PY_VERSION=3.5
build-image-py35: build-image

build-image-py36: PY_VERSION=3.6
build-image-py36: build-image

build-image-py37: PY_VERSION=3.7
build-image-py37: build-image


test: build-image
	docker run -t -i --rm \
		--security-opt seccomp:unconfined --cap-add=SYS_PTRACE \
		-e PYTHONHASHSEED=1 \
		cpython-lldb:$(PY_VERSION) \
		bash -c "cd /root/.lldb/cpython-lldb && poetry run pytest -vv tests/"

test-py34: PY_VERSION=3.4
test-py34: test

test-py35: PY_VERSION=3.5
test-py35: test

test-py36: PY_VERSION=3.6
test-py36: test

test-py37: PY_VERSION=3.7
test-py37: test

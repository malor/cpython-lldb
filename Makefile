PY_VERSION ?= latest
LLDB_VERSION ?= lldb10
DOCKER_IMAGE_TAG = $(PY_VERSION)-$(LLDB_VERSION)

build-image:
	docker build -t cpython-lldb:$(PY_VERSION) --build-arg PY_VERSION=$(PY_VERSION) -f Dockerfile.base .
	docker build -t cpython-lldb:$(DOCKER_IMAGE_TAG) --build-arg PY_VERSION=$(PY_VERSION) -f Dockerfile.$(LLDB_VERSION) .

build-image-py35: PY_VERSION=3.5
build-image-py35: build-image

build-image-py36: PY_VERSION=3.6
build-image-py36: build-image

build-image-py37: PY_VERSION=3.7
build-image-py37: build-image

build-image-py38: PY_VERSION=3.8
build-image-py38: build-image


test: build-image
	docker run -t -i --rm \
		--security-opt seccomp:unconfined --cap-add=SYS_PTRACE \
		-e PYTHONHASHSEED=1 \
		cpython-lldb:$(DOCKER_IMAGE_TAG) \
		bash -c "cd /root/.lldb/cpython-lldb && poetry run pytest -vv tests/"

test-py35: PY_VERSION=3.5
test-py35: test

test-py36: PY_VERSION=3.6
test-py36: test

test-py37: PY_VERSION=3.7
test-py37: test

test-py38: PY_VERSION=3.8
test-py38: test

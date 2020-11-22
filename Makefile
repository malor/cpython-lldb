PY_VERSION ?= latest
LLDB_VERSION ?= 10
DOCKER_IMAGE_TAG = $(PY_VERSION)-lldb$(LLDB_VERSION)

build-image:
	docker build \
		-t cpython-lldb:$(DOCKER_IMAGE_TAG) \
		--build-arg PY_VERSION=$(PY_VERSION) \
		--build-arg LLDB_VERSION=$(LLDB_VERSION) \
		-f Dockerfile .

build-image-py35: PY_VERSION=3.5
build-image-py35: build-image

build-image-py36: PY_VERSION=3.6
build-image-py36: build-image

build-image-py37: PY_VERSION=3.7
build-image-py37: build-image

build-image-py38: PY_VERSION=3.8
build-image-py38: build-image

build-image-py39: PY_VERSION=3.9
build-image-py39: build-image

build-image-py310: PY_VERSION=3.10-rc
build-image-py310: build-image


test: build-image
	docker run -t -i --rm \
		--security-opt seccomp:unconfined --cap-add=SYS_PTRACE \
		-e PYTHONHASHSEED=1 \
		cpython-lldb:$(DOCKER_IMAGE_TAG) \
		bash -c "cd /root/.lldb/cpython-lldb && poetry run pytest -n 4 -vv tests/ -m 'not serial' && poetry run pytest -n 0 -vv tests/ -m 'serial'"

test-py35: PY_VERSION=3.5
test-py35: test

test-py36: PY_VERSION=3.6
test-py36: test

test-py37: PY_VERSION=3.7
test-py37: test

test-py38: PY_VERSION=3.8
test-py38: test

test-py39: PY_VERSION=3.9
test-py39: test

test-py310: PY_VERSION=3.10-rc
test-py310: test

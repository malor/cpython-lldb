PY_VERSION ?= 3.9
LLDB_VERSION ?= 11
DOCKER_IMAGE_TAG = $(PY_VERSION)-lldb$(LLDB_VERSION)

# older LLVM versions are not packaged for Debian Bullseye, which is the new stable
# used in Python Docker images. We can fall back to Buster images for testing those
ifeq ($(shell test $(LLDB_VERSION) -lt 11 && echo true), true)
	PY_DISTRO = $(PY_VERSION)-buster
else
	PY_DISTRO = $(PY_VERSION)
endif

build-image:
	docker build \
		-t cpython-lldb:$(DOCKER_IMAGE_TAG) \
		--build-arg PY_VERSION=$(PY_DISTRO) \
		--build-arg LLDB_VERSION=$(LLDB_VERSION) \
		-f Dockerfile .

test: build-image
	docker run \
		--rm \
		--security-opt seccomp:unconfined --cap-add=SYS_PTRACE \
		-e PYTHONHASHSEED=1 \
		cpython-lldb:$(DOCKER_IMAGE_TAG) \
		bash -c "cd /root/.lldb/cpython-lldb && poetry run pytest -n 4 -vv tests/ -m 'not serial' && poetry run pytest -n 0 -vv tests/ -m 'serial'"

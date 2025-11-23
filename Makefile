PY_VERSION ?= 3.10
LLDB_VERSION ?= 11
DOCKER_IMAGE_TAG = $(PY_VERSION)-lldb$(LLDB_VERSION)

ifeq ($(shell test $(LLDB_VERSION) -lt 11 && echo true), true)
	# LLVM >= 7: https://apt.llvm.org/buster/pool/main/l/
	PY_DISTRO = $(PY_VERSION)-buster
else ifeq ($(shell test $(LLDB_VERSION) -lt 15 && echo true), true)
	# LLVM >= 11: https://apt.llvm.org/bullseye/pool/main/l/
	PY_DISTRO = $(PY_VERSION)-bullseye
else
	# LLVM >= 15
	PY_DISTRO = $(PY_VERSION)
endif

build-image:
	docker buildx build  \
		--debug \
		-t cpython-lldb:$(DOCKER_IMAGE_TAG) \
		--build-arg PY_VERSION=$(PY_DISTRO) \
		--build-arg LLDB_VERSION=$(LLDB_VERSION) \
		-f Dockerfile .

# Run tests normally. The level of parallelism is set to match the number of CPU threads
test: build-image
	docker run \
		--rm \
		--security-opt seccomp:unconfined --cap-add=SYS_PTRACE \
		-e PYTHONHASHSEED=1 \
		cpython-lldb:$(DOCKER_IMAGE_TAG) \
		bash -c "ulimit -n 1024 && cd /root/.lldb/cpython-lldb && poetry run pytest -n auto -vv tests/"

# Run tests serially and start a pdb session when a test fails
debug: build-image
	docker run -t -i \
		--rm \
		--security-opt seccomp:unconfined --cap-add=SYS_PTRACE \
		-e PYTHONHASHSEED=1 \
		cpython-lldb:$(DOCKER_IMAGE_TAG) \
		bash -c "ulimit -n 1024 && cd /root/.lldb/cpython-lldb && poetry run pytest -s -n auto -vv --pdb -x --ff tests/"

# Start a shell in a container with cpython-lldb installed
shell: build-image
	docker run -t -i \
		--rm \
		--security-opt seccomp:unconfined --cap-add=SYS_PTRACE \
		-e PYTHONHASHSEED=1 \
		cpython-lldb:$(DOCKER_IMAGE_TAG) \
		bash

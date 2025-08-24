# Directories
VENV_DIR := build_venv
BUILD_DIR := build
WHEEL_DIR := dist

# Calculate the exact version from the git tag (requires the repo to be tagged correctly)
VERSION := $(shell git describe | awk -F- '{print $$1"."$$2}')

.PHONY: all venv install-deps build-ui build-wheel install-wheel clean help

all: install-wheel

help:
	@echo "Available commands:"
	@echo "  make all            - Run all steps: venv, install dependencies, build UI, build wheel, install wheel"
	@echo "  make venv           - Create Python virtual environment (in $(VENV_DIR))"
	@echo "  make install-deps   - Install required Python packages from misc/requirements.in"
	@echo "  make build-ui       - Compile UI files, resources, and translations (with --force)"
	@echo "  make build-wheel    - Build Python wheel package using setup.py"
	@echo "  make install-wheel  - Install the generated wheel package using pip install"
	@echo "  make clean          - Remove virtual environment, build artifacts, and marker files"

$(BUILD_DIR):
	mkdir -p $@

$(VENV_DIR): $(BUILD_DIR)
	python3 -m venv $(VENV_DIR)
venv: $(VENV_DIR)

$(BUILD_DIR)/.rare-install-deps: venv
	. $(VENV_DIR)/bin/activate && pip install -r misc/requirements.in
	. $(VENV_DIR)/bin/activate && pip install ruff
	touch $@
install-deps: $(BUILD_DIR)/.rare-install-deps

$(BUILD_DIR)/.rare-build-ui: install-deps
	. $(VENV_DIR)/bin/activate && bash tools/ui2py.sh --force
	. $(VENV_DIR)/bin/activate && bash tools/qrc2py.sh --force
	. $(VENV_DIR)/bin/activate && python3 tools/ts2qm.py
	touch $@
build-ui: $(BUILD_DIR)/.rare-build-ui

$(BUILD_DIR)/.rare-build-wheel: build-ui
	. $(VENV_DIR)/bin/activate && python -m build
	touch $@
build-wheel: $(BUILD_DIR)/.rare-build-wheel

install-wheel: build-wheel
	. $(VENV_DIR)/bin/activate && \
	if pip show rare > /dev/null 2>&1; then \
		pip3 uninstall -y rare; \
	fi
	WHEEL_FILE=$$(ls -t $(WHEEL_DIR)/rare-*-py3-none-any.whl | head -n1); \
	. $(VENV_DIR)/bin/activate && pip install "$$WHEEL_FILE"

clean:
	rm -rf $(VENV_DIR) $(WHEEL_DIR) build/ Rare.egg-info __pycache__ **/__pycache__
	rm -f $(BUILD_DIR)/.rare-install-deps $(BUILD_DIR)/.rare-build-ui $(BUILD_DIR)/.rare-build-wheel

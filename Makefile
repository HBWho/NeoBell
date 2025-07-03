# Makefile for NeoBell Project
# Organized management for development, testing, and environment setup

.PHONY: help setup setup-src setup-components venv-src venv-components install-src install-components run-src run-components clean clean-src clean-components env-config

# Default help target
help:
	@echo "\nNeoBell Project Makefile"
	@echo "====================================="
	@echo "Available targets:"
	@echo "  setup            - Setup both src and components_tests environments"
	@echo "  setup-src        - Setup Python venv and install requirements for src/"
	@echo "  setup-components - Setup Python venv and install requirements for components_tests/"
	@echo "  venv-src         - Create Python venv for src/ only"
	@echo "  venv-components  - Create Python venv for components_tests/ only"
	@echo "  install-src      - Install requirements for src/ only"
	@echo "  install-components - Install requirements for components_tests/ only"
	@echo "  run-src          - Run main application in src/"
	@echo "  run-components   - Run main.py in components_tests/"
	@echo "  env-config       - Guide user to configure .env file for src/"
	@echo "  clean            - Remove all venvs and __pycache__"
	@echo "  clean-src        - Remove src venv and __pycache__"
	@echo "  clean-components - Remove components_tests venv and __pycache__"
	@echo "\nExample: make setup run-src\n"

# Setup both environments
setup: setup-src setup-components
	@echo "\n🎉 All environments set up!"
	@echo "\n⚠️  Remember to configure your .env file in the project root. Run: make env-config\n"

# Setup src environment
setup-src: venv-src install-src
	@echo "\n✅ src/ environment ready."

# Setup components_tests environment
setup-components: venv-components install-components
	@echo "\n✅ components_tests/ environment ready."

# Create venv for src
venv-src:
	@if [ ! -d venv-src ]; then \
		python -m venv venv-src; \
		printf '\n[venv-src] Virtual environment created.\n'; \
	else \
		printf '\n[venv-src] Virtual environment already exists.\n'; \
	fi
# Platform detection
OS := $(shell uname 2>/dev/null | grep -i -E 'mingw|msys|cygwin' && echo Windows || echo Linux)

# Python and venv activation
ifeq ($(OS),Windows)
PYTHON = python
VENV_SRC_ACTIVATE = venv-src\Scripts\activate.bat
VENV_COMPONENTS_ACTIVATE = venv-components\Scripts\activate.bat
PIP_SRC = venv-src\Scripts\pip.exe
PIP_COMPONENTS = venv-components\Scripts\pip.exe
RM = rmdir /S /Q
else
PYTHON = python3
VENV_SRC_ACTIVATE = . venv-src/bin/activate
VENV_COMPONENTS_ACTIVATE = . venv-components/bin/activate
PIP_SRC = venv-src/bin/pip
PIP_COMPONENTS = venv-components/bin/pip
RM = rm -rf
endif

# Create venv for src
venv-src:
	@if [ ! -d venv-src ]; then \
		$(PYTHON) -m venv venv-src; \
		printf '\n[venv-src] Virtual environment created.\n'; \
	else \
		printf '\n[venv-src] Virtual environment already exists.\n'; \
	fi

# Create venv for components_tests
venv-components:
	@if [ ! -d venv-components ]; then \
		$(PYTHON) -m venv venv-components; \
		printf '\n[venv-components] Virtual environment created.\n'; \
	else \
		printf '\n[venv-components] Virtual environment already exists.\n'; \
	fi

# Install requirements for src
install-src: venv-src
	@if [ -f requirements.txt ]; then \
		$(PIP_SRC) install --upgrade pip; \
		$(PIP_SRC) install -r requirements.txt; \
		printf '\n[venv-src] Requirements installed.\n'; \
	else \
		printf '\n[venv-src] requirements.txt not found!\n'; \
	fi

# Install requirements for components_tests
install-components: venv-components
	@if [ -f components_tests/requirements.txt ]; then \
		$(PIP_COMPONENTS) install --upgrade pip; \
		$(PIP_COMPONENTS) install -r components_tests/requirements.txt; \
		printf '\n[venv-components] Requirements installed.\n'; \
	else \
		printf '\n[venv-components] requirements.txt not found!\n'; \
	fi

# Run main application in src
run-src:
ifeq ($(OS),Windows)
	@call $(VENV_SRC_ACTIVATE) && $(PYTHON) src\main.py
else
	@$(VENV_SRC_ACTIVATE); $(PYTHON) src/main.py
endif

# Run main.py in components_tests
run-components:
ifeq ($(OS),Windows)
	@call $(VENV_COMPONENTS_ACTIVATE) && $(PYTHON) components_tests\main.py
else
	@$(VENV_COMPONENTS_ACTIVATE); $(PYTHON) components_tests/main.py
endif

# Guide user to configure .env
env-config:
ifeq ($(OS),Windows)
	@echo. & echo ⚠️  Please configure your .env file in the project root. & \
	echo You can copy .env.example to .env and edit the values: & \
	echo   copy .env.example .env & \
	echo Then edit .env with your AWS IoT credentials and other settings. & \
	echo. & \
	echo Required fields (see .env.example): & \
	findstr /R "^[A-Z_][A-Z_0-9]*=" .env.example || echo Check .env.example for required variables.
else
	@echo "\n⚠️  Please configure your .env file in the project root."; \
	echo "You can copy .env.example to .env and edit the values:"; \
	echo "  cp .env.example .env"; \
	echo "Then edit .env with your AWS IoT credentials and other settings."; \
	echo "\nRequired fields (see .env.example):"; \
	grep -E '^[A-Z_]+=' .env.example || echo 'Check .env.example for required variables.'
endif

# Clean all venvs and __pycache__
clean: clean-src clean-components
	@echo "\n🧹 All environments and caches cleaned."

clean-src:
ifeq ($(OS),Windows)
	-$(RM) venv-src
	-@for /d /r src %%d in (__pycache__) do @if exist "%%d" $(RM) "%%d"
else
	-$(RM) venv-src
	-find src/ -type d -name '__pycache__' -exec rm -rf {} + || true
endif
	@echo "[venv-src] and src/__pycache__ removed."

clean-components:
ifeq ($(OS),Windows)
	-$(RM) venv-components
	-@for /d /r components_tests %%d in (__pycache__) do @if exist "%%d" $(RM) "%%d"
else
	-$(RM) venv-components
	-find components_tests/ -type d -name '__pycache__' -exec rm -rf {} + || true
endif
	@echo "[venv-components] and components_tests/__pycache__ removed."

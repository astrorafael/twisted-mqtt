# To install just on a per-project basis
# 1. Activate your virtual environemnt
# 2. uv add --dev rust-just
# 3. Use just within the activated environment

pkg := "twisted-mqtt"
module := "mqtt.client"

# list all recipes
default:
    just --list

# Add conveniente development dependencies
dev:
    uv add --dev pytest

# Build the package
build:
    rm -fr dist/*
    uv build

# Install tools globally
tools:
    uv tool install twine
    uv tool install ruff


# Publish the package to PyPi
publish: build
    twine upload -r pypi dist/*
    uv run --no-project --with {{pkg}} --refresh-package {{pkg}} \
        -- python -c "from {{module}} import __version__; print(__version__)"

# Publish to Test PyPi server
test-publish: build
    twine upload --verbose -r testpypi dist/*
    uv run --no-project  --with {{pkg}} --refresh-package {{pkg}} \
        --index-url https://test.pypi.org/simple/ \
        --extra-index-url https://pypi.org/simple/ \
        -- python -c "from {{module}} import __version__; print(__version__)"
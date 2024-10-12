# To install just on a per-project basis
# 1. Activate your virtual environemnt
# 2. uv add --dev rust-just
# 3. Use just within the activated environment

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

# Publish the package in (pypi|testpypi)
publish repo="pypi" : build
    twine upload --verbose -r {{ repo }} dist/*

# Install tools globally
tools:
    uv tool install twine
    uv tool install ruff

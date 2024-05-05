#!/bin/bash

pytest --doctest-modules --junitxml=junit/test-results.xml --cov=com --cov-report=xml --cov-report=html
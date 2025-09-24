SHELL := $(shell which bash)
SELF  := $(patsubst %/,%,$(dir $(abspath $(firstword $(MAKEFILE_LIST)))))

export

.PHONY: all

all: test

.PHONY: test test_one test_rc test_yaml

test: test_one test_rc test_yaml

test_one:
	rspec $(SELF)/ruby/one_spec.rb
	python $(SELF)/python/test_one.py

test_rc:
	rspec $(SELF)/ruby/rc_spec.rb
	python $(SELF)/python/test_rc.py

test_yaml:
	python $(SELF)/python/test_yaml.py

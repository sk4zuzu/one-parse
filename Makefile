SHELL := $(shell which bash)
SELF  := $(patsubst %/,%,$(dir $(abspath $(firstword $(MAKEFILE_LIST)))))

export

.PHONY: all

all: test

.PHONY: test test_one test_rc

test: test_one test_rc

test_one:
	rspec $(SELF)/tests/one_spec.rb

test_rc:
	rspec $(SELF)/tests/rc_spec.rb

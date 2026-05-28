#!/bin/bash
set -e

exec liquibase \
  --changeLogFile=dbchangelog.xml \
  update

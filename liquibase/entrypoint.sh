#!/bin/bash
set -e

exec liquibase \
  --url="${DATABASE_URL}" \
  --changeLogFile=dbchangelog.xml \
  update


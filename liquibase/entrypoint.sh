#!/bin/bash
set -e

exec liquibase \
  --url="${DATABASE_URL}" \
  --username="${DATABASE_USER}" \
  --password="${DATABASE_PASSWORD}" \
  --changeLogFile=dbchangelog.xml \
  update


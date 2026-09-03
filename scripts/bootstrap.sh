#!/bin/sh
set -eu
command -v docker >/dev/null 2>&1 || { echo 'Brak Docker CLI'; exit 1; }
docker compose version >/dev/null 2>&1 || { echo 'Brak docker compose'; exit 1; }
arch=$(uname -m)
case "$arch" in arm64|aarch64) ;; *) echo "Uwaga: wykryto architekture $arch, projekt celuje w Apple Silicon" ;; esac
[ -f .env ] || cp .env.example .env
mkdir -p data reports secrets
chmod 700 secrets
printf 'Bootstrap OK\n'

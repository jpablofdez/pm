# Scripts

This directory contains OS-specific start/stop scripts for running the MVP in Docker.

## Contract

- `start_mac.sh`
- `stop_mac.sh`
- `start_linux.sh`
- `stop_linux.sh`
- `start_windows.ps1`
- `stop_windows.ps1`

Each script checks that `docker` is available and then runs the expected `docker compose` command from the project root.

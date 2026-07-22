#!/bin/bash
psql -U urja -d urja -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

#!/bin/bash

# Use npx to automatically download and run the official v2.0.2 Node.js server
echo "Starting official Node.js POT provider on port 4416..."

# Run the server in the background
npx -y bgutil-ytdlp-pot-provider@2.0.2 server --port 4416 &

echo "POT provider running (PID: $!)"
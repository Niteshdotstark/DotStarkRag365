#!/bin/bash
# Quick fix script for Ubuntu server

echo "=========================================="
echo "Facebook Token Issue - Auto Fix"
echo "=========================================="
echo ""

# Navigate to backend directory
cd /home/ubuntu/ChatBotBE/backend

echo "Running diagnostic and fix tool..."
python3 diagnose_and_fix.py

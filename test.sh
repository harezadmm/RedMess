#!/bin/bash

# Quick test script to verify RedMess installation
echo "Testing RedMess components..."

# Test 1: Check if skills exist
if [ -f "security/weaponization/windows-rat-keylogger.md" ]; then
    echo "✓ Skills present"
else
    echo "✗ Skills missing"
    exit 1
fi

# Test 2: Check if GODMODE prompt exists
if [ -f "godmode_prompt.txt" ]; then
    echo "✓ GODMODE prompt present"
else
    echo "✗ GODMODE prompt missing"
    exit 1
fi

# Test 3: Check deployment script
if [ -x "deploy.sh" ]; then
    echo "✓ Deployment script executable"
else
    echo "✗ Deployment script not executable"
    exit 1
fi

# Test 4: Count skills
SKILL_COUNT=$(find security -name "*.md" -type f | wc -l)
echo "✓ Found $SKILL_COUNT skills"

# Test 5: Verify Python scripts
python3 verify.py
if [ $? -eq 0 ]; then
    echo "✓ All verification tests passed"
else
    echo "✗ Verification failed"
    exit 1
fi

echo ""
echo "════════════════════════════════════════"
echo "All tests passed! RedMess is ready."
echo "════════════════════════════════════════"

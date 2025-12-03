#!/bin/bash

echo "Installing Psh..."
if command -v python3 &> /dev/null; then
    if [[ ! -f psh ]]; then
        echo "Error: psh file not found in current directory"
        exit 1
    fi

    sudo cp psh /usr/local/bin/psh || exit 1
    sudo chmod +x /usr/local/bin/psh

    if ! grep -q "^/usr/local/bin/psh$" /etc/shells; then
        echo "/usr/local/bin/psh" | sudo tee -a /etc/shells > /dev/null
    fi

    chsh -s /usr/local/bin/psh
    echo "Shell changed successfully to psh"
    echo "Done"

else
    echo "Python3 not found. Install it first then try again"
    exit 1

fi
#!/bin/bash

# Detect package manager
if command -v apt &> /dev/null; then
    PKG_MANAGER="apt"
elif command -v yum &> /dev/null; then
    PKG_MANAGER="yum"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
else
    echo "Unsupported package manager. Exiting."
    exit 1
fi

# Update repositories and install required system packages
if [ "$PKG_MANAGER" == "apt" ]; then
    sudo apt update
    sudo apt install -y python3-pip python3-venv net-tools unzip
elif [ "$PKG_MANAGER" == "yum" ] || [ "$PKG_MANAGER" == "dnf" ]; then
    sudo $PKG_MANAGER -y update
    sudo $PKG_MANAGER -y install python3-pip python3-venv net-tools unzip
else
    echo "Unsupported package manager. Exiting."
    exit 1
fi

# Create and activate virtual environment
python3 -m venv myenv
source myenv/bin/activate
# Install Python packages using pip in the virtual environment
packages=(
    "Flask"
    "Flask-Login"
    "Flask-WTF"
    "Flask-Bootstrap"
    "Flask-SQLAlchemy"
    "Flask-Migrate"
    "Flask-Admin"
    "Flask-Caching"
    "Flask-Mail"
    "Flask-RESTful"
    "psutil"
    "humanize"
)

for package in "${packages[@]}"; do
    pip install "$package"
done

# Deactivate the virtual environment after installation
python3 -m venv myenv
source myenv/bin/activate
python -m pip install --upgrade pip
pip install Flask Flask-Login Flask-WTF Flask-Bootstrap Flask-SQLAlchemy Flask-Migrate Flask-Admin Flask-Caching Flask-Mail Flask-RESTful psutil humanize


# Unzip required files and clean up
unzip -q pycache.zip
unzip -q static.zip
unzip -q templates.zip
rm -f pycache.zip static.zip templates.zip

# Execute the run script (assuming it's present and correctly configured)
if [ -f "run.sh" ]; then
    bash run.sh
else
    echo "run.sh not found. Exiting."
    exit 1
fi

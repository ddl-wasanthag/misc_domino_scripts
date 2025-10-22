#!/bin/bash
set -x

#create a tar file from Domino flyte packages from a workspace with Domino Standard Env 6.0, where these packages are available
#cd /opt/conda/envs/python39/lib/python3.10/site-packages/

# List to see what's there
#ls -la
##Created the backup directory structure
#mkdir -p /tmp/domino-backup
#Copied the Domino-specific packages
## Copy all domino-related packages from Python 3.10 to the backup directory
#cp -r domino* /tmp/domino-backup/
#cp -r flytekit* /tmp/domino-backup/
#cp -r flytekitplugins* /tmp/domino-backup/

#cd /tmp
#tar -czf domino-backup.tar.gz domino-backup/

# Download the tar file from GitHub (use raw URL)
wget -O /tmp/domino-flyte-backup.tar.gz https://github.com/ddl-wasanthag/misc_domino_scripts/raw/main/misc/domino-flyte-backup.tar.gz

# Extract the tar file
cd /tmp
tar -xzf domino-flyte-backup.tar.gz

# Copy to Python 3.12 site-packages
cp -r /tmp/domino-backup/* /opt/conda/lib/python3.12/site-packages/

# Install flytekit first
pip install --force-reinstall --no-cache-dir flytekit

# Install dependencies with compatible versions
# Note: Using typing-extensions>=4.12 to satisfy most packages
# and frozendict>=2.4.2 for conda
pip install \
    plotly \
    pandas \
    pyarrow \
    rich-click \
    ipywidgets \
    markdown \
    backoff \
    'bson>=0.5.10,<0.6.0' \
    'loguru>=0.5.3,<0.6.0' \
    'urllib3>=1.26.16,<2.0.0' \
    'polling2~=0.5.0' \
    'retry==0.9.2' \
    'frozendict>=2.4.2' \
    'python-dateutil>=2.8.2' \
    'typing-extensions>=4.12' \
    'attrs>=20.1.0,<22.0.0'

# Verify installation
python3.12 -c "from flytekitplugins.domino.task import DominoJobConfig, DominoJobTask; print('Success')"

# Check for conflicts
pip check

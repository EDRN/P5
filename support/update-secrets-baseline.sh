#!/bin/sh
#
# Update the secrets baseline file. Relies on detect-secrets being in the $PATH
#

if [ \! -f .secrets.baseline ]; then
    echo "🐇 No .secrets.baseline file found, creating a new one" 1>&2
fi

detect-secrets scan \
    '--disable-plugin' \
    'AbsolutePathDetectorExperimental' \
    --exclude-files '\.secrets..*' \
    --exclude-files '\.git.*' \
    --exclude-files '\.mypy_cache' \
    --exclude-files '\.pytest_cache' \
    --exclude-files '\.tox' \
    --exclude-files '\.venv' \
    --exclude-files 'venv' \
    --exclude-files 'dists' \
    --exclude-files 'build' \
    --exclude-files 'static' \
    --exclude-files 'papers' \
    --exclude-files 'media' \
    --exclude-files '__pycache__' \
    --exclude-files '.*\.egg-info' > .secrets.baseline

echo "Don't forget to audit the new .secrets.baseline now" 1>&2
echo "Run: detect-secrets audit .secrets.baseline" 1>&2
exit 0

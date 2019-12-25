#!/bin/sh -l
#
# Bootstrap, buildout, and run tests
#
# This feels … not so modular

bootstrapURL="$1"
buildoutConfig="$2"
testPackages="$3"

PATH=/usr/local/bin:/usr/bin:/bin
export PATH

mkdir $HOME/.buildout
cp /root/.buildout/default.cfg $HOME/.buildout

echo "🔍 Checking for `bootstrap.py` in $GITHUB_WORKSPACE…" 1>&2
cd "$GITHUB_WORKSPACE"
if [ ! -f bootstrap.py ]; then
    echo '🔍 Checking for `bootstrap-buildout.py`…' 1>&2
    if [ ! -f bootstrap-buildout.py ]; then
        echo "🚚 Retrieving a bootstrapper from $bootstrapURL" 1>&2
        curl -L "$bootstrapURL" > bootstrap.py
    else
        echo '📛 Renaming `bootstrap-buildout.py` to just `bootstrap.py`' 1>&2
        mv bootstrap-buildout.py bootstrap.py
    fi
fi

echo '🏃‍♀️ Bootstrapping the buildout and building out' 1>&2
python bootstrap.py -c "$buildoutConfig" && bin/buildout -c "$buildoutConfig"

echo '🔍 Checking for a test runner in `bin/test`' 1>&2
if [ ! -x bin/test ]; then
    echo "Buildout with $buildoutConfig didn't create a test runner in bin/test; skipping tests" 1>&2
    exit 0
fi

for package in $testPackages; do
    echo "🧪 Testing $package" 1>&2
    if ! bin/test --package $package; then
        echo "Failed to run tests in $package; aborting the rest" 1>&2
        exit 1
    fi
done

echo '✋ All done' 1>&2
exit 0

# Check if bin/test exists

# echo "🚗 ===== OK we are in ====="
# echo "⚙️ ===== args = $@ "
# echo "… bootstrapURL= $bootstrapURL"
# echo "… buildoutConfig = $buildoutConfig"
# echo "… testPackages = $testPackages"
# echo "… and bin dir contains"
# ls -F bin

# echo "…pwd"
# pwd
# echo "🌳 ===== env follows"
# env
# echo "🌳 ===== end env "
# echo "📁 ===== directory / follows"
# ls -F /
# echo "📁 ===== directory / ends"
# echo "📂 ===== workspace follows"
# ls -F /github/workspace
# echo "📂 ===== workspace ends"
# echo "🛑 the end"
# exit 0



# Successfully tagged 671ee6:1e997ec6be2451bfdbdd7a2b87e82dae
# ##[command]/usr/bin/docker run --name ee61e997ec6be2451bfdbdd7a2b87e82dae_76ef93 --label 671ee6 --workdir /github/workspace --rm -e INPUT_BOOTSTRAP-URL -e HOME -e GITHUB_REF -e GITHUB_SHA -e GITHUB_REPOSITORY -e GITHUB_ACTOR -e GITHUB_WORKFLOW -e GITHUB_HEAD_REF -e GITHUB_BASE_REF -e GITHUB_EVENT_NAME -e GITHUB_WORKSPACE -e GITHUB_ACTION -e GITHUB_EVENT_PATH -e RUNNER_OS -e RUNNER_TOOL_CACHE -e RUNNER_TEMP -e RUNNER_WORKSPACE -e ACTIONS_RUNTIME_URL -e ACTIONS_RUNTIME_TOKEN -e GITHUB_ACTIONS=true -v "/var/run/docker.sock":"/var/run/docker.sock" -v "/home/runner/work/_temp/_github_home":"/github/home" -v "/home/runner/work/_temp/_github_workflow":"/github/workflow" -v "/home/runner/work/P5/P5":"/github/workspace" 671ee6:1e997ec6be2451bfdbdd7a2b87e82dae  "https://bootstrap.pypa.io/bootstrap-buildout.py"
# 🚗 ===== OK we are in =====
# ⚙️ ===== args = https://bootstrap.pypa.io/bootstrap-buildout.py 
# 🌳 ===== env follows
# ACTIONS_RUNTIME_TOKEN=***
# HOSTNAME=0c9be033c409
# HOME=/github/home
# RUNNER_TEMP=/home/runner/work/_temp
# GITHUB_EVENT_PATH=/github/workflow/event.json
# GITHUB_HEAD_REF=
# ACTIONS_RUNTIME_URL=https://pipelines.actions.githubusercontent.com/ctIOLZ6zLlJfaetuYw5chFr919NmFoX4KBHnBvb3zx7yc2PrY7/
# RUNNER_OS=Linux
# GITHUB_WORKFLOW=P5 Continuous Integration
# GITHUB_BASE_REF=
# PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# RUNNER_TOOL_CACHE=/opt/hostedtoolcache
# GITHUB_ACTION=self
# GITHUB_REPOSITORY=nutjob4life/P5
# GITHUB_ACTIONS=true
# GITHUB_WORKSPACE=/github/workspace
# GITHUB_SHA=ec4ddb8c260a102e9d55681c807fee36d92f4a53
# GITHUB_REF=refs/heads/master
# GITHUB_ACTOR=nutjob4life
# RUNNER_WORKSPACE=/home/runner/work/P5
# PWD=/github/workspace
# GITHUB_EVENT_NAME=push
# 🌳 ===== end env 
# 📁 ===== directory / follows
# bin/
# boot/
# dev/
# entrypoint.sh*
# etc/
# github/
# home/
# lib/
# lib64/
# media/
# mnt/
# opt/
# proc/
# root/
# run/
# sbin/
# srv/
# sys/
# tmp/
# usr/
# var/
# 📁 ===== directory / ends
# 📂 ===== workspace follows
# CHANGELOG.rst
# Dockerfile
# INSTALL.rst
# LICENSE.txt
# P5-EDRN.sublime-project
# README.md
# bootstrap.py
# data/
# dev.cfg
# docker-compose.yaml
# docker.cfg
# docs/
# etc/
# jenkins.cfg
# notes.rst
# ops.cfg.in
# src/
# support/
# templates/
# 📂 ===== workspace ends
# 🛑 the end
# Post job cleanup.
# [command]/usr/bin/git version
# git version 2.24.0
# [command]/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
# http.https://github.com/.extraheader
# [command]/usr/bin/git config --local --unset-all http.https://github.com/.extraheader
# Cleaning up orphan processes

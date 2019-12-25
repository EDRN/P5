#!/bin/sh -l
#

bootstrapURL="$1"
buildoutConfig="$2"

PATH=/usr/local/bin:/usr/bin:/bin
export PATH

cd "$GITHUB_WORKSPACE"

if [ \! -f $HOME/.buildout/default.cfg ]; then
    echo "The image is missing the buildout default.cfg"
    exit 1
fi

if [ \! -f bootstrap.py ]; then
    if [ \! -f bootstrap-buildout.py ]; then
        curl -L "$bootstrapURL" > bootstrap.py
    else
        mv bootstrap-buildout.py bootstrap.py
    fi
fi

python bootstrap.py -c "$buildoutConfig" && bin/buildout -c "$buildoutConfig"

# echo "🚗 ===== OK we are in ====="
# echo "⚙️ ===== args = $@ "
# echo "… bootstrapURL= $bootstrapURL"
# echo "… buildoutConfig = $buildoutConfig"
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

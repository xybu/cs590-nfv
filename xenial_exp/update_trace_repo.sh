#!/bin/bash

source ./config/config.$(hostname).ini

parent_dir=$(dirname $LOCAL_TRACE_REPO_DIR)
base_dir=$(basename $LOCAL_TRACE_REPO_DIR)

if [ -d "$LOCAL_TRACE_REPO_DIR" ] ; then
	echo -e "\033[94mUpdating local trace repository...\033[0m"
	hg pull --cwd=$LOCAL_TRACE_REPO_DIR
	hg update --cwd=$LOCAL_TRACE_REPO_DIR
else
	echo -e "\033[94mCloning local trace repository...\033[0m"
	hg clone --cwd=$parent_dir $REMOTE_TRACE_REPO_URL $base_dir
fi

echo -e "\033[92mDone.\033[0m"

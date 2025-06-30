#!/bin/bash
# https://github.com/arminbiere/runlim

CAT="{run.root}/programs/gcat.sh"

cd "$(dirname $0)"

#top -n 1 -b > top.txt

# change runlim version if necessary
[[ -e .finished ]] || "{run.root}/programs/runlim-2.0.0rc12" \
	--space-limit=20000 \
	--output-file=runsolver.watcher \
	--time-limit={run.timeout} \
	"{run.root}/programs/{run.solver}" -i "{run.file}" {run.encodings} {run.args} > runsolver.solver

touch .finished

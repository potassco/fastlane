#!/bin/bash
# https://github.com/arminbiere/runlim

cd "$(dirname $0)"

[[ -e .finished ]] || "{run.root}/programs/runlim" \
	--space-limit={run.memout} \
	--output-file=runsolver.watcher \
	--real-time-limit={run.timeout} \
	--single \
	--kill-delay=5120 \
	"{run.root}/programs/{run.solver}" {run.files} {run.encodings} {run.args} > runsolver.solver

touch .finished

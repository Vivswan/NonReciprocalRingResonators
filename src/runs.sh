#!/usr/bin/env bash

# simulation runs.

python run_simulation.py --lsf --slurm --num-resonators 1 --reciprocal 1 --frequency-sweep --components "r::phase:0" "r::coupling:0:1:10"
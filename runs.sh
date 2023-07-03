#!/usr/bin/env bash

# simulation 1
python src/run_simulation.py --lsf --slurm --not-record-all --num-resonators 1 --reciprocal 1 --frequency-sweep --components "r::phase:0" "r::coupling:0:1:4096"
python src/run_simulation.py --lsf --slurm --not-record-all --num-resonators 1 --reciprocal 0 --frequency-sweep --components "r::phase:0" "r::coupling:0:1:4096"
python src/run_simulation.py --lsf --slurm --not-record-all --num-resonators 1 --reciprocal -1 --frequency-sweep --components "r::phase:0" "r::coupling:0:1:4096"

#!/usr/bin/env bash

# simulation 1 (1 ring resonator, coupling=0-1, phase=0, Frequency sweep → A) [7806f8af]
python src/run_simulation.py --lsf --slurm --wg-insertion-loss 0 --dc-insertion-loss 0 --num-resonators 1 --reciprocal 1 --frequency-sweep --components "r::phase:0" "r::coupling:0:1:4096"
python src/run_simulation.py --lsf --slurm --wg-insertion-loss 0 --dc-insertion-loss 0 --num-resonators 1 --reciprocal 0 --frequency-sweep --components "r::phase:0" "r::coupling:0:1:4096"
python src/run_simulation.py --lsf --slurm --wg-insertion-loss 0 --dc-insertion-loss 0 --num-resonators 1 --reciprocal -1 --frequency-sweep --components "r::phase:0" "r::coupling:0:1:4096"

# simulation 2 (1 ring resonator, coupling=0-1, phase=0-2pi/-pi-pi, Frequency sweep) [868d1548]
python src/run_simulation.py --lsf --slurm --wg-insertion-loss 0 --dc-insertion-loss 0 --num-resonators 1 --reciprocal 0 --frequency-sweep --components "r::phase:0:6.28318530718:64" "r::coupling:0:1:64"
python src/run_simulation.py --lsf --slurm --wg-insertion-loss 0 --dc-insertion-loss 0 --num-resonators 1 --reciprocal -1 --frequency-sweep --components "r::phase:-3.14159265359:3.14159265359:64" "r::coupling:0:1:64"

#!/bin/bash
#SBATCH --job-name=@name@
#SBATCH --output=slurm_%x_%A.log
#SBATCH --mail-user=vis77@pitt.edu
#SBATCH --mail-type=ALL
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --cluster=smp
#SBATCH --partition=smp
#SBATCH --time=1-00:00:00
#SBATCH --chdir="/ihome/nyoungblood/vis77"
#SBATCH --requeue

source ~/.bashrc;
conda activate Ring-Resonator;

TarGzLocation="@DataDirectoryLocation@.tar.gz";
echo "TarGzLocation: $TarGzLocation"
TarName=$(basename $TarGzLocation | sed 's/.tar.gz//')
echo "TarName: $TarName"
ParentDir=$(dirname $TarGzLocation)
echo "ParentDir: $ParentDir"

cd $SLURM_SCRATCH || exit 1;

run_on_exit() {
  echo "";
  echo "####################################### Billing #######################################";
  echo "";
  sacct -M smp -j "$SLURM_JOBID" --format=AllocTRES%50,elapsed;
  echo "";

  echo "";
  echo "####################################### crc-job-stats.py #######################################";
  echo "";
  crc-job-stats;
  echo "";
  echo "!!!!!! Completed !!!!!!!";
  echo "";
}
trap run_on_exit EXIT;

echo "####################################### Main Program: Starting #######################################";

# if $TarGzLocation does not exist, then exit 1
if [ ! -f $TarGzLocation ]; then
  echo "tar.gz Location does not exist: $TarGzLocation";
  exit 1;
fi

echo "Copying $TarGzLocation to $SLURM_SCRATCH"
srun rsync -av $TarGzLocation $SLURM_SCRATCH || exit 1;

echo "Extracting $TarName.tar.gz"
srun tar -xzf $TarGzLocation || exit 1;

echo "Removing $TarName.tar.gz"
srun rm $TarName.tar.gz || exit 1;

echo "Running compile_data.py"
srun python @compile_data_py@ -cp -l ./$TarName || exit 1;

echo "Copying $TarName.sqlite to $ParentDir"
srun rsync -av "${TarName}.sqlite" "${ParentDir}/" || exit 1;

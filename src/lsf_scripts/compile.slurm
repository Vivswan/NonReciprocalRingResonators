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

source "${HOME}/.bashrc";
conda activate Ring-Resonator;

DataDirectoryLocation="@DataDirectoryLocation@";
ParentDir=$(dirname $DataDirectoryLocation)
TarName=$(basename $DataDirectoryLocation)
TarGzLocation="$DataDirectoryLocation.tar.gz";

echo "";
echo "DataDirectoryLocation: $DataDirectoryLocation"
echo "ParentDir: $ParentDir"
echo "TarName: $TarName"
echo "TarGzLocation: $TarGzLocation"

echo "";
echo "!!!!!! cd $SLURM_SCRATCH !!!!!!!"
cd "$SLURM_SCRATCH" || exit 1;

run_on_exit() {
  echo "";
  echo "####################################### Billing #######################################";
  echo "";
  sacct -M "$SLURM_CLUSTER_NAME" -j "$SLURM_JOBID" --format=AllocTRES%50,elapsed;
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

if [ ! -f "$TarGzLocation" ]; then
  if [ ! -d "$DataDirectoryLocation" ]; then
    echo "";
    echo "Error: '$TarGzLocation' does not exist and '$DataDirectoryLocation' is not a directory"
    exit 1;
  fi

  echo "";
  echo "!!!!!! Copying '${DataDirectoryLocation}' to '${SLURM_SCRATCH}/' !!!!!!!"
  srun rsync -av $DataDirectoryLocation "${SLURM_SCRATCH}/" || exit 1;
  
  echo "";
  echo "!!!!!! Compressing '${TarName}' !!!!!!!"
  srun tar -czvf "./${TarName}.tar.gz" "${TarName}" || exit 1;

  echo "";
  echo "!!!!!! Copying './${TarName}.tar.gz' to '${ParentDir}/' !!!!!!!"
  srun rsync -av "./${TarName}.tar.gz" "${ParentDir}/" || exit 1;

  echo "";
  echo "!!!!!! Removing '${DataDirectoryLocation}' !!!!!!!"
  srun rm -rfv $DataDirectoryLocation || exit 1;
else
  echo "";
  echo "!!!!!! Copying '${TarGzLocation}' to '${SLURM_SCRATCH}/' !!!!!!!"
  srun rsync -av $TarGzLocation "${SLURM_SCRATCH}/" || exit 1;

  echo "";
  echo "!!!!!! Extracting './${TarName}.tar.gz' !!!!!!!"
  srun tar -xzf "./${TarName}.tar.gz" || exit 1;
fi

echo "";
echo "!!!!!! Removing './${TarName}.tar.gz' !!!!!!!"
srun rm -v "./${TarName}.tar.gz" || exit 1;

echo "";
echo "!!!!!! Running compile_data.py !!!!!!!"
srun python @compile_data_py@ -opmc -l "./${TarName}" || exit 1;

echo "";
echo "!!!!!! Copying '${TarName}.sqlite' to '${ParentDir}/' !!!!!!!"
srun rsync -av "${TarName}.sqlite" "${ParentDir}/" || exit 1;

#!/usr/bin/env bash
#SBATCH -o %j.out
#SBATCH -p C064M0256G
#SBATCH --qos=high
#SBATCH -J dp_init_3C
#SBATCH --nodes=1
#SBATCH --ntasks=64
#SBATCH -t 120:00:00
#SBATCH --account hpc0006168316
#SBATCH --mail-type=ALL
#SBATCH --mail-user=LTC201806070316@outlook.com

# 获取开始时间戳
start_time=$(date +%s)

cd /lustre/home/2201210084/abacus_learn/example/2_abacus-dpgen/init/3C
nohup dpgen init_bulk param.json machine_wm.json &

# 获取结束时间戳
end_time=$(date +%s)

# 计算时间差
elapsed_time=$((end_time - start_time))

# 转换为小时、分钟、秒
hours=$((elapsed_time / 3600))
minutes=$(( (elapsed_time % 3600) / 60 ))
seconds=$((elapsed_time % 60))

# 输出执行时间
echo "Running dp_init_3C Successfully"
echo "Execution time: ${hours}h ${minutes}m ${seconds}s"
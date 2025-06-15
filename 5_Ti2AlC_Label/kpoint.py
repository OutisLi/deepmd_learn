"""
ABACUS K-point Spacing Test Script

This script performs a series of ABACUS calculations with different k-point spacings
to determine the optimal value for energy convergence. It automates the process of:
1. Running multiple ABACUS calculations with different kspacing values
2. Collecting energy results from each calculation
3. Generating plots of energy vs. kspacing

Usage:
    python kpoint.py cal    # Run calculations
    python kpoint.py post   # Process results and generate plot

Parameters:
    kspacing_min: Minimum k-point spacing (1/Bohr)
    kspacing_max: Maximum k-point spacing (1/Bohr)
    kspacing_interval: Step size for kspacing values (1/Bohr)
"""

import os
import sys
import time
import shutil
import subprocess
import pandas as pd
import matplotlib.pyplot as plt

# Define parameters for kspacing test
kspacing_min = 0.05  # 1/Bohr
kspacing_max = 0.3  # 1/Bohr
kspacing_interval = 0.02
current_dir = os.path.dirname(os.path.abspath(__file__))


def run_abacus(sr_path: str = None):
    """Run ABACUS calculation with proper environment setup.

    Args:
        sr_path (str, optional): script to be sourced before running abacus. Defaults to None.
    """
    # Set up the source command
    source_cmd = "source $HOME/Software/abacus-develop/toolchain/abacus_env.sh"
    if sr_path is not None:
        source_cmd = f"source {sr_path}"

    # Get environment variables after sourcing the script
    env_cmd = f"bash -c '{source_cmd} && env'"
    env_result = subprocess.run(env_cmd, shell=True, capture_output=True, text=True)

    if env_result.returncode != 0:
        print(f"Error sourcing environment: {env_result.stderr}")
        return

    # Parse environment variables
    env = {}
    for line in env_result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            env[key] = value

    start_time = time.time()

    # Run abacus with the sourced environment
    result = subprocess.run("abacus", shell=True, env=env, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error running abacus: {result.stderr}")
    else:
        end_time = time.time()
        elapsed_time = end_time - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        print(f"Abacus completed successfully, time used: {minutes} min {seconds} sec")


def function_submit():
    print(f"\nStarting kspacing test from {kspacing_min} to {kspacing_max} 1/Bohr with interval {kspacing_interval} 1/Bohr")
    found = False
    if os.path.exists(os.path.join(current_dir, "kpointtest_dir")):
        confirm = input("The folder 'kpointtest_dir' already exists, do you want to delete it?(y/n): ").strip().lower()
        if confirm == "y":
            shutil.rmtree(os.path.join(current_dir, "kpointtest_dir"))
        else:
            print("Using the existing 'kpointtest_dir'")
    os.makedirs(os.path.join(current_dir, "kpointtest_dir"), exist_ok=True)
    os.chdir(os.path.join(current_dir, "kpointtest_dir"))

    # Calculate the number of points to test
    num = int((kspacing_max - kspacing_min) // kspacing_interval + 1)
    print(f"\nTesting kspacing ({num} points)")

    for i in range(num):
        kspacing = round(kspacing_min + kspacing_interval * i, 3)
        dir_name = f"kspacing_{kspacing}"

        # Check if the directory already exists
        if os.path.exists(os.path.join(current_dir, "kpointtest_dir", dir_name)):
            print(f"-> Skipping kspacing = {kspacing} 1/Bohr (already computed)")
            continue

        print(f"-> Processing kspacing = {kspacing} 1/Bohr ({i + 1}/{num})")
        os.mkdir(os.path.join(current_dir, "kpointtest_dir", dir_name))
        os.chdir(os.path.join(current_dir, "kpointtest_dir", dir_name))
        os.system(f"cp -r `find {current_dir}/scf -maxdepth 1 -type f` . ")
        with open(os.path.join(current_dir, "kpointtest_dir", dir_name, "INPUT"), "r") as file:
            lines = file.readlines()
        for t, line in enumerate(lines):
            if "kspacing" in line:
                lines[t] = f"kspacing                {kspacing}\n"
                found = True
                break
        if not found:
            lines.append(f"kspacing                {kspacing}\n")
        with open(os.path.join(current_dir, "kpointtest_dir", dir_name, "INPUT"), "w") as file:
            file.writelines(lines)
        run_abacus()
        os.chdir(os.path.join(current_dir, "kpointtest_dir"))
    print("\nAll calculations completed!")


def function_postprocessing():
    print("\nProcessing calculation results...")
    name = "ABACUS"
    os.chdir(os.path.join(current_dir, "kpointtest_dir"))
    first_dir = f"kspacing_{kspacing_min}"
    with open(os.path.join(first_dir, "INPUT"), "r") as file:
        lines = file.readlines()
    for i, line in enumerate(lines):
        if "suffix" in line:
            columns = line.split()
            name = columns[1]

    print(f"\nProcessing results")
    energy_file = f"energy"
    num = int((kspacing_max - kspacing_min) // kspacing_interval + 1)

    with open(energy_file, "w") as outfile:
        for i in range(num):
            kspacing = round(kspacing_min + kspacing_interval * i, 3)
            dir_name = f"kspacing_{kspacing}"
            if not os.path.exists(os.path.join(dir_name, f"OUT.{name}")):
                print(f"The {dir_name}/OUT.{name} file does not exist")
                exit()
            os.system(
                f"grep E_KohnSham {os.path.join(dir_name, f'OUT.{name}', 'running_scf.log')} -A0| tail -n1" + " | awk '{print $3}' >> temp_energy"
            )
            with open("temp_energy", "r") as infile:
                energy = infile.read().strip()
            outfile.write(f"{kspacing},{energy}\n")
            os.remove("temp_energy")
    print("Results processed successfully!")


def generate_plot():
    os.chdir(os.path.join(current_dir, "kpointtest_dir"))
    print("\nGenerating plots...")

    # Create a figure
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))

    energy_file = f"energy"
    df = pd.read_csv(energy_file, header=None)

    # Plot
    ax.plot(df.iloc[:, 0], df.iloc[:, 1], marker="o")
    ax.set_title("kspacing")
    ax.set_xlabel("kspacing")
    ax.set_ylabel("Energy / eV")
    ax.grid(True)

    plt.tight_layout()
    plt.savefig("kpoint_plot.png", format="png", dpi=300)
    print("Plot saved as kpoint_plot.png")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        function_submit()
        function_postprocessing()
        generate_plot()
    elif len(sys.argv) == 2:
        if sys.argv[1] == "cal":
            function_submit()
        elif sys.argv[1] == "post":
            function_postprocessing()
            generate_plot()
    else:
        print("Usage: python kpoint.py [cal|post]")
        print("  cal  - Run calculations")
        print("  post - Process results and generate plot")

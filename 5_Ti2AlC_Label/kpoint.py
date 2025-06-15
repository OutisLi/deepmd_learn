"""
ABACUS K-point Spacing Test Script

This script performs a series of ABACUS calculations with different k-point spacings
to determine the optimal value for energy convergence. It automates the process of:
1. Running multiple ABACUS calculations with different kspacing values
2. Collecting energy results from each calculation
3. Generating plots of energy vs. kspacing for each direction

Usage:
    python kpoint.py cal    # Run calculations
    python kpoint.py post   # Process results and generate plot

Parameters:
    kspacing_min: Minimum k-point spacing for x,y,z directions (1/Bohr)
    kspacing_max: Maximum k-point spacing for x,y,z directions (1/Bohr)
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
kspacing_min = [0.09, 0.09, 0.24]  # [x, y, z]
kspacing_max = [0.24, 0.24, 0.24]  # [x, y, z]
kspacing_interval = 0.03
current_dir = os.path.dirname(os.path.abspath(__file__))


def run_abacus():
    """Run ABACUS calculation with proper environment setup."""
    env = os.environ.copy()
    env["PATH"] = f"{os.environ['HOME']}/Software/abacus-develop/bin:" + env["PATH"]

    start_time = time.time()

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

    # Create tests for each direction
    for direction in range(3):  # x, y, z
        # Check if this direction needs testing
        if kspacing_min[direction] == kspacing_max[direction]:
            print(f"\nSkipping {['x', 'y', 'z'][direction]} direction (min equals max)")
            continue

        # Calculate the number of points to test for this direction
        num = int((kspacing_max[direction] - kspacing_min[direction]) // kspacing_interval + 1)
        print(f"\nTesting kspacing in {['x', 'y', 'z'][direction]} direction ({num} points)")

        for i in range(num):
            kspacing = kspacing_min.copy()
            kspacing[direction] = round(kspacing_min[direction] + kspacing_interval * i, 3)
            dir_name = f"kspacing_{kspacing[0]}_{kspacing[1]}_{kspacing[2]}"

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
                    lines[t] = f"kspacing                {kspacing[0]} {kspacing[1]} {kspacing[2]}\n"
                    found = True
                    break
            if not found:
                lines.append(f"kspacing                {kspacing[0]} {kspacing[1]} {kspacing[2]}\n")
            with open(os.path.join(current_dir, "kpointtest_dir", dir_name, "INPUT"), "w") as file:
                file.writelines(lines)
            run_abacus()
            os.chdir(os.path.join(current_dir, "kpointtest_dir"))
    print("\nAll calculations completed!")


def function_postprocessing():
    print("\nProcessing calculation results...")
    name = "ABACUS"
    os.chdir(os.path.join(current_dir, "kpointtest_dir"))
    first_dir = f"kspacing_{kspacing_min[0]}_{kspacing_min[1]}_{kspacing_min[2]}"
    with open(os.path.join(first_dir, "INPUT"), "r") as file:
        lines = file.readlines()
    for i, line in enumerate(lines):
        if "suffix" in line:
            columns = line.split()
            name = columns[1]

    # Process results for each direction
    for direction in range(3):  # x, y, z
        # Check if this direction needs processing
        if kspacing_min[direction] == kspacing_max[direction]:
            print(f"\nSkipping results processing for {['x', 'y', 'z'][direction]} direction (min equals max)")
            continue

        print(f"\nProcessing results for {['x', 'y', 'z'][direction]} direction")
        energy_file = f"energy_{['x', 'y', 'z'][direction]}"
        num = int((kspacing_max[direction] - kspacing_min[direction]) // kspacing_interval + 1)

        with open(energy_file, "w") as outfile:
            for i in range(num):
                kspacing = kspacing_min.copy()
                kspacing[direction] = round(kspacing_min[direction] + kspacing_interval * i, 3)
                dir_name = f"kspacing_{kspacing[0]}_{kspacing[1]}_{kspacing[2]}"
                if not os.path.exists(os.path.join(dir_name, f"OUT.{name}")):
                    print(f"The {dir_name}/OUT.{name} file does not exist")
                    exit()
                os.system(
                    f"grep E_KohnSham {os.path.join(dir_name, f'OUT.{name}', 'running_scf.log')} -A0| tail -n1" + " | awk '{print $3}' >> temp_energy"
                )
                with open("temp_energy", "r") as infile:
                    energy = infile.read().strip()
                outfile.write(f"{kspacing[direction]},{energy}\n")
                os.remove("temp_energy")
    print("Results processed successfully!")


def generate_plot():
    os.chdir(os.path.join(current_dir, "kpointtest_dir"))
    print("\nGenerating plots...")

    # Calculate the number of directions to plot
    directions_to_plot = [d for d in range(3) if kspacing_min[d] != kspacing_max[d]]
    if not directions_to_plot:
        print("No directions to plot (all min values equal max values)")
        return

    # Create a large figure with the required subplots
    fig, axes = plt.subplots(1, len(directions_to_plot), figsize=(5 * len(directions_to_plot), 5))
    if len(directions_to_plot) == 1:
        axes = [axes]  # Ensure axes is a list

    for idx, direction in enumerate(directions_to_plot):
        energy_file = f"energy_{['x', 'y', 'z'][direction]}"
        df = pd.read_csv(energy_file, header=None)

        # Plot for each direction
        axes[idx].plot(df.iloc[:, 0], df.iloc[:, 1], marker="o")
        axes[idx].set_title(f"kspacing_{['x', 'y', 'z'][direction]}")
        axes[idx].set_xlabel(f"kspacing_{['x', 'y', 'z'][direction]}")
        axes[idx].set_ylabel("Energy / eV")
        axes[idx].grid(True)

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

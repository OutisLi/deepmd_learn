"""
ABACUS Plane Wave Cutoff Energy Test Script

This script performs a series of ABACUS calculations with different plane wave cutoff energies (ecut)
to determine the optimal value for energy convergence. It automates the process of:
1. Running multiple ABACUS calculations with different ecut values
2. Collecting energy results from each calculation
3. Generating a plot of energy vs. ecut

NOTE: This is only valid for pw basis type

Usage:
    python ecut.py cal    # Run calculations
    python ecut.py post   # Process results and generate plot

Parameters:
    ecut_min: Minimum cutoff energy (Ry)
    ecut_max: Maximum cutoff energy (Ry)
    ecut_interval: Step size for ecut values (Ry)
"""

import os
import sys
import time
import shutil
import subprocess
import pandas as pd
import matplotlib.pyplot as plt

# Define parameters for ecut test
ecut_min = 50.0
ecut_max = 250.0
ecut_interval = 10.0
num = int((float(ecut_max) - float(ecut_min)) // float(ecut_interval) + 1)
current_dir = os.path.dirname(os.path.abspath(__file__))


def function_submit():
    print(f"\nStarting ecut test from {ecut_min} to {ecut_max} Ry with interval {ecut_interval} Ry")
    # Check if the result directory exists and handle user input
    if os.path.exists(os.path.join(current_dir, "ecuttest_dir")):
        confirm = input("The folder 'ecuttest_dir' already exists, do you want to delete it?(y/n): ").strip().lower()
        if confirm == "y":
            shutil.rmtree(os.path.join(current_dir, "ecuttest_dir"))
        else:
            print("Using the existing 'ecuttest_dir'")
    os.makedirs(os.path.join(current_dir, "ecuttest_dir"), exist_ok=True)
    os.chdir(os.path.join(current_dir, "ecuttest_dir"))
    for i in range(num):
        ecut = float(ecut_min) + float(ecut_interval) * i
        print(f"-> Processing ecut = {ecut} Ry ({i + 1}/{num})")
        ecut_dir = os.path.join(current_dir, "ecuttest_dir", f"{ecut}")
        if os.path.exists(ecut_dir):
            print(f"   Directory {ecut} already exists, skipping...")
            continue
        os.mkdir(ecut_dir)
        os.chdir(ecut_dir)
        os.system(f"cp -r `find {current_dir}/scf -maxdepth 1 -type f` . ")
        with open(os.path.join(current_dir, "ecuttest_dir", f"{ecut}", "INPUT"), "r") as file:
            lines = file.readlines()
        for i, line in enumerate(lines):
            if "ecutwfc" in line:
                lines[i] = f"ecutwfc                 {ecut}\n"
        # ecuttest is only valid for pw basis type
        for i, line in enumerate(lines):
            if "basis_type" in line:
                lines[i] = f"basis_type              pw\n"
        # for pw basis type, use cg solver
        for i, line in enumerate(lines):
            if "ks_solver" in line:
                lines[i] = f"ks_solver               cg\n"
        with open(os.path.join(current_dir, "ecuttest_dir", f"{ecut}", "INPUT"), "w") as file:
            file.writelines(lines)
        run_abacus()
    print("\nAll calculations completed!")


def function_postprocessing():
    print("\nProcessing calculation results...")
    # Process the results and generate a plot
    name = "ABACUS"
    os.chdir(os.path.join(current_dir, "ecuttest_dir"))
    with open(os.path.join(f"{ecut_min}", "INPUT"), "r") as file:
        lines = file.readlines()
    for i, line in enumerate(lines):
        if "suffix" in line:
            columns = line.split()
            name = columns[1]
    for i in range(num):
        ecut = float(ecut_min) + float(ecut_interval) * i
        if not os.path.exists(os.path.join(f"{ecut}", f"OUT.{name}")):
            print(f"The {ecut}/OUT.{name} file does not exist, skipping...")
            continue
        os.system(f"grep E_KohnSham {os.path.join(f'{ecut}', f'OUT.{name}', 'running_scf.log')} -A0| tail -n1 | awk '{{print $3}}' >> energy")
    t = 0
    with open("energy", "r") as infile, open("ecuttest_result.csv", "w") as outfile:
        for line in infile:
            ecut = float(ecut_min) + float(ecut_interval) * t
            outfile.write(f"{ecut}" + "," + line)
            t = t + 1
    os.remove("./energy")
    print("Results processed successfully!")


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


def generate_plot():
    os.chdir(os.path.join(current_dir, "ecuttest_dir"))
    print("\nGenerating plot...")
    df = pd.read_csv("ecuttest_result.csv", header=None)
    plt.figure(figsize=(10, 6))
    plt.plot(df.iloc[:, 0], df.iloc[:, 1], marker="o")
    plt.title("Energy_Cutoff_Test")
    plt.xlabel("ecutwfc / Ry")
    plt.ylabel("Energy / eV")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("ecut_plot.png", format="png", dpi=300)
    print("Plot saved as ecut_plot.png")


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
        print("Usage: python ecut.py [cal|post]")
        print("  cal  - Run calculations")
        print("  post - Process results and generate plot")

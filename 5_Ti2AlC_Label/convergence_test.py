"""
ABACUS Convergence Test Suite

This script provides a unified interface for performing convergence tests in ABACUS calculations.
It combines three types of tests:
1. K-point spacing convergence test (uniform spacing)
2. Plane wave cutoff energy (ecut) convergence test
3. K-point spacing convergence test (directional spacing for x, y, z)

The script automates the process of:
- Running multiple ABACUS calculations with different parameter values
- Collecting energy results from each calculation
- Generating plots of energy vs. parameter values

Usage:
    python convergence_test.py kpoint cal        # Run k-point spacing calculations
    python convergence_test.py kpoint post       # Process k-point results and generate plot
    python convergence_test.py ecut cal          # Run ecut calculations
    python convergence_test.py ecut post         # Process ecut results and generate plot
    python convergence_test.py kpoint_xyz cal    # Run directional k-point calculations
    python convergence_test.py kpoint_xyz post   # Process directional k-point results and generate plot

Parameters can be modified in the class initialization or by creating custom instances.
"""

import os
import sys
import time
import shutil
import subprocess
import pandas as pd
import matplotlib.pyplot as plt


class ABACUSConvergenceTest:
    """
    A unified class for performing ABACUS convergence tests.

    This class provides methods for testing convergence of different parameters:
    - K-point spacing (uniform)
    - Plane wave cutoff energy (ecut)
    - K-point spacing (directional for x, y, z)

    Attributes:
        current_dir (str): Current working directory
        kspacing_min (float): Minimum k-point spacing for uniform test
        kspacing_max (float): Maximum k-point spacing for uniform test
        kspacing_interval (float): Interval for k-point spacing test
        ecut_min (float): Minimum cutoff energy for ecut test
        ecut_max (float): Maximum cutoff energy for ecut test
        ecut_interval (float): Interval for ecut test
        kspacing_min_xyz (list): Minimum k-point spacing for each direction [x, y, z]
        kspacing_max_xyz (list): Maximum k-point spacing for each direction [x, y, z]
        kspacing_interval_xyz (float): Interval for directional k-point test
    """

    def __init__(self, work_dir: str = None, sr_path: str = None):
        """Initialize the convergence test with default parameters.

        Args:
            work_dir (str, optional): Path to the working directory. Defaults to current directory.
            sr_path (str, optional): Path to the script to be sourced before running abacus. Defaults to None.
        """
        # Common parameters
        self.current_dir = os.path.dirname(os.path.abspath(__file__)) if work_dir is None else work_dir
        self.sr_path = sr_path

        # K-point spacing test parameters (uniform)
        self.kspacing_min = 0.1  # 1/Bohr
        self.kspacing_max = 0.3  # 1/Bohr
        self.kspacing_interval = 0.02

        # Ecut test parameters
        self.ecut_min = 50.0  # Ry
        self.ecut_max = 130.0  # Ry
        self.ecut_interval = 10.0

        # K-point spacing test parameters (directional)
        self.kspacing_min_xyz = [0.09, 0.09, 0.24]  # [x, y, z] in 1/Bohr
        self.kspacing_max_xyz = [0.24, 0.24, 0.24]  # [x, y, z] in 1/Bohr
        self.kspacing_interval_xyz = 0.03

    def run_abacus(self):
        """Run ABACUS calculation with proper environment setup."""
        # Set up the source command
        source_cmd = "source $HOME/Software/abacus-develop/toolchain/abacus_env.sh"
        if self.sr_path is not None:
            source_cmd = f"source {self.sr_path}"

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

    def kpoint_run(self, kspacing_min=None, kspacing_max=None, kspacing_interval=None):
        """
        Run k-point spacing convergence test calculations (uniform spacing).

        Args:
            kspacing_min (float, optional): Minimum k-point spacing (1/Bohr). Defaults to class attribute.
            kspacing_max (float, optional): Maximum k-point spacing (1/Bohr). Defaults to class attribute.
            kspacing_interval (float, optional): Interval for k-point spacing test (1/Bohr). Defaults to class attribute.
        """
        # Use provided parameters or fall back to class attributes
        kspacing_min = kspacing_min if kspacing_min is not None else self.kspacing_min
        kspacing_max = kspacing_max if kspacing_max is not None else self.kspacing_max
        kspacing_interval = kspacing_interval if kspacing_interval is not None else self.kspacing_interval

        # Store the parameters for later use in postprocessing
        self._kpoint_params = {"kspacing_min": kspacing_min, "kspacing_max": kspacing_max, "kspacing_interval": kspacing_interval}

        print(f"\nStarting kspacing test from {kspacing_min} to {kspacing_max} 1/Bohr with interval {kspacing_interval} 1/Bohr")
        found = False
        test_dir = os.path.join(self.current_dir, "kpointtest_dir")

        if os.path.exists(test_dir):
            confirm = input("The folder 'kpointtest_dir' already exists, do you want to delete it?(y/n): ").strip().lower()
            if confirm == "y":
                shutil.rmtree(test_dir)
            else:
                print("Using the existing 'kpointtest_dir'")
        os.makedirs(test_dir, exist_ok=True)
        os.chdir(test_dir)

        # Calculate the number of points to test
        num = int((kspacing_max - kspacing_min) // kspacing_interval + 1)
        print(f"\nTesting kspacing ({num} points)")

        for i in range(num):
            kspacing = round(kspacing_min + kspacing_interval * i, 3)
            dir_name = f"kspacing_{kspacing}"

            # Check if the directory already exists
            if os.path.exists(os.path.join(test_dir, dir_name)):
                print(f"-> Skipping kspacing = {kspacing} 1/Bohr (already computed)")
                continue

            print(f"-> Processing kspacing = {kspacing} 1/Bohr ({i + 1}/{num})")
            os.mkdir(os.path.join(test_dir, dir_name))
            os.chdir(os.path.join(test_dir, dir_name))
            os.system(f"cp -r `find {self.current_dir}/scf -maxdepth 1 -type f` . ")
            with open("INPUT", "r") as file:
                lines = file.readlines()
            for t, line in enumerate(lines):
                if "kspacing" in line:
                    lines[t] = f"kspacing                {kspacing}\n"
                    found = True
                    break
            if not found:
                lines.append(f"kspacing                {kspacing}\n")
            with open("INPUT", "w") as file:
                file.writelines(lines)
            self.run_abacus()
            os.chdir(test_dir)
        print("\nAll calculations completed!")

    def kpoint_postprocessing(self):
        """Process k-point spacing test results and generate data file."""
        print("\nProcessing calculation results...")
        name = "ABACUS"
        test_dir = os.path.join(self.current_dir, "kpointtest_dir")
        os.chdir(test_dir)

        # Use parameters from the previous submit call or default values
        if hasattr(self, "_kpoint_params"):
            kspacing_min = self._kpoint_params["kspacing_min"]
            kspacing_max = self._kpoint_params["kspacing_max"]
            kspacing_interval = self._kpoint_params["kspacing_interval"]
        else:
            kspacing_min = self.kspacing_min
            kspacing_max = self.kspacing_max
            kspacing_interval = self.kspacing_interval

        first_dir = f"kspacing_{kspacing_min}"
        with open(os.path.join(first_dir, "INPUT"), "r") as file:
            lines = file.readlines()
        for i, line in enumerate(lines):
            if "suffix" in line:
                columns = line.split()
                name = columns[1]

        print(f"\nProcessing results")
        energy_file = "energy"
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

    def kpoint_generate_plot(self, n_atoms=8):
        """Generate plot for k-point spacing convergence test.

        Args:
            n_atoms (int, optional): Number of atoms in the unit cell. Defaults to 8.
        """
        test_dir = os.path.join(self.current_dir, "kpointtest_dir")
        os.chdir(test_dir)
        print("\nGenerating plots...")

        # Create a figure
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))

        energy_file = "energy"
        df = pd.read_csv(energy_file, header=None)

        # Plot
        ax.plot(df.iloc[:, 0], df.iloc[:, 1] / n_atoms, marker="o")
        ax.set_title("kspacing")
        ax.set_xlabel("kspacing")
        ax.set_ylabel("Energy / eV / atom")
        ax.grid(True)

        # add axhline at leftmost point
        ax.axhline(y=df.iloc[0, 1] / n_atoms + 1e-3, color="red", linestyle="--")
        ax.axhline(y=df.iloc[0, 1] / n_atoms - 1e-3, color="red", linestyle="--")

        plt.tight_layout()
        plt.savefig("kpoint_plot.png", format="png", dpi=300)
        print("Plot saved as kpoint_plot.png")

    def ecut_run(self, ecut_min=None, ecut_max=None, ecut_interval=None):
        """
        Run plane wave cutoff energy convergence test calculations.

        Args:
            ecut_min (float, optional): Minimum cutoff energy (Ry). Defaults to class attribute.
            ecut_max (float, optional): Maximum cutoff energy (Ry). Defaults to class attribute.
            ecut_interval (float, optional): Interval for ecut test (Ry). Defaults to class attribute.
        """
        # Use provided parameters or fall back to class attributes
        ecut_min = ecut_min if ecut_min is not None else self.ecut_min
        ecut_max = ecut_max if ecut_max is not None else self.ecut_max
        ecut_interval = ecut_interval if ecut_interval is not None else self.ecut_interval

        # Store the parameters for later use in postprocessing
        self._ecut_params = {"ecut_min": ecut_min, "ecut_max": ecut_max, "ecut_interval": ecut_interval}

        print(f"\nStarting ecut test from {ecut_min} to {ecut_max} Ry with interval {ecut_interval} Ry")
        test_dir = os.path.join(self.current_dir, "ecuttest_dir")
        num = int((float(ecut_max) - float(ecut_min)) // float(ecut_interval) + 1)

        # Check if the result directory exists and handle user input
        if os.path.exists(test_dir):
            confirm = input("The folder 'ecuttest_dir' already exists, do you want to delete it?(y/n): ").strip().lower()
            if confirm == "y":
                shutil.rmtree(test_dir)
            else:
                print("Using the existing 'ecuttest_dir'")
        os.makedirs(test_dir, exist_ok=True)
        os.chdir(test_dir)

        for i in range(num):
            ecut = float(ecut_min) + float(ecut_interval) * i
            print(f"-> Processing ecut = {ecut} Ry ({i + 1}/{num})")
            ecut_dir = os.path.join(test_dir, f"{ecut}")
            if os.path.exists(ecut_dir):
                print(f"   Directory {ecut} already exists, skipping...")
                continue
            os.mkdir(ecut_dir)
            os.chdir(ecut_dir)
            os.system(f"cp -r `find {self.current_dir}/scf -maxdepth 1 -type f` . ")
            with open("INPUT", "r") as file:
                lines = file.readlines()
            for j, line in enumerate(lines):
                if "ecutwfc" in line:
                    lines[j] = f"ecutwfc                 {ecut}\n"
            # ecuttest is only valid for pw basis type
            for j, line in enumerate(lines):
                if "basis_type" in line:
                    lines[j] = f"basis_type              pw\n"
            # for pw basis type, use cg solver
            for j, line in enumerate(lines):
                if "ks_solver" in line:
                    lines[j] = f"ks_solver               cg\n"
            with open("INPUT", "w") as file:
                file.writelines(lines)
            self.run_abacus()
            os.chdir(test_dir)
        print("\nAll calculations completed!")

    def ecut_postprocessing(self):
        """Process ecut test results and generate data file."""
        print("\nProcessing calculation results...")
        # Process the results and generate a plot
        name = "ABACUS"
        test_dir = os.path.join(self.current_dir, "ecuttest_dir")
        os.chdir(test_dir)

        # Use parameters from the previous submit call or default values
        if hasattr(self, "_ecut_params"):
            ecut_min = self._ecut_params["ecut_min"]
            ecut_max = self._ecut_params["ecut_max"]
            ecut_interval = self._ecut_params["ecut_interval"]
        else:
            ecut_min = self.ecut_min
            ecut_max = self.ecut_max
            ecut_interval = self.ecut_interval

        num = int((float(ecut_max) - float(ecut_min)) // float(ecut_interval) + 1)

        # Get the first ecut value to find the INPUT file
        first_ecut = float(ecut_min)
        with open(os.path.join(f"{first_ecut}", "INPUT"), "r") as file:
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

    def ecut_generate_plot(self, n_atoms=8):
        """Generate plot for ecut convergence test.

        Args:
            n_atoms (int, optional): Number of atoms in the unit cell. Defaults to 8.
        """
        test_dir = os.path.join(self.current_dir, "ecuttest_dir")
        os.chdir(test_dir)
        print("\nGenerating plot...")
        df = pd.read_csv("ecuttest_result.csv", header=None)
        plt.figure(figsize=(10, 6))
        plt.plot(df.iloc[:, 0], df.iloc[:, 1] / n_atoms, marker="o")
        plt.title("Energy_Cutoff_Test")
        plt.xlabel("ecutwfc / Ry")
        plt.ylabel("Energy / eV / atom")
        plt.grid(True)

        # add axhline at leftmost point
        plt.axhline(y=df.iloc[0, 1] / n_atoms + 1e-3, color="red", linestyle="--")
        plt.axhline(y=df.iloc[0, 1] / n_atoms - 1e-3, color="red", linestyle="--")

        plt.tight_layout()
        plt.savefig("ecut_plot.png", format="png", dpi=300)
        print("Plot saved as ecut_plot.png")

    def kpoint_xyz_run(self, kspacing_min_xyz=None, kspacing_max_xyz=None, kspacing_interval_xyz=None):
        """
        Run directional k-point spacing convergence test calculations.

        Args:
            kspacing_min_xyz (list, optional): Minimum k-point spacing for each direction [x, y, z] (1/Bohr). Defaults to class attribute.
            kspacing_max_xyz (list, optional): Maximum k-point spacing for each direction [x, y, z] (1/Bohr). Defaults to class attribute.
            kspacing_interval_xyz (float, optional): Interval for directional k-point test (1/Bohr). Defaults to class attribute.
        """
        # Use provided parameters or fall back to class attributes
        kspacing_min_xyz = kspacing_min_xyz if kspacing_min_xyz is not None else self.kspacing_min_xyz
        kspacing_max_xyz = kspacing_max_xyz if kspacing_max_xyz is not None else self.kspacing_max_xyz
        kspacing_interval_xyz = kspacing_interval_xyz if kspacing_interval_xyz is not None else self.kspacing_interval_xyz

        # Store the parameters for later use in postprocessing
        self._kpoint_xyz_params = {
            "kspacing_min_xyz": kspacing_min_xyz,
            "kspacing_max_xyz": kspacing_max_xyz,
            "kspacing_interval_xyz": kspacing_interval_xyz,
        }

        print(f"\nStarting kspacing test from {kspacing_min_xyz} to {kspacing_max_xyz} 1/Bohr with interval {kspacing_interval_xyz} 1/Bohr")
        found = False
        test_dir = os.path.join(self.current_dir, "kpointtest_dir")

        if os.path.exists(test_dir):
            confirm = input("The folder 'kpointtest_dir' already exists, do you want to delete it?(y/n): ").strip().lower()
            if confirm == "y":
                shutil.rmtree(test_dir)
            else:
                print("Using the existing 'kpointtest_dir'")
        os.makedirs(test_dir, exist_ok=True)
        os.chdir(test_dir)

        # Create tests for each direction
        for direction in range(3):  # x, y, z
            # Check if this direction needs testing
            if kspacing_min_xyz[direction] == kspacing_max_xyz[direction]:
                print(f"\nSkipping {['x', 'y', 'z'][direction]} direction (min equals max)")
                continue

            # Calculate the number of points to test for this direction
            num = int((kspacing_max_xyz[direction] - kspacing_min_xyz[direction]) // kspacing_interval_xyz + 1)
            print(f"\nTesting kspacing in {['x', 'y', 'z'][direction]} direction ({num} points)")

            for i in range(num):
                kspacing = kspacing_min_xyz.copy()
                kspacing[direction] = round(kspacing_min_xyz[direction] + kspacing_interval_xyz * i, 3)
                dir_name = f"kspacing_{kspacing[0]}_{kspacing[1]}_{kspacing[2]}"

                # Check if the directory already exists
                if os.path.exists(os.path.join(test_dir, dir_name)):
                    print(f"-> Skipping kspacing = {kspacing} 1/Bohr (already computed)")
                    continue

                print(f"-> Processing kspacing = {kspacing} 1/Bohr ({i + 1}/{num})")
                os.mkdir(os.path.join(test_dir, dir_name))
                os.chdir(os.path.join(test_dir, dir_name))
                os.system(f"cp -r `find {self.current_dir}/scf -maxdepth 1 -type f` . ")
                with open("INPUT", "r") as file:
                    lines = file.readlines()
                for t, line in enumerate(lines):
                    if "kspacing" in line:
                        lines[t] = f"kspacing                {kspacing[0]} {kspacing[1]} {kspacing[2]}\n"
                        found = True
                        break
                if not found:
                    lines.append(f"kspacing                {kspacing[0]} {kspacing[1]} {kspacing[2]}\n")
                with open("INPUT", "w") as file:
                    file.writelines(lines)
                self.run_abacus()
                os.chdir(test_dir)
        print("\nAll calculations completed!")

    def kpoint_xyz_postprocessing(self):
        """Process directional k-point spacing test results and generate data files."""
        print("\nProcessing calculation results...")
        name = "ABACUS"
        test_dir = os.path.join(self.current_dir, "kpointtest_dir")
        os.chdir(test_dir)

        # Use parameters from the previous run call or default values
        if hasattr(self, "_kpoint_xyz_params"):
            kspacing_min_xyz = self._kpoint_xyz_params["kspacing_min_xyz"]
            kspacing_max_xyz = self._kpoint_xyz_params["kspacing_max_xyz"]
            kspacing_interval_xyz = self._kpoint_xyz_params["kspacing_interval_xyz"]
        else:
            kspacing_min_xyz = self.kspacing_min_xyz
            kspacing_max_xyz = self.kspacing_max_xyz
            kspacing_interval_xyz = self.kspacing_interval_xyz

        first_dir = f"kspacing_{kspacing_min_xyz[0]}_{kspacing_min_xyz[1]}_{kspacing_min_xyz[2]}"
        with open(os.path.join(first_dir, "INPUT"), "r") as file:
            lines = file.readlines()
        for i, line in enumerate(lines):
            if "suffix" in line:
                columns = line.split()
                name = columns[1]

        # Process results for each direction
        for direction in range(3):  # x, y, z
            # Check if this direction needs processing
            if kspacing_min_xyz[direction] == kspacing_max_xyz[direction]:
                print(f"\nSkipping results processing for {['x', 'y', 'z'][direction]} direction (min equals max)")
                continue

            print(f"\nProcessing results for {['x', 'y', 'z'][direction]} direction")
            energy_file = f"energy_{['x', 'y', 'z'][direction]}"
            num = int((kspacing_max_xyz[direction] - kspacing_min_xyz[direction]) // kspacing_interval_xyz + 1)

            with open(energy_file, "w") as outfile:
                for i in range(num):
                    kspacing = kspacing_min_xyz.copy()
                    kspacing[direction] = round(kspacing_min_xyz[direction] + kspacing_interval_xyz * i, 3)
                    dir_name = f"kspacing_{kspacing[0]}_{kspacing[1]}_{kspacing[2]}"
                    if not os.path.exists(os.path.join(dir_name, f"OUT.{name}")):
                        print(f"The {dir_name}/OUT.{name} file does not exist")
                        exit()
                    os.system(
                        f"grep E_KohnSham {os.path.join(dir_name, f'OUT.{name}', 'running_scf.log')} -A0| tail -n1"
                        + " | awk '{print $3}' >> temp_energy"
                    )
                    with open("temp_energy", "r") as infile:
                        energy = infile.read().strip()
                    outfile.write(f"{kspacing[direction]},{energy}\n")
                    os.remove("temp_energy")
        print("Results processed successfully!")

    def kpoint_xyz_generate_plot(self, n_atoms=8):
        """Generate plots for directional k-point spacing convergence test.

        Args:
            n_atoms (int, optional): Number of atoms in the unit cell. Defaults to 8.
        """
        test_dir = os.path.join(self.current_dir, "kpointtest_dir")
        os.chdir(test_dir)
        print("\nGenerating plots...")

        # Use parameters from the previous run call or default values
        if hasattr(self, "_kpoint_xyz_params"):
            kspacing_min_xyz = self._kpoint_xyz_params["kspacing_min_xyz"]
            kspacing_max_xyz = self._kpoint_xyz_params["kspacing_max_xyz"]
        else:
            kspacing_min_xyz = self.kspacing_min_xyz
            kspacing_max_xyz = self.kspacing_max_xyz

        # Calculate the number of directions to plot
        directions_to_plot = [d for d in range(3) if kspacing_min_xyz[d] != kspacing_max_xyz[d]]
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
            axes[idx].plot(df.iloc[:, 0], df.iloc[:, 1] / n_atoms, marker="o")
            axes[idx].set_title(f"kspacing_{['x', 'y', 'z'][direction]}")
            axes[idx].set_xlabel(f"kspacing_{['x', 'y', 'z'][direction]}")
            axes[idx].set_ylabel("Energy / eV / atom")
            axes[idx].grid(True)

            # add axhline at leftmost point
            axes[idx].axhline(y=df.iloc[0, 1] / n_atoms + 1e-3, color="red", linestyle="--")
            axes[idx].axhline(y=df.iloc[0, 1] / n_atoms - 1e-3, color="red", linestyle="--")

        plt.tight_layout()
        plt.savefig("kpoint_plot.png", format="png", dpi=300)
        print("Plot saved as kpoint_plot.png")

    def run_test(self, test_type, operation):
        """
        Run a specific convergence test.

        Args:
            test_type (str): Type of test ('kpoint', 'ecut', 'kpoint_xyz')
            operation (str): Operation to perform ('cal' for calculation, 'post' for post-processing)
        """
        if test_type == "kpoint":
            if operation == "cal":
                self.kpoint_run()
            elif operation == "post":
                self.kpoint_postprocessing()
                self.kpoint_generate_plot(n_atoms=8)
            else:
                self._print_usage()
        elif test_type == "ecut":
            if operation == "cal":
                self.ecut_run()
            elif operation == "post":
                self.ecut_postprocessing()
                self.ecut_generate_plot(n_atoms=8)
            else:
                self._print_usage()
        elif test_type == "kpoint_xyz":
            if operation == "cal":
                self.kpoint_xyz_run()
            elif operation == "post":
                self.kpoint_xyz_postprocessing()
                self.kpoint_xyz_generate_plot(n_atoms=8)
            else:
                self._print_usage()
        else:
            self._print_usage()

    def run_full_test(self, test_type):
        """
        Run both calculation and post-processing for a specific test type.

        Args:
            test_type (str): Type of test ('kpoint', 'ecut', 'kpoint_xyz')
        """
        if test_type == "kpoint":
            self.kpoint_run()
            self.kpoint_postprocessing()
            self.kpoint_generate_plot(n_atoms=8)
        elif test_type == "ecut":
            self.ecut_run()
            self.ecut_postprocessing()
            self.ecut_generate_plot(n_atoms=8)
        elif test_type == "kpoint_xyz":
            self.kpoint_xyz_run()
            self.kpoint_xyz_postprocessing()
            self.kpoint_xyz_generate_plot(n_atoms=8)
        else:
            self._print_usage()

    def _print_usage(self):
        """Print usage information."""
        print("Usage: python convergence_test.py <test_type> [operation]")
        print("  test_type:")
        print("    kpoint     - K-point spacing convergence test (uniform)")
        print("    ecut       - Plane wave cutoff energy convergence test")
        print("    kpoint_xyz - K-point spacing convergence test (directional)")
        print("  operation:")
        print("    cal        - Run calculations only")
        print("    post       - Process results and generate plot only")
        print("    (no operation) - Run both calculations and post-processing")


if __name__ == "__main__":
    convergence_test = ABACUSConvergenceTest()

    if len(sys.argv) == 2:
        # Run full test (both calculation and post-processing)
        test_type = sys.argv[1]
        convergence_test.run_full_test(test_type)
    elif len(sys.argv) == 3:
        # Run specific operation
        test_type = sys.argv[1]
        operation = sys.argv[2]
        convergence_test.run_test(test_type, operation)
    else:
        convergence_test._print_usage()

import os
import re
import shutil
import pandas as pd
import matplotlib.pyplot as plt
import sys

kspacing_min = 0.1
kspacing_max = 0.3
kspacing_interval = 0.02
num = int((kspacing_max - kspacing_min) // kspacing_interval + 1)
current_path = os.path.dirname(os.path.abspath(__file__))


def function_submit():
    found = False
    if os.path.exists("./kpointtest_result"):
        confirm = input("The folder 'kpointtest_result' already exists, do you want to delete it?(y/n): ").strip().lower()
        if confirm == "y":
            shutil.rmtree("./kpointtest_result")
        else:
            exit()
    os.makedirs("kpointtest_result")
    os.chdir("kpointtest_result")
    for i in range(num):
        kspacing = round(kspacing_min + kspacing_interval * i, 2)
        os.mkdir(f"{kspacing}")
        os.chdir(f"{kspacing}")
        os.system("cp -r `find ../../ -maxdepth 1 -type f` . ")
        with open("./INPUT", "r") as file:
            lines = file.readlines()
        for t, line in enumerate(lines):
            if "kspacing" in line:
                lines[t] = f"kspacing                {kspacing}"
                found = True
                break
        if not found:
            lines.append(f"kspacing                {kspacing}")
        with open("./INPUT", "w") as file:
            file.writelines(lines)
        os.system("OMP_NUM_THREADS=2 mpirun -np 16 abacus")
        os.chdir("../")


def function_postprocessing():
    name = "ABACUS"
    with open(f"{kspacing_min}/INPUT", "r") as file:
        lines = file.readlines()
    for i, line in enumerate(lines):
        if "suffix" in line:
            columns = line.split()
            name = columns[1]
    for i in range(num):
        kspacing = round(kspacing_min + kspacing_interval * i, 2)
        if not os.path.exists(f"{kspacing}/OUT.{name}"):
            print(f"The {kspacing}/OUT.{name} file does not exist")
            exit()
        os.system(f"grep E_KohnSham {kspacing}/OUT.{name}/running_scf.log -A0| tail -n1" + " | awk '{print $3}' >> energy")
    t = 0
    with open("energy", "r") as infile, open("kpointtest", "w") as outfile:
        for line in infile:
            kspacing = round(kspacing_min + kspacing_interval * t, 2)
            outfile.write(f"{kspacing}" + "    " + line)
            t = t + 1
    os.remove("./energy")


if len(sys.argv) > 1:
    if sys.argv[1] == "cal":
        function_submit()
    elif sys.argv[1] == "post":
        function_postprocessing()
        df = pd.read_csv("kpointtest", header=None, delim_whitespace=True)
        plt.figure(figsize=(10, 6))
        plt.plot(df.iloc[:, 0], df.iloc[:, 1], marker="o")
        plt.title("kpoint_test")
        plt.xlabel("kspacing")
        plt.ylabel("Energy / eV")
        plt.grid(True)
        plt.savefig("kpoint_plot.png", format="png", dpi=300)
        plt.show()

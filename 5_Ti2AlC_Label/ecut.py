import os
import re
import shutil
import sys
import pandas as pd
import matplotlib.pyplot as plt

ecut_min = 90.0
ecut_max = 130.0
ecut_interval = 5.0
num = int((float(ecut_max) - float(ecut_min)) // float(ecut_interval) + 1)
current_path = os.path.dirname(os.path.abspath(__file__))


def function_submit():
    if os.path.exists("./ecuttest_result"):
        confirm = input("The folder 'ecuttest_result' already exists, do you want to delete it?(y/n): ").strip().lower()
        if confirm == "y":
            shutil.rmtree("./ecuttest_result")
        else:
            exit()
    os.makedirs("ecuttest_result")
    os.chdir("ecuttest_result")
    for i in range(num):
        ecut = float(ecut_min) + float(ecut_interval) * i
        os.mkdir(f"{ecut}")
        os.chdir(f"{ecut}")
        os.system("cp -r `find ../../ -maxdepth 1 -type f` . ")
        with open("./INPUT", "r") as file:
            lines = file.readlines()
        for i, line in enumerate(lines):
            if "ecutwfc" in line:
                lines[i] = f"ecutwfc                 {ecut}\n"
        with open("./INPUT", "w") as file:
            file.writelines(lines)
        os.system("abacus")
        os.chdir("../")


def function_postprocessing():
    name = "ABACUS"
    with open(f"{ecut_min}/INPUT", "r") as file:
        lines = file.readlines()
    for i, line in enumerate(lines):
        if "suffix" in line:
            columns = line.split()
            name = columns[1]
    for i in range(num):
        ecut = float(ecut_min) + float(ecut_interval) * i
        if not os.path.exists(f"{ecut}/OUT.{name}"):
            print(f"The {ecut}/OUT.{name} file does not exist")
            exit()
        os.system(f"grep E_KohnSham {ecut}/OUT.{name}/running_scf.log -A0| tail -n1" + " | awk '{print $3}' >> energy")
    t = 0
    with open("energy", "r") as infile, open("ecuttest", "w") as outfile:
        for line in infile:
            ecut = float(ecut_min) + float(ecut_interval) * t
            outfile.write(f"{ecut}" + "   " + line)
            t = t + 1
    os.remove("./energy")


if len(sys.argv) > 1:
    if sys.argv[1] == "cal":
        function_submit()
    elif sys.argv[1] == "post":
        function_postprocessing()
        df = pd.read_csv("ecuttest", header=None, delim_whitespace=True)
        plt.figure(figsize=(10, 6))
        plt.plot(df.iloc[:, 0], df.iloc[:, 1], marker="o")
        plt.title("ecut_test")
        plt.xlabel("ecut")
        plt.ylabel("Energy / eV")
        plt.grid(True)
        plt.savefig("ecut_plot.png", format="png", dpi=300)
        plt.show()

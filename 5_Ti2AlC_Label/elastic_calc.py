import os
import sys
import glob
import shutil
import dpdata
import numpy as np
from monty.serialization import dumpfn, loadfn
from pymatgen.core.structure import Structure
from pymatgen.analysis.elasticity.elastic import Strain, ElasticTensor
from pymatgen.analysis.elasticity.strain import DeformedStructureSet
from pymatgen.analysis.elasticity.stress import Stress


class ElasticCalculator:
    """
    A class for calculating elastic properties by generating deformed structures.

    This class handles the generation of deformed structures for elastic property calculations
    using both normal and shear strains. It manages the creation of calculation directories
    and necessary input files for each deformation.
    """

    def __init__(self, relax_dir="cell-relax"):
        """
        Initialize the ElasticCalculator.

        Args:
            relax_dir (str): Directory containing the relaxed structure. Defaults to "cell-relax".
        """
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.relax_dir = os.path.join(self.current_dir, relax_dir)

        self.equi_log = os.path.join(self.relax_dir, "OUT.ABACUS", "running_cell-relax.log")
        self.equi_contcar = os.path.join(self.relax_dir, "OUT.ABACUS", "STRU_ION_D")
        self.POSCAR = os.path.join(self.relax_dir, "STRU")
        self.INCAR = os.path.join(self.relax_dir, "INPUT")
        self.KPOINTS = os.path.join(self.relax_dir, "KPT")

        if not os.path.exists(self.equi_contcar):
            raise RuntimeError("Please do relaxation first!")

    def gen_dfm(self, norm_strains=None, shear_strains=None):
        """
        Generate deformed structures for elastic property calculations.

        Args:
            norm_strains (list): List of normal strain values. Defaults to [-0.010, -0.005, 0.005, 0.010].
            shear_strains (list): List of shear strain values. Defaults to [-0.010, -0.005, 0.005, 0.010].

        Returns:
            None: Creates calculation directories with deformed structures and necessary input files.
        """
        if norm_strains is None:
            norm_strains = [-0.010, -0.005, 0.005, 0.010]
        if shear_strains is None:
            shear_strains = [-0.010, -0.005, 0.005, 0.010]

        stru = dpdata.System(self.equi_contcar, fmt="stru")
        stru.to("poscar", "POSCAR.tmp")
        ss = Structure.from_file("POSCAR.tmp")
        os.remove("POSCAR.tmp")

        dfm_ss = DeformedStructureSet(ss, symmetry=False, norm_strains=norm_strains, shear_strains=shear_strains)
        n_dfm = len(dfm_ss)

        print(f"gen with norm {norm_strains}")
        print(f"gen with shear {shear_strains}")

        work_dir = os.path.join(self.current_dir, "elastic-calc")
        os.makedirs(work_dir, exist_ok=True)
        os.chdir(work_dir)
        os.system(f"cp -r `find {self.relax_dir} -maxdepth 1 -type f` . ")
        for file in glob.glob("*.json") + glob.glob("KPT") + glob.glob("*_pw") + glob.glob("*_lcao") + glob.glob("*.cif"):
            if file != "elastic.json":
                os.remove(file)

        for ii in range(n_dfm):
            output_task = os.path.join(work_dir, f"task.{ii:03d}")
            os.makedirs(output_task, exist_ok=True)
            os.chdir(output_task)

            # STRU
            dfm_ss.deformed_structures[ii].to("POSCAR", fmt="POSCAR")
            stru = dpdata.System("POSCAR", fmt="vasp/poscar")
            n_atoms = len(stru["atom_names"])
            atom_mass = []
            pseudo = []
            orb = []
            with open(self.equi_contcar, "r") as f:
                lines = f.readlines()
            for idx, line in enumerate(lines):
                if "ATOMIC_SPECIES" in line:
                    for i in range(n_atoms):
                        atom_mass.append(float(lines[idx + i + 1].split()[1]))
                        pseudo.append(lines[idx + i + 1].split()[2])
                if "NUMERICAL_ORBITAL" in line:
                    for i in range(n_atoms):
                        orb.append(lines[idx + i + 1])
            if orb == []:
                stru.to("stru", "STRU", mass=atom_mass, pp_file=pseudo)
            else:
                stru.to("stru", "STRU", mass=atom_mass, pp_file=pseudo, numerical_orbital=orb)
            os.remove("POSCAR")

            # INPUT
            shutil.copy("../INPUT", ".")
            with open("INPUT", "r") as f:
                lines = f.readlines()
            pseudo_dir = "../"
            orb_dir = "../"
            for i, line in enumerate(lines):
                if "pseudo_dir" in line:
                    lines[i] = f"pseudo_dir              {pseudo_dir}\n"
                if "orbital_dir" in line:
                    lines[i] = f"orbital_dir             {orb_dir}\n"
                if "calculation" in line:
                    lines[i] = f"calculation             relax\n"
            with open("INPUT", "w") as f:
                f.writelines(lines)

            # KPOINTS
            # kspacing is used so no need to copy KPT
            # shutil.copy("../KPT", ".")

            df = Strain.from_deformation(dfm_ss.deformations[ii])
            dumpfn(df.as_dict(), "strain.json", indent=4)
            os.chdir(self.current_dir)

    def _get_stress(self, lines: list) -> np.ndarray:
        """
        Extract stress tensor from ABACUS output.

        Args:
            lines (list): List of lines from ABACUS output file.

        Returns:
            np.ndarray: 3x3 stress tensor in kB.
        """
        stress = np.zeros([3, 3])
        for idx, line in enumerate(lines):
            if "TOTAL-STRESS (KBAR)" in line:
                stress_xx = float(lines[idx + 2].split()[0])
                stress_yy = float(lines[idx + 3].split()[1])
                stress_zz = float(lines[idx + 4].split()[2])
                stress_xy = float(lines[idx + 2].split()[1])
                stress_yz = float(lines[idx + 3].split()[2])
                stress_zx = float(lines[idx + 2].split()[2])
                stress[0] = [stress_xx, stress_xy, stress_zx]
                stress[1] = [stress_xy, stress_yy, stress_yz]
                stress[2] = [stress_zx, stress_yz, stress_zz]
        return stress

    def compute_elastic(self):
        """
        Compute elastic constants from the deformed structures.

        Returns:
            dict: Dictionary containing elastic constants and derived properties.
        """
        # Get equilibrium stress
        with open(self.equi_log, "r") as fin:
            lines = fin.read().split("\n")

        # raw output is in KBAR, convert to GPa
        equi_stress = Stress(self._get_stress(lines) * 0.1)

        # Process all task directories
        work_dir = os.path.join(self.current_dir, "elastic-calc")
        task_dirs = glob.glob(os.path.join(work_dir, "task.*"))
        lst_strain = []
        lst_stress = []

        outcar_pattern = "OUT.*/running_*.log"

        for task_dir in task_dirs:
            os.chdir(task_dir)

            strain = loadfn("strain.json")
            outcar = glob.glob(outcar_pattern)[0]

            with open(outcar, "r") as fin:
                lines = fin.read().split("\n")

            stress = self._get_stress(lines)
            lst_strain.append(strain)
            lst_stress.append(Stress(stress * -0.1))

            os.chdir(self.current_dir)

        # Calculate elastic tensor
        et = ElasticTensor.from_independent_strains(lst_strain, lst_stress, eq_stress=equi_stress, vasp=False)

        # Prepare results
        res_data = {}
        ptr_data = "# Elastic Constants in GPa\n"
        res_data["elastic_tensor"] = []

        for ii in range(6):
            for jj in range(6):
                res_data["elastic_tensor"].append(et.voigt[ii][jj])
                ptr_data += "%7.2f " % (et.voigt[ii][jj])
            ptr_data += "\n"

        # Calculate derived properties
        BV = et.k_voigt
        GV = et.g_voigt
        EV = 9 * BV * GV / (3 * BV + GV)
        uV = 0.5 * (3 * BV - 2 * GV) / (3 * BV + GV)

        res_data["BV"] = BV
        res_data["GV"] = GV
        res_data["EV"] = EV
        res_data["uV"] = uV

        # Print results
        ptr_data += "# Bulk   Modulus BV = %.2f GPa\n" % BV
        ptr_data += "# Shear  Modulus GV = %.2f GPa\n" % GV
        ptr_data += "# Youngs Modulus EV = %.2f GPa\n" % EV
        ptr_data += "# Poission Ratio uV = %.2f " % uV
        print(ptr_data)

        # Save results
        output_file = os.path.join(work_dir, "elastic.json")
        dumpfn(res_data, output_file, indent=4)

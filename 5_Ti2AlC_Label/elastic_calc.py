import os
import sys
import shutil
import dpdata
import glob
from monty.serialization import dumpfn
from pymatgen.core.structure import Structure
from pymatgen.analysis.elasticity.elastic import Strain
from pymatgen.analysis.elasticity.strain import DeformedStructureSet


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

        self.CONTCAR = os.path.join(self.relax_dir, "OUT.*", "STRU_ION_D")
        self.POSCAR = os.path.join(self.relax_dir, "STRU")
        self.INCAR = os.path.join(self.relax_dir, "INPUT")
        self.KPOINTS = os.path.join(self.relax_dir, "KPT")

        self.equi_contcar = self.CONTCAR
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
        os.system(f"cp -r `find {self.current_dir}/{self.relax_dir} -maxdepth 1 -type f` . ")
        os.chdir(work_dir)

        for ii in range(n_dfm):
            output_task = os.path.join(work_dir, "task.%03d" % ii)
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
                    lines[i] = f"pseudo_dir                {pseudo_dir}\n"
                if "orb_dir" in line:
                    lines[i] = f"orb_dir                {orb_dir}\n"
            with open("INPUT", "w") as f:
                f.writelines(lines)

            # KPOINTS
            # kspacing is used so no need to copy KPT
            # shutil.copy("../KPT", ".")

            df = Strain.from_deformation(dfm_ss.deformations[ii])
            dumpfn(df.as_dict(), "strain.json", indent=4)
            os.chdir(self.current_dir)

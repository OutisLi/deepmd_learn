from ase import Atoms
from deepmd.calculator import DP
from ase.optimize import BFGS

# Compute potential energy
dp = DP("water_finetune/dpa3_water_finetune.pth")
water = Atoms("H2O", positions=[(0.7601, 1.9270, 1), (1.9575, 1, 1), (1.0, 1.0, 1.0)], cell=[100, 100, 100])
water.calc = dp
print("Before optimization")
print("Potential energy:", water.get_potential_energy())
print("Forces:", water.get_forces())
print("--------------------------------------\n")

# Run BFGS structure optimization
dyn = BFGS(water)
dyn.run(fmax=1e-3)
print("After optimization")
print("Potential energy:", water.get_potential_energy())
print("Forces:", water.get_forces())
print("Positions:", water.get_positions())




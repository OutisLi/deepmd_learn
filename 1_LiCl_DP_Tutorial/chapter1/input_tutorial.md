---
## LAMMPS Input Script for Simulating Molten LiCl: A Tutorial

This document provides an explanation of a LAMMPS input script designed for simulating a 3D Lithium Chloride (LiCl) melt at 900K. It aims to be a learning resource for new LAMMPS users.

### 📜 Script Overview

The script performs a molecular dynamics simulation under NVT conditions (constant Number of particles, Volume, and Temperature). It calculates properties like the Radial Distribution Function (RDF) and Mean Squared Displacement (MSD) to analyze the structure and dynamics of the molten salt.

---

### 🔧 Initialization Settings

```lammps
# initialize simulation settings
units           metal
boundary        p p p
atom_style      charge
```

-   `# initialize simulation settings`: This is a **comment line**. LAMMPS ignores lines starting with `#`. They are for human readers to understand the script.
-   `units metal`: This command sets the **units** for various physical quantities. `metal` units mean:
    -   Mass: grams/mole
    -   Distance: Angstroms (Å)
    -   Time: picoseconds (ps)
    -   Energy: electronVolts (eV)
    -   Velocity: Angstroms/picosecond
    -   Force: eV/Angstrom
    -   Torque: eV
    -   Temperature: Kelvin (K)
    -   Pressure: bars
    -   Charge: multiple of electron charge (e.g., +1 for a proton)
-   `boundary p p p`: This defines the **boundary conditions** of the simulation box. `p p p` means periodic boundaries in all three directions (x, y, and z). If a particle exits the box on one side, it re-enters from the opposite side. This mimics an infinitely large system.
-   `atom_style charge`: This specifies that each **atom** will have an associated **electric charge**. This is essential for simulating ionic materials like LiCl.

---

### 📦 Defining the Simulation Cell

```lammps
# define the simulation cell
read_data       licl.data
group           Li  type 1
group           Cl  type 2
set             type 1 charge 1
set             type 2 charge -1
```

-   `# define the simulation cell`: Another comment.
-   `read_data licl.data`: This command tells LAMMPS to read the initial atomic coordinates, atom types, box dimensions, and possibly other information from a **data file** named `licl.data`. This file must be present in the same directory as the input script or its path must be specified.
-   `group Li type 1`: This creates a **group** of atoms named `Li` and assigns all atoms of `type 1` (as defined in `licl.data`) to this group.
-   `group Cl type 2`: Similarly, this creates a group named `Cl` for atoms of `type 2`.
-   `set type 1 charge 1`: This command sets the **charge** of all atoms belonging to `type 1` (Lithium ions) to `+1.0` (in electron charge units).
-   `set type 2 charge -1`: This sets the charge of all atoms belonging to `type 2` (Chloride ions) to `-1.0`.

---

### 💪 Setting the Force Field

```lammps
# set force field
pair_style      born/coul/long 7
pair_coeff      1 1 0.4225000 0.3425 1.632 0.045625 0.01875
pair_coeff      1 2 0.2904688 0.3425 2.401 1.250000 1.50000
pair_coeff      2 2 0.1584375 0.3425 3.170 69.37500 139.375
kspace_style    ewald 1.0e-6
```

This section defines how atoms interact with each other (the force field).

-   `# set force field`: Comment.
-   `pair_style born/coul/long 7`: This specifies the **type of interaction potential** to use.
    -   `born`: Refers to the Born-Mayer-Huggins potential, which describes short-range repulsive and van der Waals attractive interactions.
    -   `coul/long`: Adds long-range Coulombic (electrostatic) interactions.
    -   `7`: This is the **cutoff distance** (in Angstroms for `metal` units) for the short-range part of the potential. Interactions beyond this distance are either neglected or handled by the long-range solver.
-   `pair_coeff`: These lines define the **parameters** for the Born-Mayer-Huggins potential for interactions between different pairs of atom types. The general form for `born/coul/long` is:
    `pair_coeff I J A_ij rho_ij C_ij D_ij cutoff`
    (Though the exact parameters and their meaning for `born` or `buck` styles can vary slightly in LAMMPS; for `born/coul/long`, the format is typically $A_{ij}$, $\rho_{ij}$, $r_{ij}^0$, $C_{ij}$, $D_{ij}$. Here, it looks like a simplified form or specific variant is used. The provided parameters are for a Buckingham-like potential: $A \exp(-B r) - C/r^6$.
    Let's assume the parameters are for: $A_{ij}$, $\rho_{ij}$, $r_{cut,ij}$ (individual cutoff, often ignored if global cutoff is set), $C_{ij}$ (for $r^{-6}$ term), $D_{ij}$ (for $r^{-8}$ term, often zero if not used).
    Specifically for the `born` component used here, the parameters usually are:
    $A_{ij}$ (energy units), $\rho_{ij}$ (distance units), $r^0_{ij}$ (distance units, often set to 0 or a small value if not relevant), $C_{ij}$ (energy\*distance^6 units), $D_{ij}$ (energy\*distance^8 units).
    The command defines parameters for:
    -   `1 1`: Li-Li interaction. Parameters: `0.4225000 0.3425 1.632 0.045625 0.01875`
    -   `1 2`: Li-Cl interaction. Parameters: `0.2904688 0.3425 2.401 1.250000 1.50000`
    -   `2 2`: Cl-Cl interaction. Parameters: `0.1584375 0.3425 3.170 69.37500 139.375`
        The specific meaning of each number depends on the exact functional form implemented in LAMMPS for `pair_style born`. Typically, these represent terms for repulsion ($A$, $\rho$), and dispersion ($C$, $D$).
-   `kspace_style ewald 1.0e-6`: This command specifies the algorithm to use for calculating **long-range Coulombic interactions** in reciprocal space (k-space).
    -   `ewald`: Uses the Ewald summation method.
    -   `1.0e-6`: This is the desired **accuracy** for the Ewald summation. It's a relative accuracy for the per-atom forces.

---

### 🔥 NVT Simulation (Constant N, V, T)

```lammps
# nvt simulation
velocity        all create 900 23456789
fix             1 all nvt temp 900 900 0.5
timestep        0.001
```

This section sets up and controls the main simulation run.

-   `# nvt simulation`: Comment.
-   `velocity all create 900 23456789`: This command **initializes atomic velocities**.
    -   `all`: Applies to all atoms in the simulation.
    -   `create 900`: Assigns velocities to atoms corresponding to a temperature of `900` K. The velocities are drawn from a Gaussian distribution.
    -   `23456789`: This is a **random number seed**. Using the same seed will produce the same initial velocities if the simulation is run again.
-   `fix 1 all nvt temp 900 900 0.5`: This is a crucial command that applies a "fix" to control the system. A fix modifies the simulation in some way.
    -   `1`: This is the **ID** for this fix (you can have multiple fixes).
    -   `all`: The fix applies to all atoms.
    -   `nvt`: Specifies the **NVT ensemble**, meaning the Number of particles (N), Volume (V), and Temperature (T) are kept constant. This is achieved using a thermostat.
    -   `temp 900 900`: Sets the **target temperature**. The first `900` is the starting temperature, and the second `900` is the ending temperature for the thermostat.
    -   `0.5`: This is the **temperature damping parameter** (`Tdamp`) in time units (picoseconds here). It determines how quickly the temperature is coupled to the thermostat. A smaller value means tighter coupling.
-   `timestep 0.001`: This sets the **integration timestep** for the simulation to `0.001` picoseconds (1 femtosecond). This is the small increment of time by which the simulation advances at each step. Choosing an appropriate timestep is critical for stability and accuracy.

---

### 📊 RDF Calculation (Radial Distribution Function)

```lammps
# rdf calculation
compute         rdf all rdf 100 1 1 1 2 2 2
fix             2 all ave/time 100 1 100 c_rdf[*] file licl.rdf mode vector
```

This section calculates the RDF, which describes how the density of atoms varies as a function of distance from a reference atom. It's a key measure of local structure.

-   `# rdf calculation`: Comment.
-   `compute rdf all rdf 100 1 1 1 2 2 2`: This command defines a "compute" that calculates the RDF.
    -   `rdf`: This is the **ID** for this compute.
    -   `all`: The compute considers all atoms.
    -   `rdf`: Specifies the type of compute: Radial Distribution Function.
    -   `100`: The number of **bins** used to discretize the RDF.
    -   The following pairs `1 1`, `1 2`, `2 2` specify which pairs of atom types to calculate the RDF for:
        -   `1 1`: RDF between type 1 atoms (Li-Li)
        -   `1 2`: RDF between type 1 and type 2 atoms (Li-Cl)
        -   `2 2`: RDF between type 2 atoms (Cl-Cl)
-   `fix 2 all ave/time 100 1 100 c_rdf[*] file licl.rdf mode vector`: This command averages the RDF values calculated by `compute rdf` over time and writes them to a file.
    -   `2`: The ID for this fix.
    -   `all`: Applies to all atoms (though it's really about the global RDF compute).
    -   `ave/time`: Specifies that this fix will average values over time.
    -   `100 1 100`: These are averaging parameters:
        -   `Nevery = 100`: The compute is invoked every 100 timesteps.
        -   `Nrepeat = 1`: The compute is averaged over 1 such invocation (effectively, no time averaging _within_ this fix beyond the sampling frequency).
        -   `Nfreq = 100`: The averaged values are output every 100 timesteps.
    -   `c_rdf[*]`: Specifies that the values to be averaged are from the compute with ID `rdf`. The `[*]` means all components of the vector/array output by `compute rdf` (i.e., $g(r)$ for each bin and each pair type).
    -   `file licl.rdf`: The output file name for the RDF data.
    -   `mode vector`: Indicates that the output from `compute rdf` is a vector (or array of vectors), and each element should be treated as a separate column in the output file after the initial columns for timestep and number of values.

---

### 🚶 MSD Calculation (Mean Squared Displacement)

```lammps
# msd calculation
compute         msd1 Li msd
compute         msd2 Cl msd
fix             3 all ave/time 100 1 100 c_msd1[4] c_msd2[4] file licl.msd
```

This section calculates the MSD, which is a measure of how much particles move on average over time. It's used to determine diffusion coefficients.

-   `# msd calculation`: Comment.
-   `compute msd1 Li msd`: Defines a compute to calculate MSD for the `Li` group.
    -   `msd1`: ID for this compute.
    -   `Li`: The group of atoms (`type 1`) for which to calculate MSD.
    -   `msd`: Specifies the MSD calculation. This compute actually calculates $MSD_x, MSD_y, MSD_z$ and the total $MSD = MSD_x + MSD_y + MSD_z$. The fourth component `c_msd1[4]` is the total MSD.
-   `compute msd2 Cl msd`: Defines a similar compute for the `Cl` group (`type 2`).
    -   `msd2`: ID for this compute.
    -   `Cl`: The group of atoms (`type 2`).
-   `fix 3 all ave/time 100 1 100 c_msd1[4] c_msd2[4] file licl.msd`: Averages and outputs the total MSD values for Li and Cl.
    -   `3`: ID for this fix.
    -   `all`: Applies to all atoms (again, related to the global computes).
    -   `ave/time 100 1 100`: Averaging parameters, same meaning as for the RDF fix. The MSD is calculated every 100 steps, and this instantaneous value is output every 100 steps.
    -   `c_msd1[4] c_msd2[4]`: Specifies the values to output: the 4th component (total MSD) from `compute msd1` and `compute msd2`.
    -   `file licl.msd`: The output file name for the MSD data.

---

### 📝 Output Settings

```lammps
# output
thermo_style    custom step temp pe ke etotal press lx ly lz vol
thermo          1000
dump            1 all custom 1000 licl.dump id type x y z
```

This section controls what thermodynamic data is printed to the screen/log file and how often atomic configurations are saved.

-   `# output`: Comment.
-   `thermo_style custom step temp pe ke etotal press lx ly lz vol`: Customizes the **thermodynamic output** printed to the screen and log file.
    -   `custom`: Indicates a user-defined list of keywords.
    -   `step`: Current timestep.
    -   `temp`: Current temperature.
    -   `pe`: Total potential energy.
    -   `ke`: Total kinetic energy.
    -   `etotal`: Total energy (`pe + ke`).
    -   `press`: Current pressure.
    -   `lx ly lz`: Dimensions of the simulation box in x, y, and z.
    -   `vol`: Volume of the simulation box.
-   `thermo 1000`: Specifies that the thermodynamic data (defined by `thermo_style`) should be printed every `1000` timesteps.
-   `dump 1 all custom 1000 licl.dump id type x y z`: This command "dumps" snapshots of atomic configurations to a file.
    -   `1`: ID for this dump.
    -   `all`: Dumps information for all atoms.
    -   `custom`: Specifies a custom output format.
    -   `1000`: Snapshots are written every `1000` timesteps.
    -   `licl.dump`: The name of the dump file.
    -   `id type x y z`: Specifies the information to write for each atom: its ID, type, and x, y, z coordinates.

---

### 🚀 Run the Simulation

```lammps
log             ./LiCl_DP_Tutorial_Example/Chapter1/Outputs/log.lammps
run             500000
```

-   `log ./LiCl_DP_Tutorial_Example/Chapter1/Outputs/log.lammps`: This command specifies the **name and location of the log file**. LAMMPS writes its screen output (including thermodynamic data) to this file. The path suggests a specific directory structure.
-   `run 500000`: This is the command that actually **starts the simulation** and runs it for `500000` timesteps.

---

This detailed breakdown should help you understand the purpose of each command in the LAMMPS input script. As you continue learning, you'll become more familiar with these commands and discover many more that LAMMPS offers! Good luck! 🧪

```

```

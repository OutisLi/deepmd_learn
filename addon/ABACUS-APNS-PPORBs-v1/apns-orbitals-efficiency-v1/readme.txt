Usage
-----
This directory stores the ABACUS Numerical Atomic Orbital
(NAO)/Pseudo-atomic Orbital (PAO)s that MUST be used 
together with the corresponding pseudopotentials (PSPs)
in `apns-pseudopotentials-v1` directory.

It is suggested to set `ecutwfc` to be at least larger
than the larger value of the suggested for PSPs and 
the "energy cutoff" recorded in the NAO/PAO files.

Any further questions and needs on the NAOs/PAOs, please
submit issues on the ABACUS GitHub repository:
https://github.com/deepmodeling/abacus-develop/issues

Warning
-------
NAOs in this directory are suggested for occupied states
determined properties, such as quick force and stress 
evaluation, geometry optimization, and molecular dynamics.

For calculation of high-accuracy energy evaluation, 
band structure, Time-dependent density functional theory 
(TDDFT), GW and other properties that require unoccupied 
states, please use the NAOs in `apns-orbitals-precision-v1` 
directory.

BSSE (Basis-set Superposition Error)
------------------------------------
BSSE is not systematically tested for NAOs in this version,
but a more complete basis would be expected to give a 
smaller BSSE. Therefore, it is suggested to use the NAOs in
`apns-orbitals-precision-v1` directory for high-accuracy
calculations. Also please follow the instruction in on-line
manual to follow the counterpoise method to correct the BSSE:
https://abacus.deepmodeling.com/en/latest/advanced/pp_orb.html#bsse-correction

Cite
----
ABACUS NAO/PAO is generated based on the algorithm that
optimizing the Spillage function. Users are kindly
suggested to cite the following papers:

Chen M, Guo G C, He L. Systematically improvable optimized 
atomic basis sets for ab initio calculations[J]. Journal 
of Physics: Condensed Matter, 2010, 22(44): 445501.

Lin P, Ren X, He L. Strategy for constructing compact 
numerical atomic orbital basis sets by incorporating the 
gradients of reference wavefunctions[J]. Physical Review B, 
2021, 103(23): 235131.

Benchmarks
----------
These NAOs were benchmarked on ABACUS-LCAO code,
against the all-electron data of systems:

Unaries:
- Body-centered cubic (bcc)
- Face-centered cubic (fcc)
- Diamond
Compounds:
- X2O
- XO
- X2O3
- XO2
- X2O5
- XO3

from the following references:

Bosoni E, Beal L, Bercx M, et al. How to verify 
the precision of density-functional-theory 
implementations via reproducible and universal 
workflows[J]. Nature Reviews Physics, 2024, 6(1): 45-58.

The benchmark data is open-sourced at AIS-Square:
https://aissquare.com/datasets/detail?pageType=datasets&name=ABACUS-stable-psp-orb-test-data&id=318
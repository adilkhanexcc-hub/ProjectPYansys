"""
PyANSYS / PyFluent CFD workflow template
Author: Adil Khan workflow starter

Purpose
-------
This script is a practical starting template for running an ANSYS Fluent CFD case
from Python using PyFluent.

It is designed for:
- external aerodynamics
- cooling duct / airflow cases
- simple steady-state incompressible flow
- junior CFD portfolio / application practice

Important
---------
You need:
1. ANSYS Fluent installed and licensed
2. PyFluent installed:
   pip install ansys-fluent-core
3. A prepared Fluent mesh file:
   .msh, .msh.h5, .cas, or .cas.h5

This workflow starts from an existing mesh/case file.
Meshing automation can be added later once your CAD and named selections are fixed.
"""

from pathlib import Path
import ansys.fluent.core as pyfluent


# ============================================================
# USER SETTINGS
# ============================================================

CASE_NAME = "external_aero_template"

# Put your mesh or case file here
MESH_FILE = Path("your_mesh_or_case_file_here.msh.h5")

# Output folder
OUTPUT_DIR = Path("pyfluent_results")
OUTPUT_DIR.mkdir(exist_ok=True)

# Simulation settings
VELOCITY_INLET = 20.0          # m/s
AIR_DENSITY = 1.225           # kg/m3
AIR_VISCOSITY = 1.7894e-5     # kg/(m.s)
REFERENCE_AREA = 1.0          # m2, change for your model
REFERENCE_LENGTH = 1.0        # m, change for your model
ITERATIONS = 500

# Boundary names must match your Fluent mesh boundary names
INLET_NAME = "inlet"
OUTLET_NAME = "outlet"
WALL_NAMES = ["car", "ground"]     # add your wall zones here
SYMMETRY_NAMES = []                # example: ["symmetry"]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def check_input_file(path: Path) -> None:
    """Check that the user-provided mesh/case file exists."""
    if not path.exists():
        raise FileNotFoundError(
            f"\nInput file not found: {path}\n"
            "Edit MESH_FILE in this script and point it to your .msh/.msh.h5/.cas/.cas.h5 file."
        )


def launch_fluent():
    """
    Launch Fluent in solver mode.

    processor_count can be changed depending on your computer.
    precision='double' is recommended for engineering simulations.
    """
    solver = pyfluent.launch_fluent(
        mode="solver",
        precision="double",
        processor_count=4,
        show_gui=True,
    )
    return solver


def read_mesh_or_case(solver, file_path: Path):
    """Read mesh or case file depending on extension."""
    suffixes = "".join(file_path.suffixes).lower()

    if suffixes.endswith(".cas") or suffixes.endswith(".cas.h5") or suffixes.endswith(".cas.gz"):
        print("Reading Fluent case file...")
        solver.file.read_case(file_name=str(file_path))
    elif suffixes.endswith(".msh") or suffixes.endswith(".msh.h5") or suffixes.endswith(".msh.gz"):
        print("Reading Fluent mesh file...")
        solver.file.read_mesh(file_name=str(file_path))
    else:
        raise ValueError("Unsupported file type. Use .msh, .msh.h5, .cas, or .cas.h5")


def setup_general_physics(solver):
    """
    Setup general steady-state incompressible RANS simulation.

    This is a solid starting point for:
    - external aerodynamics
    - ducts
    - cooling flow
    """
    tui = solver.tui

    # 3D pressure-based steady solver
    try:
        tui.define.models.solver.pressure_based("yes")
    except Exception as exc:
        print(f"Warning: pressure-based solver command may vary by Fluent version: {exc}")

    # Enable viscous turbulence model: k-omega SST
    tui.define.models.viscous.kw_sst("yes")

    # Material properties for air
    # If this fails, set air properties manually in Fluent GUI.
    try:
        tui.define.materials.change_create(
            "air",
            "air",
            "yes", "constant", AIR_DENSITY,
            "yes", "constant", AIR_VISCOSITY,
            "no", "no", "no"
        )
    except Exception as exc:
        print(f"Warning: Could not update air material automatically: {exc}")


def setup_boundary_conditions(solver):
    """
    Setup common boundary conditions.

    Important:
    Boundary names must match the mesh.
    Check names inside Fluent if this fails.
    """
    tui = solver.tui

    # Velocity inlet
    try:
        tui.define.boundary_conditions.velocity_inlet(
            INLET_NAME,
            "yes",
            "no",
            VELOCITY_INLET,
            "no",
            0,
            "no",
            0,
            "no",
            0,
            "yes",
            "no",
            "no",
            5,
            10
        )
    except Exception as exc:
        print(f"Warning: Could not set velocity inlet automatically: {exc}")

    # Pressure outlet
    try:
        tui.define.boundary_conditions.pressure_outlet(
            OUTLET_NAME,
            "yes",
            "no",
            0,
            "no",
            "yes",
            "no",
            "no",
            5,
            10
        )
    except Exception as exc:
        print(f"Warning: Could not set pressure outlet automatically: {exc}")

    for wall in WALL_NAMES:
        try:
            tui.define.boundary_conditions.wall(wall)
        except Exception as exc:
            print(f"Warning: Could not set wall boundary for {wall}: {exc}")

    for sym in SYMMETRY_NAMES:
        try:
            tui.define.boundary_conditions.symmetry(sym)
        except Exception as exc:
            print(f"Warning: Could not set symmetry boundary for {sym}: {exc}")


def setup_reference_values(solver):
    """Set reference values used for drag/lift coefficient reporting."""
    tui = solver.tui

    try:
        tui.report.reference_values.area(REFERENCE_AREA)
        tui.report.reference_values.length(REFERENCE_LENGTH)
        tui.report.reference_values.density(AIR_DENSITY)
        tui.report.reference_values.velocity(VELOCITY_INLET)
    except Exception as exc:
        print(f"Warning: Could not set reference values automatically: {exc}")


def setup_numerics(solver):
    """
    Setup discretization schemes and solution controls.

    Second-order schemes are preferred once the case is stable.
    Some TUI commands vary by Fluent version, so warnings are acceptable.
    """
    tui = solver.tui

    try:
        tui.solve.set.p_v_coupling(24)  # SIMPLE in many Fluent versions
    except Exception as exc:
        print(f"Warning: Could not set pressure-velocity coupling automatically: {exc}")

    try:
        tui.solve.set.discretization_scheme.pressure(12)
        tui.solve.set.discretization_scheme.mom(1)
        tui.solve.set.discretization_scheme.k(1)
        tui.solve.set.discretization_scheme.omega(1)
    except Exception as exc:
        print(f"Warning: Could not set all discretization schemes automatically: {exc}")


def initialize_and_run(solver):
    """Initialize and run the simulation."""
    tui = solver.tui

    print("Initializing solution...")
    tui.solve.initialize.hybrid_initialize()

    print(f"Running {ITERATIONS} iterations...")
    tui.solve.iterate(ITERATIONS)


def save_results(solver):
    """Save final case and data."""
    case_file = OUTPUT_DIR / f"{CASE_NAME}.cas.h5"
    data_file = OUTPUT_DIR / f"{CASE_NAME}.dat.h5"

    print("Saving case and data...")
    solver.file.write_case(file_name=str(case_file))
    solver.file.write_data(file_name=str(data_file))

    print(f"Saved:\n{case_file}\n{data_file}")


def main():
    check_input_file(MESH_FILE)

    solver = launch_fluent()

    try:
        read_mesh_or_case(solver, MESH_FILE)
        setup_general_physics(solver)
        setup_boundary_conditions(solver)
        setup_reference_values(solver)
        setup_numerics(solver)
        initialize_and_run(solver)
        save_results(solver)

        print("\nSimulation workflow complete.")
        print("Next step: open results in Fluent or ParaView and inspect:")
        print("- residual convergence")
        print("- velocity streamlines")
        print("- pressure contours")
        print("- drag/lift values")
        print("- wake or cooling behavior")

    finally:
        # Uncomment this when you want Fluent to close automatically after the run.
        # solver.exit()
        pass


if __name__ == "__main__":
    main()

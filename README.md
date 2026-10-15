# smt: CSA A23.3-19 Punching Shear & SSR Design Tool

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Standard: CSA A23.3-19](https://img.shields.io/badge/Standard-CSA%20A23.3--19-E03C31.svg?style=flat)](https://www.csagroup.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Package Manager: uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://docs.astral.sh/uv/)

`smt` is a high-performance Python structural engineering tool designed for calculating two-way concrete punching shear capacities and designing Stud Shear Reinforcement (SSR) in accordance with the Canadian standard **CSA A23.3-19**.

---

## Features

- **First-Principles Geometry Engine**:
  - Calculates true polar moments of inertia ($J_c$) retaining all $d^3$ terms without relying on simplified textbook approximations:
    $$J_{\text{local}} = \frac{d \cdot L^3}{12} + \frac{L \cdot d^3}{12}$$
  - Full Cartesian coordinate tracking with parallel axis theorem shifts relative to the column centroid.
- **Dynamic Slab Edge & Proximity Detection**:
  - Automatically identifies **Interior**, **Edge**, and **Corner** boundary conditions by evaluating whether slab edges fall within the active $5d$ zone of the column face.
  - Dynamically builds and trims critical shear perimeters ($b_0$) using [`shapely`](https://shapely.readthedocs.io/).
- **Rigorous CSA A23.3-19 Code Checks**:
  - **Concrete Resistance ($v_c$)**: Evaluates governing limits across Cl. 13.3.4.1 (a, b, c) and applies the size effect factor for $d > 300\text{ mm}$ (Cl. 13.3.4.3).
  - **Unbalanced Moment Transfer**: Computes shear transfer fraction ($\gamma_v$) and flexural transfer fraction ($\gamma_f = 1 - \gamma_v$) along with the effective transfer slab band width $b_{\text{band}} = c_2 + 3h$ (Cl. 13.3.5.2 & 13.3.5.3).
  - **Maximum Stress Limit**: Verifies concrete crushing limits ($v_{r,\text{max}} = 0.75 \phi_c \lambda \sqrt{f'_c}$) prior to reinforcement design (Cl. 13.3.8.2).
- **Automated Stud Shear Reinforcement (SSR) Design**:
  - Determines required stud diameter, number of rails, and stud spacing adhering to code limits ($s_0 \le 0.4d$, $s \le 0.5d$ or $0.25d$) per Cl. 13.3.8.5.
  - Runs an automated iterative expansion loop for the outer octagonal perimeter until shear stress satisfies $v_{c,\text{out}} \le 0.19 \phi_c \lambda \sqrt{f'_c}$ (Cl. 13.3.8.6).
- **Interactive Visualizations**:
  - Interactive **Plotly** and static **Matplotlib** diagrams rendering the physical column, slab boundaries, critical perimeters, plastic centroid, and arranged stud rails.
- **Modern Frontends**:
  - Reactive GUI via [Marimo](https://marimo.io) (`punching_shear_mvp.py`) with live input sliders and real-time updates.
  - Comprehensive Jupyter Notebook workflow (`punching_shear_mvp.ipynb`).

---

## Project Architecture

```
smt/
├── Codes/
│   └── CSA_A23_3_19.py          # CSA code provisions (vc, vr_max, gamma_v, SSR layout)
├── Core/
│   └── Geometry.py              # Pure math: Shapely perimeters, centroids, Jc, octagons
├── Models/
│   ├── Materials.py             # Concrete & Rebar material dataclasses
│   └── Results.py               # Input & analysis result schemas
├── Utilities/
│   ├── plotting.py              # Matplotlib visualization utilities
│   └── plotting_plotly.py       # Interactive Plotly rendering functions
├── Tests/
│   ├── test_calculator.py       # Hand-calculation verified Pytest suite
│   └── test_geometry.py         # Perimeter geometry & Jc unit tests
├── punching_shear_mvp.py        # Reactive Marimo application
├── punching_shear_mvp.ipynb      # Interactive Jupyter notebook
├── pyproject.toml               # Project metadata and tool configuration
└── uv.lock                      # Deterministic dependency lockfile
```

---

## Installation

This project uses [`uv`](https://docs.astral.sh/uv/) for fast, deterministic Python environment management.

### Recommended: With `uv`

1. Install `uv` if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. Clone the repository and navigate into the project directory:
   ```bash
   git clone https://github.com/halledega/smt.git
   cd smt
   ```
3. Sync the virtual environment:
   ```bash
   uv sync
   ```

### Alternative: Standard `pip`

Ensure Python 3.12 or newer is installed:

```bash
git clone https://github.com/halledega/smt.git
cd smt
pip install -e .
```

---

## Quickstart (Python API)

```python
from Core.Geometry import ColumnLocation, calculate_punching_properties
from Codes.CSA_A23_3_19 import (
    calc_vc_unreinforced,
    calc_gamma_v,
    calc_max_shear_stress,
    check_maximum_ssr_stress,
    design_ssr_rails,
)
from Models.Materials import Concrete, Rebar
from Models.Results import PunchingShearInput

# 1. Define materials
concrete = Concrete(name="35MPa", fc=35.0, unit_weight=24.0, lamb=1.0)
rebar = Rebar(name="400W", fy=400.0)

# 2. Define inputs
inputs = PunchingShearInput(
    slab_thickness=250.0,
    c_top=30.0,
    c_bot=30.0,
    c1=300.0,
    c2=600.0,
    x_c=0.0,
    y_c=0.0,
    Vf=1200.0,       # kN
    Mf_x=120.0,      # kN·m
    Mf_y=-200.0,     # kN·m
    concrete=concrete,
    rebar=rebar,
    location=ColumnLocation.EDGE,
)

# Slab bounds [x_min, y_min, x_max, y_max] in mm
slab_bounds = [-5000.0, -5000.0, 1000.0, 5000.0]

# 3. Compute critical perimeter properties (b0, Ac, Centroid, Jc)
geometry = calculate_punching_properties(inputs, slab_bounds)

# 4. Evaluate CSA A23.3-19 capacity
v_c, d_factor = calc_vc_unreinforced(inputs, geometry)
v_r_max = check_maximum_ssr_stress(inputs)
gamma_vx = calc_gamma_v(inputs, "x")
gamma_vy = calc_gamma_v(inputs, "y")

vf = calc_max_shear_stress(
    v_f=inputs.Vf * 1000,
    m_fx=inputs.Mf_x * 1e6,
    m_fy=inputs.Mf_y * 1e6,
    inputs=inputs,
    geometry=geometry,
    gamma_vx=gamma_vx,
    gamma_vy=gamma_vy,
)

# 5. Check capacity and design SSR rails if required
if vf > v_c:
    print(f"SSR Required: vf ({vf:.2f} MPa) > vc ({v_c:.2f} MPa)")
    ssr_result = design_ssr_rails(inputs, slab_bounds, geometry, vf)
    if ssr_result["success"]:
        print(f"Rails Designed: {ssr_result['num_rails']} rails with {ssr_result['num_studs_per_rail']} studs each.")
```

---

## Running the Applications

### Marimo Reactive Web App
Run the interactive reactive notebook with live sliders:
```bash
uv run marimo edit punching_shear_mvp.py
```

### Jupyter Notebook
Launch the Jupyter Lab environment:
```bash
uv run jupyter lab punching_shear_mvp.ipynb
```

---

## Testing & Verification

The calculation engine is backed by an automated test suite verifying geometry properties ($A_c$, $J_c$), code equations, and stud rail placement against hand calculations:

```bash
uv run pytest
```

---

## Development Roadmap

- [x] **Phase 1: Core Engine & MVP**
  - [x] First-principles geometry engine with exact $J_c$ (preserving $d^3$).
  - [x] Dynamic edge detection for interior, edge, and corner column positions.
  - [x] CSA A23.3-19 shear checks ($v_c$, size effect, $\gamma_v$, $v_{r,\text{max}}$).
  - [x] Iterative SSR design loop with octagonal outer perimeter expansion.
  - [x] Matplotlib & Plotly interactive visualization.
  - [x] Marimo & Jupyter notebook frontends.
- [ ] **Phase 2: Alpha (In Progress)**
  - [ ] Support for circular column geometries.
  - [ ] Slab opening deductions per CSA A23.3-19 Cl. 13.3.3.3.
  - [ ] Traditional stirrup and hairpin reinforcement options.
  - [ ] Markdown & PDF engineering calculation summary report exporter.
- [ ] **Phase 3: Beta**
  - [ ] Standalone PySide desktop graphical interface.
  - [ ] Automated column load ingestion from structural analysis packages (ETABS / SAFE).

---

## References

1. **CSA Group**, *CSA A23.3:19 - Design of concrete structures*, Rexdale, Ontario, Canada, 2019.
2. **CPCA**, *Concrete Design Handbook (4th Edition)*, Canadian Portland Cement Association.

---

## License

This project is licensed under the [MIT License](LICENSE).

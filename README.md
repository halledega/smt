# smt

A structural engineering tool for calculating punching shear capacity to CSA A23.3-19.

## Overview
This project provides calculations and verification for punching shear according to the Canadian structural design standards (CSA A23.3-19).

## Installation
The project manages its dependencies using `uv`. 

1. Ensure you have `uv` installed. If not, follow the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).
2. Clone the repository and navigate into the `smt` directory.
3. Sync the environment and install the package:

```bash
uv sync
```

Alternatively, if you are not using `uv`, ensure you have Python 3.12 or higher installed and run:
```bash
pip install -e .
```

## Testing
Run tests using pytest (if using `uv`, prefix with `uv run`):

```bash
uv run pytest
```

## Examples

The project includes an example Jupyter Notebook (`punching_shear_mvp.ipynb`) demonstrating how to use the tool to calculate capacities for different column configurations. 

### Notebook Inputs Explained
The core inputs are provided to the `PunchingShearInput` model:
- `slab_thickness`: Total thickness of the concrete slab (mm).
- `c_top`, `c_bot`: Clear cover to the top and bottom reinforcement (mm).
- `c1`, `c2`: Column dimensions (mm). `c1` is parallel to the x-axis, `c2` is parallel to the y-axis.
- `x_c`, `y_c`: Coordinates of the column centroid (mm).
- `Vf`, `Mf_x`, `Mf_y`: Factored shear force (kN) and unbalanced moments about the x and y axes (kN·m).
- `concrete`, `rebar`: Material objects defining properties like compressive strength (`fc`) and yield strength (`fy`).
- `location`: An enumeration (`ColumnLocation.INTERIOR`, `ColumnLocation.EDGE`, or `ColumnLocation.CORNER`) specifying the general column layout.
- `slab_bounds`: A list `[x_min, y_min, x_max, y_max]` defining the absolute boundary limits of the slab (used to determine distance to edges and boundary conditions).

### Column Configurations

You can evaluate different configurations by modifying the `location` and `slab_bounds` inputs in the notebook. 
*(Note: As defined by CSA A23.3-19, a free edge is considered "active" if it is within 5d of the column face. The code automatically opens the shear perimeter if an edge is active.)*

#### 1. Interior Column
An interior column is far away from all slab edges.
```python
inputs.location = ColumnLocation.INTERIOR
slab_bounds = [-5000.0, -5000.0, 5000.0, 5000.0]
```
*Setting `slab_bounds` to large values ensures no edge is within 5d of the column.*

#### 2. Edge Column
An edge column has one slab edge in close proximity (within 5d).
```python
inputs.location = ColumnLocation.EDGE
slab_bounds = [-5000.0, -5000.0, 500.0, 5000.0] 
```
*In this example, the right edge is set close to the column (at x = 500 mm). The code will automatically open the shear perimeter towards the right edge.*

#### 3. Corner Column
A corner column has two adjacent slab edges in close proximity (within 5d).
```python
inputs.location = ColumnLocation.CORNER
slab_bounds = [-5000.0, -5000.0, 500.0, 500.0] 
```
*In this example, both the right edge (x = 500 mm) and top edge (y = 500 mm) are close to the column. The critical perimeter will open towards both nearby edges.*

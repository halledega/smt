import pytest
import numpy as np
from Core.Geometry import calculate_punching_properties, generate_octagonal_outer_perimeter
from Models.Results import PunchingShearInput
from Core.Geometry import ColumnLocation
from Models.Materials import Concrete, Rebar
from shapely.geometry import MultiLineString

def test_interior_column():
    """
    Test an interior column where all slab edges are far away (> 5d).
    The perimeter should be a full rectangle.
    """
    # Create mock inputs
    concrete = Concrete(name="30MPa", fc=30, unit_weight=24.0)
    rebar = Rebar(name="400W", fy=400)
    inputs = PunchingShearInput(
        slab_thickness=250.0, c_top=50.0, c_bot=50.0,
        c1=300.0, c2=300.0, x_c=0.0, y_c=0.0,
        Vf=100.0, Mf_x=50.0, Mf_y=50.0,
        concrete=concrete, rebar=rebar, location=ColumnLocation.INTERIOR
    )
    d = inputs.d  # d = 200
    
    # Slab edges very far away
    slab_bounds = [-5000.0, -5000.0, 5000.0, 5000.0]
    
    results = calculate_punching_properties(inputs, slab_bounds)
    
    # Expected b0: 
    # Left/Right legs: cy + d = 300 + 200 = 500
    # Top/Bottom legs: cx + d = 300 + 200 = 500
    # Total = 4 * 500 = 2000
    expected_b0 = 2000.0
    expected_Ac = expected_b0 * d
    
    assert np.isclose(results.b0, expected_b0, rtol=1e-3)
    assert np.isclose(results.Ac, expected_Ac, rtol=1e-3)
    assert np.isclose(results.cx_plastic, 0.0, atol=1.0)
    assert np.isclose(results.cy_plastic, 0.0, atol=1.0)
    # The center of the column is (0, 0), so eccentricity should be 0
    assert np.isclose(results.e_x, 0.0, atol=1.0)
    assert np.isclose(results.e_y, 0.0, atol=1.0)


def test_edge_column():
    """
    Test an edge column.
    For example, right edge is close, other edges are far.
    """
    concrete = Concrete(name="30MPa", fc=30, unit_weight=24.0)
    rebar = Rebar(name="400W", fy=400)
    inputs = PunchingShearInput(
        slab_thickness=250.0, c_top=50.0, c_bot=50.0,
        c1=300.0, c2=300.0, x_c=0.0, y_c=0.0,
        Vf=100.0, Mf_x=50.0, Mf_y=50.0,
        concrete=concrete, rebar=rebar, location=ColumnLocation.EDGE
    )
    d = inputs.d  # d = 200
    
    # Slab right edge is at x = 200.
    # Column right face is at x = 150.
    # Distance to edge = 50 (<= 5d = 1000), so right edge is active.
    # The perimeter will extend to the right edge (50mm).
    slab_bounds = [-5000.0, -5000.0, 200.0, 5000.0]
    
    results = calculate_punching_properties(inputs, slab_bounds)
    
    # Left face exists at x = -150 - d/2 = -250
    # Right face is OMITTED.
    # Top/Bottom legs extend from x = -250 to x = 150 + 50 = 200
    # Length of Top/Bottom = 200 - (-250) = 450
    # Length of Left = 150 + d/2 - (-150 - d/2) = 250 - (-250) = 500
    # Expected b0 = 450 (top) + 450 (bottom) + 500 (left) = 1400
    expected_b0 = 1400.0
    expected_Ac = expected_b0 * d
    
    assert np.isclose(results.b0, expected_b0, rtol=1e-3)
    assert np.isclose(results.Ac, expected_Ac, rtol=1e-3)
    
    # Plastic centroid must have shifted left (negative x) since the right face is missing
    assert results.cx_plastic < 0.0
    assert np.isclose(results.cy_plastic, 0.0, atol=1.0)
    
    # Eccentricity should match centroid shift since x_c = 0
    assert np.isclose(results.e_x, results.cx_plastic, rtol=1e-3)
    assert np.isclose(results.e_y, 0.0, atol=1.0)


def test_corner_column():
    """
    Test a corner column.
    For example, top and right edges are close.
    """
    concrete = Concrete(name="30MPa", fc=30, unit_weight=24.0)
    rebar = Rebar(name="400W", fy=400)
    inputs = PunchingShearInput(
        slab_thickness=250.0, c_top=50.0, c_bot=50.0,
        c1=300.0, c2=300.0, x_c=0.0, y_c=0.0,
        Vf=100.0, Mf_x=50.0, Mf_y=50.0,
        concrete=concrete, rebar=rebar, location=ColumnLocation.CORNER
    )
    d = inputs.d  # d = 200
    
    # Slab right edge at x = 200, top edge at y = 200
    # Column right face at 150, top face at 150.
    # Distances are 50 (<= 5d), so both are active.
    slab_bounds = [-5000.0, -5000.0, 200.0, 200.0]
    
    results = calculate_punching_properties(inputs, slab_bounds)
    
    # Right and Top faces are OMITTED.
    # Left face exists at x = -250. It extends from y = -250 to y = 200. Length = 450.
    # Bottom face exists at y = -250. It extends from x = -250 to x = 200. Length = 450.
    # Expected b0 = 450 + 450 = 900
    expected_b0 = 900.0
    expected_Ac = expected_b0 * d
    
    assert np.isclose(results.b0, expected_b0, rtol=1e-3)
    assert np.isclose(results.Ac, expected_Ac, rtol=1e-3)
    
    # Plastic centroid must have shifted left and down
    assert results.cx_plastic < 0.0
    assert results.cy_plastic < 0.0
    
    # Eccentricities
    assert np.isclose(results.e_x, results.cx_plastic, rtol=1e-3)
    assert np.isclose(results.e_y, results.cy_plastic, rtol=1e-3)

def test_generate_octagonal_outer_perimeter():
    """
    Test the generation of the octagonal outer perimeter for SSR checks.
    """
    x_c, y_c = 0.0, 0.0
    c1, c2 = 400.0, 400.0
    d = 200.0
    rail_length = 500.0
    
    perimeter = generate_octagonal_outer_perimeter(x_c, y_c, c1, c2, d, rail_length)
    
    assert isinstance(perimeter, MultiLineString)
    
    # Check total length of the octagon
    # Top, Bottom, Left, Right faces are length c1 = 400
    # The diagonals connect points spanning (rail_length + d/2).
    # Since rail_length is from column face: 
    # dist_x = c1/2 + rail_length + d/2 = 200 + 500 + 100 = 800
    # Diagonal spans from x = c1/2 (200) to dist_x (800), dx = 600
    # Diagonal spans from y = dist_y (800) to c2/2 (200), dy = 600
    # Diagonal length = sqrt(600^2 + 600^2) = sqrt(720000) = 848.528
    # 4 straight sides (4 * 400 = 1600)
    # 4 diagonal sides (4 * 848.528 = 3394.11)
    # Total expected b0_out = 1600 + 3394.11 = 4994.11
    
    total_length = perimeter.length
    assert np.isclose(total_length, 4994.11, rtol=1e-3)

import pytest
import numpy as np
from types import SimpleNamespace
from Core.Geometry import ColumnLocation, generate_octagonal_outer_perimeter, discretize_shapely_line, calculate_section_properties
from Models.Materials import Concrete, Rebar
from Models.Results import PunchingShearInput
from Codes.CSA_A23_3_19 import (
    calc_vc_unreinforced,
    calc_gamma_v,
    calc_max_shear_stress,
    check_maximum_ssr_stress,
    calc_vc_with_ssr,
    design_ssr_rails
)

def get_base_inputs(location=ColumnLocation.INTERIOR):
    concrete = Concrete(name="30MPa", fc=30, unit_weight=24.0)
    rebar = Rebar(name="400W", fy=400)
    return PunchingShearInput(
        slab_thickness=250.0, c_top=50.0, c_bot=50.0,
        c1=300.0, c2=400.0, x_c=0.0, y_c=0.0,
        Vf=100.0, Mf_x=50.0, Mf_y=50.0,
        concrete=concrete, rebar=rebar, location=location
    )

def test_calc_vc_unreinforced():
    """
    Test v_c unreinforced logic.
    For a 300x400 column, d=200, fc=30, phi_c=0.65, lamb=1.0.
    """
    inputs = get_base_inputs(ColumnLocation.INTERIOR)
    # Mock geometry where b0 = 2000
    geom = SimpleNamespace(b0=2000.0)
    
    # Expected v_c
    phi_c = 0.65
    fc = 30.0
    lamb = 1.0
    beta_c = 400 / 300  # 1.333
    d = 200.0
    b0 = 2000.0
    
    v_135 = (1 + 2/beta_c) * lamb * phi_c * np.sqrt(fc) # (1 + 1.5) * 0.65 * 5.477 = 2.5 * 3.56 = 8.90
    v_136 = (4.0 * d / b0 + 0.19) * lamb * phi_c * np.sqrt(fc) # (800/2000 + 0.19) * 3.56 = (0.4 + 0.19) * 3.56 = 0.59 * 3.56 = 2.10
    v_137 = 0.38 * lamb * phi_c * np.sqrt(fc) # 0.38 * 3.56 = 1.35
    
    expected_v = min(v_135, v_136, v_137)
    
    # d factor = min(1.0, 1300 / (1000 + 200)) = min(1.0, 1300/1200) = 1.0
    expected_d_factor = 1.0
    
    v, d_factor = calc_vc_unreinforced(inputs, geom)
    
    assert np.isclose(v, expected_v, rtol=1e-3)
    assert np.isclose(d_factor, expected_d_factor, rtol=1e-3)

def test_calc_gamma_v():
    """
    Test gamma_v logic.
    b1, b2 are dimension of critical section parallel and perp to moment axis.
    """
    inputs = get_base_inputs()
    # c1 = 300, c2 = 400
    
    # For X axis, b1 = c1 = 300, b2 = c2 = 400
    expected_gamma_x = 1 - 1 / (1 + (2/3) * np.sqrt(300 / 400))
    gamma_x = calc_gamma_v(inputs, "x")
    assert np.isclose(gamma_x, expected_gamma_x, rtol=1e-3)
    
    # For Y axis, b1 = c2 = 400, b2 = c1 = 300
    expected_gamma_y = 1 - 1 / (1 + (2/3) * np.sqrt(400 / 300))
    gamma_y = calc_gamma_v(inputs, "y")
    assert np.isclose(gamma_y, expected_gamma_y, rtol=1e-3)

def test_calc_max_shear_stress():
    """
    Test the calculation of vf taking into account the geometry eccentricities and Jx/Jy.
    """
    inputs = get_base_inputs()
    d = 200.0
    
    # Mock geometry for test
    geom = SimpleNamespace(
        b0=2000.0,
        Jx=1e9,
        Jy=2e9,
        e_x=50.0, # Eccentricity in X
        e_y=-30.0 # Eccentricity in Y
    )
    
    Vf = 500_000.0 # N
    Mf_x = 100_000_000.0 # N-mm
    Mf_y = 75_000_000.0 # N-mm
    
    gamma_vx = 0.4
    gamma_vy = 0.4
    
    # Direct shear = Vf / (b0 * d) = 500,000 / (2000 * 200) = 500,000 / 400,000 = 1.25 MPa
    # X moment stress = gamma_vx * Mf_x * e_x / Jx = 0.4 * 100,000,000 * 50.0 / 1e9 = 2,000,000,000 / 1,000,000,000 = 2.0 MPa
    # Y moment stress = gamma_vy * Mf_y * e_y / Jy = 0.4 * 75,000,000 * (-30.0) / 2e9 = -900,000,000 / 2,000,000,000 = -0.45 MPa
    
    expected_vf = 1.25 + 2.0 - 0.45 # = 2.80 MPa
    
    vf = calc_max_shear_stress(Vf, Mf_x, Mf_y, inputs, geom, gamma_vx, gamma_vy)
    
    assert np.isclose(vf, expected_vf, rtol=1e-3)

def test_check_maximum_ssr_stress():
    """
    Tests the v_r_max capacity check (0.75 * phi_c * lambda * sqrt(f_c)).
    """
    inputs = get_base_inputs()
    
    phi_c = 0.65
    lamb = 1.0
    fc = 30.0
    
    expected_vr_max = 0.75 * phi_c * lamb * np.sqrt(fc)
    
    vr_max = check_maximum_ssr_stress(inputs)
    assert np.isclose(vr_max, expected_vr_max, rtol=1e-3)

def test_calc_vc_with_ssr():
    """
    Tests the v_c drop when SSR is used (0.28 * phi_c * lambda * sqrt(f_c)).
    """
    inputs = get_base_inputs()
    
    phi_c = 0.65
    lamb = 1.0
    fc = 30.0
    
    expected_vc_ssr = 0.28 * phi_c * lamb * np.sqrt(fc)
    
    vc_ssr = calc_vc_with_ssr(inputs)
    assert np.isclose(vc_ssr, expected_vc_ssr, rtol=1e-3)

def test_design_ssr_rails_success():
    """
    Test the SSR rail design loop iterating and finding a successful outer perimeter.
    Ensure minimum rail length is enforced (2.0 * d).
    """
    inputs = get_base_inputs(ColumnLocation.INTERIOR)
    # Give it a tiny shear so it passes on the first iteration stress-wise
    inputs.Vf = 10.0 # kN
    inputs.Mf_x = 0.0
    inputs.Mf_y = 0.0
    vf = 0.5 # Mock shear stress
    
    # Needs initial geometry
    outer_perimeter_line = generate_octagonal_outer_perimeter(
        x_c=inputs.x_c, y_c=inputs.y_c, 
        c1=inputs.c1, c2=inputs.c2, 
        d=inputs.d, rail_length=100.0
    )
    fibers = discretize_shapely_line(outer_perimeter_line, inputs.d)
    geom = calculate_section_properties(fibers, inputs.d, inputs.x_c, inputs.y_c)
    
    result = design_ssr_rails(inputs, geom, vf, stud_diameter=12.7)
    
    assert result["success"] is True
    assert "required_rail_length" in result
    assert "num_studs_per_rail" in result
    assert result["vf_out"] <= result["v_c_out_limit"]
    
    # The minimum required rail length should be at least 2*d
    assert result["required_rail_length"] >= 2.0 * inputs.d

def test_design_ssr_rails_failure():
    """
    Test the SSR rail design loop failing to find a viable perimeter within max length.
    """
    inputs = get_base_inputs(ColumnLocation.INTERIOR)
    # Give it an impossible shear force so it iterates up to max_rail_length
    inputs.Vf = 50000.0 # kN
    inputs.Mf_x = 0.0
    inputs.Mf_y = 0.0
    vf = 15.0 # Mock high shear stress
    
    outer_perimeter_line = generate_octagonal_outer_perimeter(
        x_c=inputs.x_c, y_c=inputs.y_c, 
        c1=inputs.c1, c2=inputs.c2, 
        d=inputs.d, rail_length=100.0
    )
    fibers = discretize_shapely_line(outer_perimeter_line, inputs.d)
    geom = calculate_section_properties(fibers, inputs.d, inputs.x_c, inputs.y_c)
    
    # Cap max rail length to 300 to run test faster
    # Note: since minimum rail length is 2*d (400), this will fail because max length is less than minimum.
    result = design_ssr_rails(inputs, geom, vf, stud_diameter=12.7, max_rail_length=300.0)
    
    assert result["success"] is False
    assert result["required_rail_length"] == 300.0

from Models.Materials import Concrete, Rebar
from Models.Results import PunchingShearInput
from Core.Geometry import ColumnLocation, calculate_punching_properties
from Codes.CSA_A23_3_19 import design_ssr_rails, calc_max_shear_stress, calc_gamma_v

concrete = Concrete(name="35MPa", fc=35.0, unit_weight=24.0)
rebar = Rebar(name="400W", fy=400.0)

inputs = PunchingShearInput(
    slab_thickness=250.0,
    c_top=30.0,
    c_bot=30.0,
    c1=300.0,
    c2=600.0,
    x_c=0.0,
    y_c=0.0,
    Vf=900.0,
    Mf_x=120.0,
    Mf_y=-150.0,
    concrete=concrete, 
    rebar=rebar, 
    location=ColumnLocation.EDGE
)

slab_bounds = [
    0.0 - 5000.0,
    0.0 - 5000.0,
    0.0 + 1000.0,
    0.0 + 1500.0
]

geometry = calculate_punching_properties(inputs, slab_bounds, fiber_length=5.0, plot=False)

ssr_design = design_ssr_rails(
    inputs=inputs, 
    slab_bounds=slab_bounds, 
    initial_geometry=geometry, 
    vf=1.0, # not needed for vf_out
    stud_diameter=12.7,
    stud_yield_stress=345.0,
    user_s0=75.0,
    user_s=150.0,
    spacing_increment=12.7
)

print(ssr_design)
# Math
from math import sqrt
import math

# Materials
from Models.Results import PunchingShearInput
from types import SimpleNamespace
from Core.Geometry import ColumnLocation, generate_octagonal_outer_perimeter, discretize_shapely_line, calculate_section_properties

# Constants from CSA A23.3-19
PHI_C = 0.65  # Resistance factor for concrete
PHI_S = 0.85  # Resistance factor for steel

# Alpha values for v_c calculation (Table 13.1)
ALPHA_INTERIOR = 4.0
ALPHA_EDGE = 3.0
ALPHA_CORNER = 2.0

def calc_vc_unreinforced(inputs: PunchingShearInput, geometry: SimpleNamespace) -> list[float]:
    """
    Calculates the unreinforced concrete shear capacity (v_c) as the minimum of
    three values from CSA A23.3-19 Cl 13.3.4.1 (a, b, c).
    Includes size effect factor if d > 300 mm.
    """
    # Concrete Properties
    phi_c = inputs.concrete.phi_c
    fc = inputs.concrete.fc
    lamb = inputs.concrete.lamb
    # Column Properties
    a = max(inputs.c1, inputs.c2)
    b = min(inputs.c1, inputs.c2)
    location = inputs.location
    b0 = geometry.b0
    # Slab Properties
    d = inputs.d

    # Eqn 13.5
    beta_c = a / b
    v_135 = (1 +  2/beta_c) * lamb * phi_c * sqrt(fc)
    # Eqn 13.6
    if location == ColumnLocation.INTERIOR:
        alpha_s = ALPHA_INTERIOR
    elif location == ColumnLocation.EDGE:
        alpha_s = ALPHA_EDGE
    else:
        alpha_s = ALPHA_CORNER
    v_136 = (alpha_s * d / b0 + 0.19) * lamb * phi_c * sqrt(fc)
    # Eqn 137
    v_137 = 0.38 * lamb * phi_c * sqrt(fc)

    v = min(v_135, v_136, v_137)
    d_factor = min(1.0, 1300.0 / (1000.0 + d))

    return [v, d_factor]


def calc_gamma_v(inputs: PunchingShearInput, axis: str) -> float:
    """
    Calculates the portion of moment transferred by eccentricity of shear (gamma_v).
    """
    b1 = inputs.c1 if axis == "x" else inputs.c2
    b2 = inputs.c2 if axis == "x" else inputs.c1

    return 1 - 1 / ( 1 + (2/3)*sqrt(b1 / b2))

def calc_max_shear_stress(v_f: float, m_fx: float, m_fy: float, inputs: PunchingShearInput, geometry: SimpleNamespace, gamma_vx: float, gamma_vy: float) -> float:
    b0 = geometry.b0
    d = inputs.d
    # Eccentricity should come from the geometry object, not the concrete object.
    e_x = geometry.e_x
    e_y = geometry.e_y
    J_x = geometry.Jx
    J_y = geometry.Jy
    return  (v_f/(b0 * d)) + (gamma_vx * m_fx * e_x / J_x) + (gamma_vy * m_fy * e_y / J_y)


def check_maximum_ssr_stress(inputs: PunchingShearInput) -> float:
    """
    Calculates the maximum allowable stress with SSR
    per CSA A23.3-19 Cl 13.3.9.4.
    Returns: v_r_max in MPa.
    """
    phi_c = inputs.concrete.phi_c
    fc = inputs.concrete.fc
    lamb = inputs.concrete.lamb
    
    # Cl 13.3.9.4
    v_r_max = 0.75 * phi_c * lamb * sqrt(fc)
    
    return v_r_max

def calc_vc_with_ssr(inputs: PunchingShearInput) -> float:
    """
    Calculates the concrete shear capacity when SSR is used (v_c_ssr)
    per CSA A23.3-19 Cl 13.3.9.5.
    """
    phi_c = inputs.concrete.phi_c
    fc = inputs.concrete.fc
    lamb = inputs.concrete.lamb
    
    # Cl 13.3.9.5
    v_c_ssr = 0.28 * phi_c * lamb * sqrt(fc)
    
    return v_c_ssr

def generate_stud_rails(inputs: PunchingShearInput, s0: float, s: float, num_studs: int, rail_length: float, slab_bounds: list[float]) -> list[list[tuple]]:
    """
    Generates the coordinates for the stud rails.
    For CSA A23.3-19, typical detailing starts the rails aligned with the column corners
    and spreading orthogonally. 
    """
    x_c, y_c = inputs.x_c, inputs.y_c
    c1, c2 = inputs.c1, inputs.c2
    d = inputs.d
    
    rails = []
    
    slab_xmin, slab_ymin, slab_xmax, slab_ymax = slab_bounds
    x_min_col = x_c - c1 / 2
    x_max_col = x_c + c1 / 2
    y_min_col = y_c - c2 / 2
    y_max_col = y_c + c2 / 2
    
    dist_left = x_min_col - slab_xmin
    dist_right = slab_xmax - x_max_col
    dist_bottom = y_min_col - slab_ymin
    dist_top = slab_ymax - y_max_col
    
    # A rail cannot develop if it hits the edge of the slab.
    # The active limits here should depend on whether the rail itself hits the boundary.
    # To be safe, we use the actual rail_length for truncation if provided, else use the 5d limit.
    active_left = dist_left <= rail_length
    active_right = dist_right <= rail_length
    active_bottom = dist_bottom <= rail_length
    active_top = dist_top <= rail_length

    # Helper to generate a single rail
    def make_rail(start_x, start_y, dx, dy):
        rail = []
        for i in range(num_studs):
            dist = s0 + i * s
            rail.append((start_x + dist * dx, start_y + dist * dy))
        return rail

    # Right face (aligned with corners)
    if not active_right:
        rails.append(make_rail(x_max_col, y_max_col, 1, 0)) # Top-Right corner, extending Right
        rails.append(make_rail(x_max_col, y_min_col, 1, 0)) # Bottom-Right corner, extending Right
        
    # Left face (aligned with corners)
    if not active_left:
        rails.append(make_rail(x_min_col, y_max_col, -1, 0)) # Top-Left corner, extending Left
        rails.append(make_rail(x_min_col, y_min_col, -1, 0)) # Bottom-Left corner, extending Left
        
    # Top face (aligned with corners)
    if not active_top:
        rails.append(make_rail(x_max_col, y_max_col, 0, 1)) # Top-Right corner, extending Up
        rails.append(make_rail(x_min_col, y_max_col, 0, 1)) # Top-Left corner, extending Up
        
    # Bottom face (aligned with corners)
    if not active_bottom:
        rails.append(make_rail(x_max_col, y_min_col, 0, -1)) # Bottom-Right corner, extending Down
        rails.append(make_rail(x_min_col, y_min_col, 0, -1)) # Bottom-Left corner, extending Down

    return rails

def design_ssr_rails(inputs: PunchingShearInput, slab_bounds: list[float], initial_geometry: SimpleNamespace, vf: float, stud_diameter: float = 12.7, stud_yield_stress: float = 345.0, user_s0: float = None, user_s: float = None, spacing_increment: float = 12.7, max_rail_length: float = 2000.0) -> dict:
    """
    Designs the SSR rails by iteratively expanding the outer perimeter until 
    the shear stress drops below the unreinforced concrete capacity limit for 
    outer perimeters (0.19 * phi_c * lambda * sqrt(f_c)).
    
    Returns the required rail length, final geometry, and stud layout details.
    """
    phi_c = inputs.concrete.phi_c
    fc = inputs.concrete.fc
    lamb = inputs.concrete.lamb
    d = inputs.d
    phi_s = inputs.rebar.phi_s
    f_y_stud = stud_yield_stress
    
    # 1. Determine number of rails based on the INITIAL active edges
    # The requirement is a minimum of 2 rails per column face.
    # Note: As rails extend, new edges may become active!
    slab_xmin, slab_ymin, slab_xmax, slab_ymax = slab_bounds
    x_min_col = inputs.x_c - inputs.c1 / 2
    x_max_col = inputs.x_c + inputs.c1 / 2
    y_min_col = inputs.y_c - inputs.c2 / 2
    y_max_col = inputs.y_c + inputs.c2 / 2
    
    dist_left = x_min_col - slab_xmin
    dist_right = slab_xmax - x_max_col
    dist_bottom = y_min_col - slab_ymin
    dist_top = slab_ymax - y_max_col

    # Area of one stud
    a_v = math.pi * (stud_diameter / 2)**2
    
    # Helper to calculate initial requirements
    def calc_reqs(num_rails_current):
        v_c_ssr = calc_vc_with_ssr(inputs)
        v_s_req_current = max(0.0, vf - v_c_ssr)
        
        b0 = initial_geometry.b0
        
        if v_s_req_current > 0:
            total_Av = num_rails_current * a_v
            s_req_current = (phi_s * total_Av * f_y_stud) / (b0 * v_s_req_current)
        else:
            s_req_current = float('inf')
            
        s0_max = 0.4 * d
        if vf > 0.56 * phi_c * lamb * sqrt(fc):
            s_max_code = 0.5 * d
        else:
            s_max_code = 0.75 * d
            
        s_max_allowed = min(s_req_current, s_max_code)

        if user_s0 is not None:
            s0_val = min(user_s0, s0_max)
        else:
            s0_val = s0_max
        s0_val = math.floor(s0_val / spacing_increment) * spacing_increment
        if s0_val == 0: s0_val = spacing_increment

        if user_s is not None:
            s_val = min(user_s, s_max_allowed)
        else:
            s_val = s_max_allowed
        s_val = math.floor(s_val / spacing_increment) * spacing_increment
        if s_val == 0: s_val = spacing_increment
            
        return s0_val, s_val

    gamma_vx = calc_gamma_v(inputs, "x")
    gamma_vy = calc_gamma_v(inputs, "y")
    v_c_out_limit = 0.19 * phi_c * lamb * sqrt(fc)

    # Initial calculation assuming base condition
    if inputs.location == ColumnLocation.INTERIOR: num_rails = 8
    elif inputs.location == ColumnLocation.EDGE: num_rails = 6
    elif inputs.location == ColumnLocation.CORNER: num_rails = 4
    else: num_rails = 8

    s0, s = calc_reqs(num_rails)
    step_size = s
    min_rail_ext = 2.0 * d
    n_min = math.ceil((min_rail_ext - s0) / s) + 1
    if n_min < 1: n_min = 1
    rail_length = s0 + (n_min - 1) * s

    while rail_length <= max_rail_length:
        # Re-evaluate active edges dynamically based on current rail length
        # A rail extends `rail_length` from the column face. The outer perimeter is at `rail_length + d/2`.
        # If the outer perimeter intersects an edge, that edge becomes active and truncates the perimeter.
        
        # A safe way to handle this is to treat the rail as intersecting the edge if it gets within d/2.
        active_left_dynamic = dist_left <= (rail_length + d/2)
        active_right_dynamic = dist_right <= (rail_length + d/2)
        active_bottom_dynamic = dist_bottom <= (rail_length + d/2)
        active_top_dynamic = dist_top <= (rail_length + d/2)
        
        active_edge_count = sum([active_left_dynamic, active_right_dynamic, active_bottom_dynamic, active_top_dynamic])
        
        if active_edge_count > 2:
            return {
                "success": False,
                "required_rail_length": rail_length,
                "vf_out": None,
                "message": f"Rail length ({rail_length} mm) expanded past 3 or more slab edges. Section cannot develop enough perimeter."
            }

        # Adjust num_rails based on newly active edges
        dynamic_num_rails = 8 - (active_edge_count * 2)
        
        # If num_rails changed, our provided `s` might no longer be valid for the required `vs` demand at the critical section.
        # We must re-calculate `s` to ensure the *inner* critical section is still satisfied with fewer rails.
        if dynamic_num_rails != num_rails:
            num_rails = dynamic_num_rails
            new_s0, new_s = calc_reqs(num_rails)
            
            # Since we have fewer rails, the code allowed max spacing might be the same, but s_req_current 
            # drops drastically because fewer rails must resist the same shear demand!
            
            # If the newly required spacing dropped, we need to enforce it and recalculate length.
            # Even if user_s is provided, it must not exceed new_s if new_s is clamped by s_req_current.
            if new_s < s:
                s = new_s
                step_size = s
                
                # If the step_size goes below a logical physical minimum (like our increment), we fail.
                # Otherwise it might infinite loop if new_s becomes tiny or 0 due to extreme lack of capacity.
                if s < spacing_increment:
                    return {
                        "success": False,
                        "required_rail_length": rail_length,
                        "vf_out": None,
                        "message": f"Required stud spacing ({s} mm) dropped below minimum increment. Not enough capacity."
                    }

                # We can't shrink rail_length, but we must ensure it aligns with the new spacing increment
                num_studs = math.ceil((rail_length - s0) / s) + 1
                rail_length = s0 + (num_studs - 1) * s
                continue # Re-run loop with new tight spacing

        outer_perimeter_line = generate_octagonal_outer_perimeter(
            x_c=inputs.x_c, y_c=inputs.y_c, 
            c1=inputs.c1, c2=inputs.c2, 
            d=d, rail_length=rail_length,
            slab_bounds=slab_bounds
        )
        
        fibers = discretize_shapely_line(outer_perimeter_line, d)
        outer_geometry = calculate_section_properties(fibers, d, inputs.x_c, inputs.y_c)
        
        vf_out = calc_max_shear_stress(
            v_f=inputs.Vf * 1000, 
            m_fx=inputs.Mf_x * 1e6, 
            m_fy=inputs.Mf_y * 1e6,
            inputs=inputs, 
            geometry=outer_geometry, 
            gamma_vx=gamma_vx, 
            gamma_vy=gamma_vy
        )
        
        if vf_out <= v_c_out_limit:
            # We found the required distance!
            num_studs_per_rail = math.ceil((rail_length - s0) / s) + 1
            actual_rail_length = s0 + (num_studs_per_rail - 1) * s
            
            stud_rails = generate_stud_rails(inputs, s0, s, num_studs_per_rail, actual_rail_length, slab_bounds)
            
            return {
                "success": True,
                "stud_diameter": stud_diameter,
                "s0": s0,
                "s": s,
                "num_rails": num_rails,
                "num_studs_per_rail": num_studs_per_rail,
                "required_rail_length": actual_rail_length,
                "vf_out": vf_out,
                "v_c_out_limit": v_c_out_limit,
                "final_geometry": outer_geometry,
                "outer_perimeter_line": outer_perimeter_line,
                "stud_rails": stud_rails
            }
            
        rail_length += step_size
        
    return {
        "success": False,
        "required_rail_length": max_rail_length,
        "vf_out": None,
        "message": "Maximum rail length exceeded before stress dropped below limit."
    }
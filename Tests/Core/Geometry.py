import numpy as np
from shapely.geometry import MultiLineString, Polygon, Point
from enum import Enum
from types import SimpleNamespace

class ColumnLocation(str, Enum):
    """Enumeration for column location types."""
    INTERIOR = "Interior"
    EDGE = "Edge"
    CORNER = "Corner"

def build_csa_perimeter(x_c: float, y_c: float, cx: float, cy: float, d: float, slab_bounds: list[float]) -> MultiLineString:
    """
    Builds the critical shear perimeter honoring CSA A23.3-19 edge rules.
    If a slab edge is within 5d, the perimeter opens towards it and extends 
    up to a maximum of d from the column face.
    """
    slab_xmin, slab_ymin, slab_xmax, slab_ymax = slab_bounds
    
    # Column faces
    x_min_col = x_c - cx / 2
    x_max_col = x_c + cx / 2
    y_min_col = y_c - cy / 2
    y_max_col = y_c + cy / 2
    
    # Distance from column faces to slab edges
    dist_left = x_min_col - slab_xmin
    dist_right = slab_xmax - x_max_col
    dist_bottom = y_min_col - slab_ymin
    dist_top = slab_ymax - y_max_col
    
    # CSA Rule: Is the edge within 5d?
    active_left = dist_left <= 5 * d
    active_right = dist_right <= 5 * d
    active_bottom = dist_bottom <= 5 * d
    active_top = dist_top <= 5 * d
    
    # Calculate the extension of the perpendicular legs
    # Extends to the slab edge if active, otherwise d/2 from face
    x_left_ext = x_min_col - min(dist_left, d) if active_left else x_min_col - d / 2
    x_right_ext = x_max_col + min(dist_right, d) if active_right else x_max_col + d / 2
    y_bottom_ext = y_min_col - min(dist_bottom, d) if active_bottom else y_min_col - d / 2
    y_top_ext = y_max_col + min(dist_top, d) if active_top else y_max_col + d / 2
    
    segments = []
    
    # Top Face (Exists if Top is NOT an active edge)
    if not active_top:
        segments.append(((x_left_ext, y_top_ext), (x_right_ext, y_top_ext)))
        
    # Bottom Face (Exists if Bottom is NOT an active edge)
    if not active_bottom:
        segments.append(((x_left_ext, y_bottom_ext), (x_right_ext, y_bottom_ext)))
        
    # Left Face (Exists if Left is NOT an active edge)
    if not active_left:
        segments.append(((x_left_ext, y_bottom_ext), (x_left_ext, y_top_ext)))
        
    # Right Face (Exists if Right is NOT an active edge)
    if not active_right:
        segments.append(((x_right_ext, y_bottom_ext), (x_right_ext, y_top_ext)))
        
    return MultiLineString(segments)

def discretize_shapely_line(geometry: MultiLineString, d: float, fiber_length: float = 5.0) -> list[dict]:
    """Breaks the MultiLineString into discrete fibers for Jx/Jy integration."""
    fibers = []
    for line in geometry.geoms:
        coords = list(line.coords)
        for i in range(len(coords) - 1):
            x1, y1 = coords[i]
            x2, y2 = coords[i+1]
            
            L_seg = np.hypot(x2 - x1, y2 - y1)
            if L_seg < 1e-6:
                continue
                
            num_fibers = max(1, int(np.ceil(L_seg / fiber_length)))
            fiber_area = (L_seg / num_fibers) * d
            
            for j in range(num_fibers):
                fraction = (j + 0.5) / num_fibers
                fx = x1 + fraction * (x2 - x1)
                fy = y1 + fraction * (y2 - y1)
                fibers.append({'x': fx, 'y': fy, 'A': fiber_area})
                
    return fibers

def calculate_section_properties(fibers: list[dict], d: float, x_c: float = 0.0, y_c: float = 0.0) -> SimpleNamespace:
    """Calculate section properties from discretized fibers."""
    if not fibers:
        raise ValueError("No effective shear perimeter could be generated.")
        
    x_coords = np.array([f['x'] for f in fibers])
    y_coords = np.array([f['y'] for f in fibers])
    areas = np.array([f['A'] for f in fibers])
    
    # Calculate Section Properties
    Ac = np.sum(areas)
    b0 = Ac / d
    cx_plastic = np.sum(x_coords * areas) / Ac
    cy_plastic = np.sum(y_coords * areas) / Ac
    
    # Calculate moments of inertia about the plastic centroid
    Jx = np.sum(areas * (y_coords - cy_plastic)**2)
    Jy = np.sum(areas * (x_coords - cx_plastic)**2)
    
    # Eccentricity is the distance from the column center to the plastic centroid
    e_x = cx_plastic - x_c
    e_y = cy_plastic - y_c
    
    return SimpleNamespace(
        b0=b0,
        Ac=Ac,
        cx_plastic=cx_plastic,
        cy_plastic=cy_plastic,
        Jx=Jx,
        Jy=Jy,
        e_x=e_x,
        e_y=e_y
    )

def calculate_punching_properties(inputs, slab_bounds: list[float], fiber_length: float = 5.0, plot: bool = False) -> SimpleNamespace:
    """Orchestrates perimeter generation and section property calculation."""
    x_c, y_c = inputs.x_c, inputs.y_c
    cx = inputs.c1
    cy = inputs.c2

    # Single source of truth for effective depth
    d = getattr(inputs, 'd', inputs.slab_thickness - inputs.c_top)
    
    # 1. Generate the Code-Compliant Perimeter
    effective_shear_line = build_csa_perimeter(x_c, y_c, cx, cy, d, slab_bounds)
    
    # 2. Discretize into fibers
    fibers = discretize_shapely_line(effective_shear_line, d, fiber_length)
    
    # 3. Calculate Section Properties, passing in the column center for eccentricity
    results = calculate_section_properties(fibers, d, x_c, y_c)
    
    # 4. Optional Plotting
    if plot:
        from Utilities.plotting import plot_punching_shear
        plot_punching_shear(x_c, y_c, cx, cy, effective_shear_line, results.cx_plastic, results.cy_plastic, slab_bounds, d)

    return results

def generate_octagonal_outer_perimeter(x_c: float, y_c: float, c1: float, c2: float, d: float, rail_length: float, slab_bounds: list[float] = None) -> MultiLineString:
    """
    Generates the outer shear perimeter for a column with SSR, honoring slab edges.
    For an interior column, this is an octagon formed by connecting points 
    located d/2 past the outermost studs on the orthogonal rails.
    
    If a slab edge is within 5d, the perimeter opens towards it and extends 
    up to a maximum of d from the column face.
    """
    if slab_bounds is None:
        slab_bounds = [-float('inf'), -float('inf'), float('inf'), float('inf')]
        
    slab_xmin, slab_ymin, slab_xmax, slab_ymax = slab_bounds
    
    # Column faces
    x_min_col = x_c - c1 / 2
    x_max_col = x_c + c1 / 2
    y_min_col = y_c - c2 / 2
    y_max_col = y_c + c2 / 2
    
    # Distance from column faces to slab edges
    dist_left = x_min_col - slab_xmin
    dist_right = slab_xmax - x_max_col
    dist_bottom = y_min_col - slab_ymin
    dist_top = slab_ymax - y_max_col
    
    # CSA Rule: Is the edge within 5d?
    active_left = dist_left <= 5 * d
    active_right = dist_right <= 5 * d
    active_bottom = dist_bottom <= 5 * d
    active_top = dist_top <= 5 * d
    
    # Base distances (without edge interference)
    dist_x_base = (c1 / 2) + rail_length + (d / 2)
    dist_y_base = (c2 / 2) + rail_length + (d / 2)
    
    # Extension of perpendicular legs towards active edges (capped at d)
    ext_left_active = x_min_col - min(dist_left, d)
    ext_right_active = x_max_col + min(dist_right, d)
    ext_bottom_active = y_min_col - min(dist_bottom, d)
    ext_top_active = y_max_col + min(dist_top, d)
    
    # Initialize bounds for the perimeter segments
    # The perimeter forms an octagon using these 8 points unless interrupted by an edge.
    
    p_tl = (x_c - c1/2, y_c + dist_y_base) if not active_top else (x_c - c1/2, ext_top_active)
    p_tr = (x_c + c1/2, y_c + dist_y_base) if not active_top else (x_c + c1/2, ext_top_active)
    
    p_rt = (x_c + dist_x_base, y_c + c2/2) if not active_right else (ext_right_active, y_c + c2/2)
    p_rb = (x_c + dist_x_base, y_c - c2/2) if not active_right else (ext_right_active, y_c - c2/2)
    
    p_br = (x_c + c1/2, y_c - dist_y_base) if not active_bottom else (x_c + c1/2, ext_bottom_active)
    p_bl = (x_c - c1/2, y_c - dist_y_base) if not active_bottom else (x_c - c1/2, ext_bottom_active)
    
    p_lb = (x_c - dist_x_base, y_c - c2/2) if not active_left else (ext_left_active, y_c - c2/2)
    p_lt = (x_c - dist_x_base, y_c + c2/2) if not active_left else (ext_left_active, y_c + c2/2)
    
    segments = []
    
    # Top Face
    if not active_top:
        segments.append((p_tl, p_tr))
    
    # Top-Right diagonal (only if neither is an active edge)
    if not active_top and not active_right:
        segments.append((p_tr, p_rt))
    elif active_right and not active_top:
        # Extend top straight line to the right edge boundary
        segments.append((p_tr, (ext_right_active, p_tr[1])))
    elif active_top and not active_right:
        # Extend right straight line to the top edge boundary
        segments.append(((p_rt[0], ext_top_active), p_rt))
        
    # Right Face
    if not active_right:
        segments.append((p_rt, p_rb))
        
    # Bottom-Right diagonal
    if not active_right and not active_bottom:
        segments.append((p_rb, p_br))
    elif active_bottom and not active_right:
        segments.append((p_rb, (p_rb[0], ext_bottom_active)))
    elif active_right and not active_bottom:
        segments.append(((ext_right_active, p_br[1]), p_br))
        
    # Bottom Face
    if not active_bottom:
        segments.append((p_br, p_bl))
        
    # Bottom-Left diagonal
    if not active_bottom and not active_left:
        segments.append((p_bl, p_lb))
    elif active_left and not active_bottom:
        segments.append((p_bl, (ext_left_active, p_bl[1])))
    elif active_bottom and not active_left:
        segments.append(((p_lb[0], ext_bottom_active), p_lb))
        
    # Left Face
    if not active_left:
        segments.append((p_lb, p_lt))
        
    # Top-Left diagonal
    if not active_left and not active_top:
        segments.append((p_lt, p_tl))
    elif active_top and not active_left:
        segments.append((p_lt, (p_lt[0], ext_top_active)))
    elif active_left and not active_top:
        segments.append(((ext_left_active, p_tl[1]), p_tl))

    return MultiLineString(segments)

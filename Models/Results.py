from dataclasses import dataclass, field
from Models.Materials import Concrete, Rebar
from Core.Geometry import ColumnLocation

class PunchingShearInput:
    """Input parameters for punching shear analysis."""
    def __init__(self, slab_thickness: float, c_top: float, c_bot: float, c1: float, c2: float, x_c: float, y_c: float, Vf: float, Mf_x: float, Mf_y: float, concrete: Concrete, rebar: Rebar, location: ColumnLocation):
        self.slab_thickness: float  = slab_thickness # mm
        self.c_top: float = c_top  # Top slab cover, mm
        self.c_bot: float = c_bot # Bottom slab cover, mm
        self.c1: float = c1 # Column dimension parallel to bending axis, mm
        self.c2: float = c2 # Column dimension perpendicular to bending axis, mm
        self.x_c: float = x_c  # Column location on x-axis, mm
        self.y_c: float =y_c  # Column location on y-axis, mm
        self.d: float = slab_thickness - c_top# Effective depth, mm
        self.Vf: float = Vf  # Factored shear force, kN
        self.Mf_x: float = Mf_x  # Factored moment about x-axis, kNm
        self.Mf_y: float = Mf_y  # Factored moment about y-axis, kNm
        self.concrete: Concrete = concrete
        self.rebar: Rebar = rebar
        self.location: ColumnLocation = location

@dataclass
class PunchingShearResult:
    """Results of the punching shear analysis."""
    v_f: float = 0.0  # Factored shear stress, MPa
    v_c: float = 0.0  # Unreinforced shear resistance, MPa
    v_r_max: float = 0.0  # Maximum shear resistance with SSR, MPa
    gamma_vx: float = 0.0  # Moment transfer factor, x-axis
    gamma_vy: float = 0.0  # Moment transfer factor, y-axis
    Ac: float = 0.0  # Area of critical perimeter, mm^2
    Jc_x: float = 0.0  # Polar moment of inertia, x-axis, mm^4
    Jc_y: float = 0.0  # Polar moment of inertia, y-axis, mm^4
    is_ok: bool = False
    ssr_required: bool = False
    # Detailed results for reporting
    report: dict = field(default_factory=dict)

from dataclasses import dataclass

@dataclass
class Concrete:
    """Represents concrete material properties."""
    name: str
    fc: float  # Compressive strength in MPa
    unit_weight: float  # Unit weight in kN/m^3
    lamb: float = 1.0  # Factor for lightweight concrete
    phi_c: float = 0.65  # Resistance factor for concrete

    @property
    def alpha1(self) -> float:
        """Stress block factor alpha1 per CSA A23.3-19 Cl 10.1.7."""
        return 0.85 - 0.0015 * self.fc if self.fc > 28 else 0.85

    @property
    def beta1(self) -> float:
        """Stress block factor beta1 per CSA A23.3-19 Cl 10.1.7."""
        value = 0.97 - 0.0025 * self.fc
        return max(0.67, value)

@dataclass
class Rebar:
    """Represents reinforcing steel properties."""
    name: str
    fy: float  # Yield strength in MPa
    phi_s: float = 0.85  # Resistance factor for steel

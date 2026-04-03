# CSA A23.3-19 Punching Shear Reference Guide

This document outlines the specific clauses, equations, and implementation notes required for the core punching shear calculation engine.

## 1. Critical Shear Perimeter
**Clause 13.3.3.1:** The critical section for two-way shear shall be perpendicular to the plane of the slab and located so that its perimeter, $b_0$, is a minimum, but need not approach closer than $d/2$ to the perimeter of the concentrated load or reaction area.
* **Implementation Note:** For rectangular interior columns, this establishes the base dimensions:
  * $b_1 = c_1 + d$ (Parallel to moment)
  * $b_2 = c_2 + d$ (Perpendicular to moment)
  * The algorithm must dynamically adjust these bounds for edge/corner columns where the perimeter terminates at the slab edge.

## 2. Concrete Shear Strength (Unreinforced)
**Clause 13.3.4.1:** The two-way shear resistance of the concrete, $v_c$, shall be the smallest of:
1. $v_c = 0.38 \phi_c \lambda \sqrt{f'_c}$
2. $v_c = 0.19 \left(1 + \frac{2}{\beta_c}\right) \phi_c \lambda \sqrt{f'_c}$
3. $v_c = \left(0.19 + \frac{\alpha_s d}{b_0}\right) \phi_c \lambda \sqrt{f'_c}$

* **Variables:** * $\beta_c$ = ratio of long side to short side of the column.
  * $\alpha_s$ = $4$ for interior columns, $3$ for edge columns, $2$ for corner columns.
* **Clause 13.3.4.3 (Size Effect):** If the effective depth, $d$, exceeds $300\text{ mm}$, the value of $v_c$ obtained from Cl. 13.3.4.1 shall be multiplied by $1300 / (1000 + d)$.
* **Implementation Note:** The Python function for $v_c$ must evaluate all three equations and return the `min()` value, automatically applying the size effect multiplier if $d > 300\text{ mm}$.

## 3. Unbalanced Moment Transfer (Shear Fraction)
**Clause 13.3.5.2:** The fraction of the unbalanced moment transferred by eccentricity of shear, $\gamma_v$, shall be calculated as:
$$\gamma_v = 1 - \frac{1}{1 + \frac{2}{3} \sqrt{\frac{b_1}{b_2}}}$$
* **Implementation Note:** $b_1$ is always the dimension of the critical perimeter parallel to the axis of the applied moment. If biaxial moments are present, the script must calculate a separate $\gamma_{vx}$ and $\gamma_{vy}$.

## 4. Unbalanced Moment Transfer (Flexural Fraction)
**Clause 13.3.5.3:** The fraction of the unbalanced moment transferred by flexure, $\gamma_f$, shall be calculated as:
$$\gamma_f = 1 - \gamma_v$$
* **Implementation Note:** This moment ($M_{f,flex} = \gamma_f \cdot M_f$) must be assumed to be transferred over a width of slab equal to the column width plus $1.5h$ on each side of the column. The script should output this effective band width ($b_{band} = c_2 + 3h$) and the required steel area ($A_s$) to warn the user of potential rebar congestion.

## 5. Maximum Shear Stress with Headed Studs
**Clause 13.3.8.2:** The maximum factored shear stress, $v_f$, at the critical section defined in Clause 13.3.3.1 shall not exceed:
$$v_{r,max} = 0.75 \phi_c \lambda \sqrt{f'_c}$$
* **Implementation Note:** If the applied stress $v_f$ exceeds this value, the script must immediately throw a `ValueError` or a "FAIL" status. Adding more shear studs will not prevent the concrete web from crushing; the slab must be thickened or the column enlarged.

## 6. Reduced Concrete Capacity with Headed Studs
**Clause 13.3.8.3:** When shear reinforcement is required, the concrete shear resistance, $v_c$, shall be reduced to:
$$v_c = 0.28 \phi_c \lambda \sqrt{f'_c}$$
* **Implementation Note:** The algorithm must switch to this reduced coefficient to calculate the required steel stress ($v_s = v_f - v_c$) once studs are deemed necessary.

## 7. Headed Stud Spacing Limits
**Clause 13.3.8.5:** The spacing between the column face and the first line of shear reinforcement shall not exceed $0.4d$. The spacing between successive lines of shear reinforcement shall not exceed:
* $0.5d$ if $v_f \le 0.56 \phi_c \lambda \sqrt{f'_c}$
* $0.25d$ if $v_f > 0.56 \phi_c \lambda \sqrt{f'_c}$
* **Implementation Note:** The script should default to generating stud layouts at a spacing of $0.5d$, but must include a conditional check to tighten the spacing to $0.25d$ under extremely high shear demands.

## 8. Outer Critical Perimeter (Extent of Rails)
**Clause 13.3.8.6:** Shear reinforcement shall be extended outward from the column until the factored shear stress, $v_f$, at the critical section outside the shear reinforcement is not greater than:
$$v_{c,out} = 0.19 \phi_c \lambda \sqrt{f'_c}$$
* **Implementation Note:** This perimeter is an octagon (for interior columns) located $d/2$ past the outermost peripheral line of shear reinforcement. The script must utilize a `while` loop, incrementally adding studs and recalculating the polygonal geometry ($A_{out}$, $c_{out}$, $J_{out}$) until the combined shear and moment stress drops below this threshold.
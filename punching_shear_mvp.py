import marimo

__generated_with = "0.22.4"
app = marimo.App(width="columns", app_title="Punching Shear")


@app.cell
def _():
    import marimo as mo
    from Models.Materials import Concrete, Rebar
    from Models.Results import PunchingShearInput
    from Core.Geometry import ColumnLocation, calculate_punching_properties
    from Codes.CSA_A23_3_19 import (
        calc_vc_unreinforced,
        calc_gamma_v,
        calc_max_shear_stress,
        check_maximum_ssr_stress,
        design_ssr_rails
    )
    from Utilities.plotting_plotly import plot_punching_shear, plot_applied_loads

    return (
        ColumnLocation,
        Concrete,
        PunchingShearInput,
        Rebar,
        calc_gamma_v,
        calc_max_shear_stress,
        calc_vc_unreinforced,
        calculate_punching_properties,
        check_maximum_ssr_stress,
        design_ssr_rails,
        mo,
        plot_applied_loads,
        plot_punching_shear,
    )


@app.cell
def _(mo):
    # 1. Define Materials
    mo.md("### Materials")

    fc_input = mo.ui.number(value=35.0, label="Concrete Strength f'c (MPa)", start=20.0, stop=100.0, step=5.0)
    fy_input = mo.ui.number(value=400.0, label="Rebar Yield fy (MPa)", start=300.0, stop=500.0, step=100.0)
    return fc_input, fy_input


@app.cell
def _(fc_input, fy_input, mo):
    mo.vstack([fc_input, fy_input])
    return


@app.cell
def _(Concrete, Rebar, fc_input, fy_input):
    concrete = Concrete(
        name=f"{fc_input.value}MPa",
        fc=fc_input.value,
        unit_weight=24.0
    )

    rebar = Rebar(
        name=f"{fy_input.value}W",
        fy=fy_input.value
    )
    return concrete, rebar


@app.cell
def _(mo):
    mo.md("### Geometry and Loads")

    slab_thickness_input = mo.ui.number(value=250.0, label="Slab Thickness (mm)", start=150.0, stop=1000.0, step=10.0)
    c1_input = mo.ui.number(value=300.0, label="Column Width c1 (mm)", start=200.0, stop=2000.0, step=50.0)
    c2_input = mo.ui.number(value=600.0, label="Column Depth c2 (mm)", start=200.0, stop=2000.0, step=50.0)

    vf_input = mo.ui.number(value=1200.0, label="Shear Force Vf (kN)", start=0.0, stop=10000.0, step=50.0)
    mfx_input = mo.ui.number(value=120.0, label="Moment Mfx (kNm)", start=-5000.0, stop=5000.0, step=10.0)
    mfy_input = mo.ui.number(value=-200.0, label="Moment Mfy (kNm)", start=-5000.0, stop=5000.0, step=10.0)

    # Edge distances inputs
    dist_left_input = mo.ui.number(value=5000.0, label="Dist to Left Edge (mm)", start=0.0, stop=20000.0, step=100.0)
    dist_right_input = mo.ui.number(value=1000.0, label="Dist to Right Edge (mm)", start=0.0, stop=20000.0, step=100.0)
    dist_top_input = mo.ui.number(value=5000.0, label="Dist to Top Edge (mm)", start=0.0, stop=20000.0, step=100.0)
    dist_bottom_input = mo.ui.number(value=5000.0, label="Dist to Bottom Edge (mm)", start=0.0, stop=20000.0, step=100.0)
    return (
        c1_input,
        c2_input,
        dist_bottom_input,
        dist_left_input,
        dist_right_input,
        dist_top_input,
        mfx_input,
        mfy_input,
        slab_thickness_input,
        vf_input,
    )


@app.cell
def _(
    c1_input,
    c2_input,
    dist_bottom_input,
    dist_left_input,
    dist_right_input,
    dist_top_input,
    mfx_input,
    mfy_input,
    mo,
    slab_thickness_input,
    vf_input,
):
    mo.vstack([
        slab_thickness_input,
        mo.hstack([c1_input, c2_input]),
        mo.hstack([vf_input, mfx_input, mfy_input]),
        mo.md("#### Slab Edge Distances (from column center)"),
        mo.hstack([dist_left_input, dist_right_input]),
        mo.hstack([dist_bottom_input, dist_top_input])
    ])
    return


@app.cell
def _(
    ColumnLocation,
    PunchingShearInput,
    c1_input,
    c2_input,
    concrete,
    dist_bottom_input,
    dist_left_input,
    dist_right_input,
    dist_top_input,
    mfx_input,
    mfy_input,
    rebar,
    slab_thickness_input,
    vf_input,
):
    # Auto-detect column location based on edge distances
    d = slab_thickness_input.value - 30.0 # Assuming c_top = 30.0
    x_c, y_c = 0.0, 0.0
    c1, c2 = c1_input.value, c2_input.value

    # Distance from column faces to slab edges
    d_left = dist_left_input.value - c1/2
    d_right = dist_right_input.value - c1/2
    d_bottom = dist_bottom_input.value - c2/2
    d_top = dist_top_input.value - c2/2

    active_edges = 0
    if d_left <= 5 * d: active_edges += 1
    if d_right <= 5 * d: active_edges += 1
    if d_bottom <= 5 * d: active_edges += 1
    if d_top <= 5 * d: active_edges += 1

    if active_edges == 0:
        detected_location = ColumnLocation.INTERIOR
    elif active_edges == 1:
        detected_location = ColumnLocation.EDGE
    else:
        detected_location = ColumnLocation.CORNER

    # 2. Define Input Data
    inputs = PunchingShearInput(
        slab_thickness=slab_thickness_input.value,
        c_top=30.0,
        c_bot=30.0,
        c1=c1,
        c2=c2,
        x_c=x_c,
        y_c=y_c,
        Vf=vf_input.value,
        Mf_x=mfx_input.value,
        Mf_y=mfy_input.value,
        concrete=concrete, rebar=rebar, location=detected_location
    )

    slab_bounds = [
        x_c - dist_left_input.value,
        y_c - dist_bottom_input.value,
        x_c + dist_right_input.value,
        y_c + dist_top_input.value
    ]
    return detected_location, inputs, slab_bounds


@app.cell
def _(detected_location, mo):
    mo.md(f"**Auto-detected Location:** {detected_location.value}")
    return


@app.cell
def _(inputs, mo, plot_applied_loads):
    loads_fig = plot_applied_loads(inputs)
    mo.ui.plotly(loads_fig)
    return


@app.cell
def _(calculate_punching_properties, inputs, mo, slab_bounds):
    # 3. Calculate Core Geometry & Plot
    geometry = calculate_punching_properties(inputs, slab_bounds, fiber_length=5.0, plot=False)

    geom_output = mo.md(f"""
    ### Critical Shear Perimeter
    - **b0:** {geometry.b0:.1f} mm
    - **Ac:** {geometry.Ac:.1f} mm²
    - **Centroid (x, y):** ({geometry.cx_plastic:.1f}, {geometry.cy_plastic:.1f}) mm
    - **Eccentricity (e_x, e_y):** ({geometry.e_x:.1f}, {geometry.e_y:.1f}) mm
    - **Jx:** {geometry.Jx:.2e} mm⁴
    - **Jy:** {geometry.Jy:.2e} mm⁴
    """)
    return geom_output, geometry


@app.cell
def _(geom_output):
    geom_output
    return


@app.cell
def _(
    calc_gamma_v,
    calc_max_shear_stress,
    calc_vc_unreinforced,
    check_maximum_ssr_stress,
    design_ssr_rails,
    geometry,
    inputs,
    mo,
    plot_punching_shear,
    slab_bounds,
):
    # 4. CSA A23.3-19 Capacity Checks
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
        gamma_vy=gamma_vy
    )

    checks_md = f"""
    ### Code Checks
    - **v_f (Factored Shear Stress):** {vf:.3f} MPa
    - **v_c (Unreinforced Capacity):** {v_c:.3f} MPa
    - **v_r_max (Max Allowed w/ SSR):** {v_r_max:.3f} MPa
    """

    fig = None
    if vf <= v_c:
        result_md = "✅ **PASS: Unreinforced capacity is adequate.**"
    elif vf <= v_r_max:
        result_md = "⚠️ **WARNING: Unreinforced capacity exceeded. SSR Required!**"

        # 5. SSR Design Loop
        ssr_design = design_ssr_rails(inputs, slab_bounds, geometry, vf, stud_diameter=12.7)

        if ssr_design["success"]:
            fig = plot_punching_shear(
                inputs.x_c, inputs.y_c, inputs.c1, inputs.c2,
                ssr_design['outer_perimeter_line'],
                ssr_design['final_geometry'].cx_plastic,
                ssr_design['final_geometry'].cy_plastic,
                slab_bounds, inputs.d,
                stud_rails=ssr_design['stud_rails'],
                required_rail_length=ssr_design['required_rail_length']
            )
            result_md += f"""

            ### SSR Design Results
            ✅ **OUTER PERIMETER PASSES** at rail length: {ssr_design['required_rail_length']:.1f} mm
            - **Outer v_f:** {ssr_design['vf_out']:.3f} MPa (Limit: {ssr_design['v_c_out_limit']:.3f} MPa)

            #### SSR Detailing
            - **Stud Diameter:** {ssr_design['stud_diameter']} mm
            - **Number of Rails:** {ssr_design['num_rails']}
            - **Studs per Rail:** {ssr_design['num_studs_per_rail']}
            - **Distance to First Stud (s0):** {ssr_design['s0']:.1f} mm
            - **Spacing Between Studs (s):** {ssr_design['s']:.1f} mm
            - **Total Rail Length:** {ssr_design['required_rail_length']:.1f} mm
            """
        else:
            result_md += f"\n\n❌ **SSR Design Failed:** {ssr_design['message']}"
    else:
        result_md = "❌ **FAIL: Stress exceeds v_r_max. Section must be resized.**"

    code_checks_output = mo.md(checks_md + "\n\n" + result_md)
    return code_checks_output, fig


@app.cell
def _(code_checks_output):
    code_checks_output
    return


@app.cell
def _(fig, mo):
    mo.ui.plotly(fig) if fig is not None else mo.md("_No plot required._")
    return


if __name__ == "__main__":
    app.run()

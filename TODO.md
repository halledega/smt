# Development Roadmap: Punching Shear MVP

## Phase 1: Core Engine & MVP (Completed)
- [x] Task 0.5: Repository Audit
    - [x] Ingest the existing codebase from the `Punching-Shear` repository.
    - [x] Provide a brief summary of what currently exists.
    - [x] Outline a step-by-step refactoring plan to migrate the existing code into the `Core/` and `Codes/` directory structure specified in the LLM_SPEC.
    - [x] Wait for user approval before modifying or rewriting any files.
- [x] Task 1: `Models/Materials.py` (Completed during refactor)
    - Create dataclasses for `Concrete` (f_c, lambda, phi_c) and `Rebar` (f_y, phi_s).
- [x] Task 2: `Core/Geometry.py` (The heavy math)
    - [x] Write `generate_rectangular_perimeter(c1, c2, d, type)` returning Shapely coordinates. (Replaced with `build_csa_perimeter`)
    - [x] Write `calculate_polygon_properties(segments, d)` to return Area, x_bar, y_bar, and exact J_c.
    - [x] Write `generate_octagonal_outer_perimeter(c1, c2, d, rail_length)` for SSR checks.
- [x] Task 3: `Codes/CSA_A23_3_19.py` (Capacity Checks)
    - [x] Implement `calc_vc_unreinforced()`.
    - [x] Implement `calc_gamma_v()`.
    - [x] Implement `calc_max_shear_stress()`.
    - [x] Implement `check_maximum_ssr_stress()`.
- [x] Task 4: `Codes/CSA_A23_3_19.py` (The Loop)
    - [x] Write `design_ssr_rails()`: Calculates required studs on the critical face, then runs a `while` loop expanding the outer perimeter until stress <= 0.19 * phi_c * lambda * sqrt(f_c).
- [x] Task 5: `Tests/`
    - [x] Write Pytest fixtures comparing the `Geometry.py` outputs against known hand-calc values for J_c and A_c.
    - [x] Write tests for `Codes/CSA_A23_3_19.py` capacity checks.
- [x] Task 6: Jupyter MVP Integration
    - [x] Build `punching_shear_mvp.ipynb` to import the backend, define a test column, and print the results cleanly.

---

## Next Steps: Progress Halted Here (Phase 1 Complete)
**Current Status & Recent Achievements:**
*   Phase 1 MVP architecture is fully functional.
*   **Geometry Engine**: `shapely`-based engine successfully calculates exact perimeters and properties.
*   **SSR Design**: `design_ssr_rails` fully operates with an iterative loop that:
    *   Finds required rail length.
    *   Trunctuates outer perimeters against active slab bounds.
    *   Calculates necessary stud spacing.
    *   Draws visual representations of `stud_rails` emerging cleanly from column corners.
*   **Validation**: Tests implemented and green across geometry and code limit checks.
*   **Visuals**: Notebook cell integration with Matplotlib renders `plot_punching_shear` including column, slab bounds, inner/outer perimeters, and layout of individual SSR stud rails.

## Phase 2: Alpha (Upcoming)
- [ ] Add circular column geometry generation.
- [ ] Implement Cl 13.3.3.3: Ineffective areas due to slab openings (using Shapely intersection).
- [ ] Add traditional stirrup/hairpin design logic.
- [ ] Implement `reports/exporter.py` for Markdown/PDF generation.

## Phase 3: Beta (Upcoming)
- [ ] Build PySide desktop GUI.
- [ ] Integrate load ingestion from the concurrent/non-concurrent column reaction generator to bypass manual entry.
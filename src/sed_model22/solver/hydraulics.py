from __future__ import annotations

from pydantic import BaseModel

from ..config import OpeningConfig, PlanViewScenarioConfig
from ..mesh import MeshSummary
from ..metrics import ScenarioMetrics


class HydraulicsSolutionSummary(BaseModel):
    solver_name: str
    solver_status: str
    solver_model: str
    turbulence_model: str
    iterations: int
    converged: bool
    max_head_delta: float
    inlet_discharge_m3_s: float
    outlet_discharge_m3_s: float
    mass_balance_error: float
    mean_velocity_m_s: float
    max_velocity_m_s: float
    max_transverse_velocity_m_s: float
    blocked_face_count: int
    ignored_baffles: list[str]
    supported_scope: list[str]
    notes: list[str]


class HydraulicFieldData(BaseModel):
    x_centers_m: list[float]
    y_centers_m: list[float]
    head: list[list[float]]
    velocity_u_m_s: list[list[float]]
    velocity_v_m_s: list[list[float]]
    speed_m_s: list[list[float]]
    cell_divergence_1_per_s: list[list[float]]


def solve_steady_screening_flow(
    scenario: PlanViewScenarioConfig,
    mesh: MeshSummary,
    metrics: ScenarioMetrics,
) -> tuple[HydraulicsSolutionSummary, HydraulicFieldData]:
    """Solve the v0.1 plan-view screening field on a structured Cartesian grid.

    The solved field is a steady potential-flow proxy: a discrete Laplace problem
    for normalized head with Dirichlet inlet/outlet boundaries and no-flux walls
    and full-depth solid baffles. The head field is iterated with Gauss-Seidel
    updates plus successive over-relaxation, then scaled to the requested flow.
    """
    x_blocked, y_blocked, ignored_baffles = _build_blocked_faces(scenario, mesh)
    inlet_cells = _boundary_cells(scenario.inlet, mesh)
    outlet_cells = _boundary_cells(scenario.outlet, mesh)

    head = _initial_head_guess(scenario, mesh)
    iterations, converged, max_delta = _solve_head_field(
        scenario,
        mesh,
        head,
        inlet_cells,
        outlet_cells,
        x_blocked,
        y_blocked,
    )

    raw_inflow_per_depth = _boundary_discharge_per_depth(
        scenario.inlet,
        mesh,
        head,
        inlet_cells,
        is_inlet=True,
    )
    raw_outflow_per_depth = _boundary_discharge_per_depth(
        scenario.outlet,
        mesh,
        head,
        outlet_cells,
        is_inlet=False,
    )
    if raw_inflow_per_depth <= 0.0:
        raise ValueError("solver produced a non-positive inlet flux; cannot scale the flow field")

    scale_factor = scenario.hydraulics.flow_rate_m3_s / (raw_inflow_per_depth * scenario.geometry.water_depth_m)

    u_field: list[list[float]] = []
    v_field: list[list[float]] = []
    speed_field: list[list[float]] = []
    divergence_field: list[list[float]] = []

    max_velocity = 0.0
    max_transverse = 0.0
    total_speed = 0.0

    for i in range(mesh.nx):
        u_row: list[float] = []
        v_row: list[float] = []
        speed_row: list[float] = []
        divergence_row: list[float] = []

        for j in range(mesh.ny):
            q_w, q_e, q_s, q_n = _cell_face_fluxes(
                scenario,
                mesh,
                head,
                inlet_cells,
                outlet_cells,
                x_blocked,
                y_blocked,
                i,
                j,
            )
            u = scale_factor * 0.5 * (q_w + q_e)
            v = scale_factor * 0.5 * (q_s + q_n)
            divergence = scale_factor * (((q_e - q_w) / mesh.dx_m) + ((q_n - q_s) / mesh.dy_m))
            speed = (u * u + v * v) ** 0.5

            u_row.append(u)
            v_row.append(v)
            speed_row.append(speed)
            divergence_row.append(divergence)

            total_speed += speed
            if speed > max_velocity:
                max_velocity = speed
            if abs(v) > max_transverse:
                max_transverse = abs(v)

        u_field.append(u_row)
        v_field.append(v_row)
        speed_field.append(speed_row)
        divergence_field.append(divergence_row)

    inlet_discharge = raw_inflow_per_depth * scale_factor * scenario.geometry.water_depth_m
    outlet_discharge = raw_outflow_per_depth * scale_factor * scenario.geometry.water_depth_m
    mass_balance_error = abs(inlet_discharge - outlet_discharge) / max(abs(inlet_discharge), 1.0e-12)
    blocked_face_count = sum(sum(1 for value in row if value) for row in x_blocked) + sum(
        sum(1 for value in row if value) for row in y_blocked
    )

    summary = HydraulicsSolutionSummary(
        solver_name="v0.1_steady_screening_flow",
        solver_status="solved_screening_flow",
        solver_model=scenario.numerics.solver_model,
        turbulence_model=scenario.numerics.turbulence_model,
        iterations=iterations,
        converged=converged,
        max_head_delta=max_delta,
        inlet_discharge_m3_s=inlet_discharge,
        outlet_discharge_m3_s=outlet_discharge,
        mass_balance_error=mass_balance_error,
        mean_velocity_m_s=total_speed / metrics.basin_area_m2 * scenario.geometry.length_m * scenario.geometry.width_m / mesh.cell_count,
        max_velocity_m_s=max_velocity,
        max_transverse_velocity_m_s=max_transverse,
        blocked_face_count=blocked_face_count,
        ignored_baffles=ignored_baffles,
        supported_scope=[
            "steady screening-flow pattern comparison",
            "inlet and outlet placement screening",
            "full-depth solid baffle screening",
            "field and artifact generation",
        ],
        notes=[
            "Implemented as a steady screening-flow solve on a structured grid.",
            "Walls and full-depth solid baffles act as impermeable boundaries.",
            "This v0.1 solver does not model tracer transport, solids transport, or density effects.",
            f"Mesh sized at {mesh.nx} x {mesh.ny} cells.",
        ],
    )

    fields = HydraulicFieldData(
        x_centers_m=[(index + 0.5) * mesh.dx_m for index in range(mesh.nx)],
        y_centers_m=[(index + 0.5) * mesh.dy_m for index in range(mesh.ny)],
        head=head,
        velocity_u_m_s=u_field,
        velocity_v_m_s=v_field,
        speed_m_s=speed_field,
        cell_divergence_1_per_s=divergence_field,
    )
    return summary, fields


def _initial_head_guess(scenario: PlanViewScenarioConfig, mesh: MeshSummary) -> list[list[float]]:
    head: list[list[float]] = []
    for i in range(mesh.nx):
        row: list[float] = []
        for j in range(mesh.ny):
            x_fraction = (i + 0.5) / mesh.nx
            y_fraction = (j + 0.5) / mesh.ny

            if scenario.inlet.side == "west":
                value = 1.0 - x_fraction
            elif scenario.inlet.side == "east":
                value = x_fraction
            elif scenario.inlet.side == "south":
                value = 1.0 - y_fraction
            else:
                value = y_fraction

            row.append(max(0.0, min(1.0, value)))
        head.append(row)
    return head


def _solve_head_field(
    scenario: PlanViewScenarioConfig,
    mesh: MeshSummary,
    head: list[list[float]],
    inlet_cells: set[tuple[int, int]],
    outlet_cells: set[tuple[int, int]],
    x_blocked: list[list[bool]],
    y_blocked: list[list[bool]],
) -> tuple[int, bool, float]:
    """Iterate the discrete plan-view Laplace solve with SOR until tolerance.

    This applies in-place Gauss-Seidel sweeps over the structured grid with the
    user-provided relaxation factor. Convergence is reported by the maximum
    single-cell head update compared against the configured tolerance.
    """
    dx_coef = 1.0 / (mesh.dx_m * mesh.dx_m)
    dy_coef = 1.0 / (mesh.dy_m * mesh.dy_m)
    max_delta = 0.0
    converged = False
    iterations = 0

    for iteration in range(1, scenario.numerics.max_iterations + 1):
        max_delta = 0.0

        for i in range(mesh.nx):
            for j in range(mesh.ny):
                rhs = 0.0
                total_coef = 0.0

                for side, coef in (("west", dx_coef), ("east", dx_coef), ("south", dy_coef), ("north", dy_coef)):
                    contribution_coef, contribution_rhs = _neighbor_contribution(
                        scenario,
                        mesh,
                        head,
                        inlet_cells,
                        outlet_cells,
                        x_blocked,
                        y_blocked,
                        i,
                        j,
                        side,
                        coef,
                    )
                    total_coef += contribution_coef
                    rhs += contribution_rhs

                if total_coef <= 0.0:
                    continue

                candidate = rhs / total_coef
                updated = ((1.0 - scenario.numerics.relaxation_factor) * head[i][j]) + (
                    scenario.numerics.relaxation_factor * candidate
                )
                delta = abs(updated - head[i][j])
                head[i][j] = updated
                if delta > max_delta:
                    max_delta = delta

        iterations = iteration
        if max_delta <= scenario.numerics.tolerance:
            converged = True
            break

    return iterations, converged, max_delta


def _neighbor_contribution(
    scenario: PlanViewScenarioConfig,
    mesh: MeshSummary,
    head: list[list[float]],
    inlet_cells: set[tuple[int, int]],
    outlet_cells: set[tuple[int, int]],
    x_blocked: list[list[bool]],
    y_blocked: list[list[bool]],
    i: int,
    j: int,
    side: str,
    coef: float,
) -> tuple[float, float]:
    if side == "west":
        if i > 0 and not x_blocked[i - 1][j]:
            return coef, coef * head[i - 1][j]
        boundary_value = _boundary_value_for_face(scenario, inlet_cells, outlet_cells, side, i, j)
        if boundary_value is not None:
            boundary_coef = 2.0 * coef
            return boundary_coef, boundary_coef * boundary_value
        return 0.0, 0.0

    if side == "east":
        if i < mesh.nx - 1 and not x_blocked[i][j]:
            return coef, coef * head[i + 1][j]
        boundary_value = _boundary_value_for_face(scenario, inlet_cells, outlet_cells, side, i, j)
        if boundary_value is not None:
            boundary_coef = 2.0 * coef
            return boundary_coef, boundary_coef * boundary_value
        return 0.0, 0.0

    if side == "south":
        if j > 0 and not y_blocked[i][j - 1]:
            return coef, coef * head[i][j - 1]
        boundary_value = _boundary_value_for_face(scenario, inlet_cells, outlet_cells, side, i, j)
        if boundary_value is not None:
            boundary_coef = 2.0 * coef
            return boundary_coef, boundary_coef * boundary_value
        return 0.0, 0.0

    if j < mesh.ny - 1 and not y_blocked[i][j]:
        return coef, coef * head[i][j + 1]
    boundary_value = _boundary_value_for_face(scenario, inlet_cells, outlet_cells, side, i, j)
    if boundary_value is not None:
        boundary_coef = 2.0 * coef
        return boundary_coef, boundary_coef * boundary_value
    return 0.0, 0.0


def _boundary_value_for_face(
    scenario: PlanViewScenarioConfig,
    inlet_cells: set[tuple[int, int]],
    outlet_cells: set[tuple[int, int]],
    side: str,
    i: int,
    j: int,
) -> float | None:
    if scenario.inlet.side == side and (i, j) in inlet_cells:
        return 1.0
    if scenario.outlet.side == side and (i, j) in outlet_cells:
        return 0.0
    return None


def _boundary_cells(opening: OpeningConfig, mesh: MeshSummary) -> set[tuple[int, int]]:
    lower = opening.center_m - (opening.span_m / 2.0)
    upper = opening.center_m + (opening.span_m / 2.0)
    cells: set[tuple[int, int]] = set()

    if opening.side in ("west", "east"):
        boundary_i = 0 if opening.side == "west" else mesh.nx - 1
        for j in range(mesh.ny):
            cell_min = j * mesh.dy_m
            cell_max = (j + 1) * mesh.dy_m
            if _intervals_overlap(cell_min, cell_max, lower, upper):
                cells.add((boundary_i, j))
        return cells

    boundary_j = 0 if opening.side == "south" else mesh.ny - 1
    for i in range(mesh.nx):
        cell_min = i * mesh.dx_m
        cell_max = (i + 1) * mesh.dx_m
        if _intervals_overlap(cell_min, cell_max, lower, upper):
            cells.add((i, boundary_j))
    return cells


def _intervals_overlap(a0: float, a1: float, b0: float, b1: float) -> bool:
    return not (a1 <= b0 or b1 <= a0)


def _build_blocked_faces(
    scenario: PlanViewScenarioConfig,
    mesh: MeshSummary,
) -> tuple[list[list[bool]], list[list[bool]], list[str]]:
    x_blocked = [[False for _ in range(mesh.ny)] for _ in range(mesh.nx - 1)]
    y_blocked = [[False for _ in range(mesh.ny - 1)] for _ in range(mesh.nx)]
    ignored_baffles: list[str] = []

    for baffle in scenario.baffles:
        if baffle.kind != "full_depth_solid":
            ignored_baffles.append(baffle.name)
            continue

        if baffle.x1_m == baffle.x2_m:
            grid_line = min(max(int(round(baffle.x1_m / mesh.dx_m)), 1), mesh.nx - 1)
            face_index = grid_line - 1
            y_min = min(baffle.y1_m, baffle.y2_m)
            y_max = max(baffle.y1_m, baffle.y2_m)
            for j in range(mesh.ny):
                cell_min = j * mesh.dy_m
                cell_max = (j + 1) * mesh.dy_m
                if _intervals_overlap(cell_min, cell_max, y_min, y_max):
                    x_blocked[face_index][j] = True
            continue

        grid_line = min(max(int(round(baffle.y1_m / mesh.dy_m)), 1), mesh.ny - 1)
        face_index = grid_line - 1
        x_min = min(baffle.x1_m, baffle.x2_m)
        x_max = max(baffle.x1_m, baffle.x2_m)
        for i in range(mesh.nx):
            cell_min = i * mesh.dx_m
            cell_max = (i + 1) * mesh.dx_m
            if _intervals_overlap(cell_min, cell_max, x_min, x_max):
                y_blocked[i][face_index] = True

    ignored_baffles.sort()
    return x_blocked, y_blocked, ignored_baffles


def _boundary_discharge_per_depth(
    opening: OpeningConfig,
    mesh: MeshSummary,
    head: list[list[float]],
    boundary_cells: set[tuple[int, int]],
    *,
    is_inlet: bool,
) -> float:
    total = 0.0

    for i, j in boundary_cells:
        if opening.side == "west":
            gradient_flux = (1.0 - head[i][j]) / (0.5 * mesh.dx_m) if is_inlet else head[i][j] / (0.5 * mesh.dx_m)
            total += gradient_flux * mesh.dy_m
        elif opening.side == "east":
            gradient_flux = (1.0 - head[i][j]) / (0.5 * mesh.dx_m) if is_inlet else head[i][j] / (0.5 * mesh.dx_m)
            total += gradient_flux * mesh.dy_m
        elif opening.side == "south":
            gradient_flux = (1.0 - head[i][j]) / (0.5 * mesh.dy_m) if is_inlet else head[i][j] / (0.5 * mesh.dy_m)
            total += gradient_flux * mesh.dx_m
        else:
            gradient_flux = (1.0 - head[i][j]) / (0.5 * mesh.dy_m) if is_inlet else head[i][j] / (0.5 * mesh.dy_m)
            total += gradient_flux * mesh.dx_m

    return total


def _cell_face_fluxes(
    scenario: PlanViewScenarioConfig,
    mesh: MeshSummary,
    head: list[list[float]],
    inlet_cells: set[tuple[int, int]],
    outlet_cells: set[tuple[int, int]],
    x_blocked: list[list[bool]],
    y_blocked: list[list[bool]],
    i: int,
    j: int,
) -> tuple[float, float, float, float]:
    west_bc = _boundary_value_for_face(scenario, inlet_cells, outlet_cells, "west", i, j)
    east_bc = _boundary_value_for_face(scenario, inlet_cells, outlet_cells, "east", i, j)
    south_bc = _boundary_value_for_face(scenario, inlet_cells, outlet_cells, "south", i, j)
    north_bc = _boundary_value_for_face(scenario, inlet_cells, outlet_cells, "north", i, j)

    if i > 0 and not x_blocked[i - 1][j]:
        q_w = (head[i - 1][j] - head[i][j]) / mesh.dx_m
    elif west_bc is not None:
        q_w = (west_bc - head[i][j]) / (0.5 * mesh.dx_m)
    else:
        q_w = 0.0

    if i < mesh.nx - 1 and not x_blocked[i][j]:
        q_e = (head[i][j] - head[i + 1][j]) / mesh.dx_m
    elif east_bc is not None:
        q_e = (head[i][j] - east_bc) / (0.5 * mesh.dx_m)
    else:
        q_e = 0.0

    if j > 0 and not y_blocked[i][j - 1]:
        q_s = (head[i][j - 1] - head[i][j]) / mesh.dy_m
    elif south_bc is not None:
        q_s = (south_bc - head[i][j]) / (0.5 * mesh.dy_m)
    else:
        q_s = 0.0

    if j < mesh.ny - 1 and not y_blocked[i][j]:
        q_n = (head[i][j] - head[i][j + 1]) / mesh.dy_m
    elif north_bc is not None:
        q_n = (head[i][j] - north_bc) / (0.5 * mesh.dy_m)
    else:
        q_n = 0.0

    return q_w, q_e, q_s, q_n

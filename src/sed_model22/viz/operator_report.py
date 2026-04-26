from __future__ import annotations

import json
from pathlib import Path

from ..config import ScenarioConfig
from ..solver import HydraulicFieldData


def build_operator_report_html(
    scenario: ScenarioConfig,
    summary: dict,
    fields: HydraulicFieldData,
    *,
    generated_at_utc: str,
) -> str:
    payload = {
        "generatedAtUtc": generated_at_utc,
        "summary": summary,
        "fields": fields.model_dump(mode="json"),
        "operatorView": _build_operator_view(summary, fields),
    }

    html = _HTML_TEMPLATE.replace("__TITLE__", f"{scenario.metadata.title} Operator Report")
    html = html.replace("__PAYLOAD__", json.dumps(payload))
    return html


def write_operator_report_html(
    scenario: ScenarioConfig,
    summary: dict,
    fields: HydraulicFieldData,
    output_path: str | Path,
    *,
    generated_at_utc: str,
) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        build_operator_report_html(
            scenario,
            summary,
            fields,
            generated_at_utc=generated_at_utc,
        ),
        encoding="utf-8",
    )
    return destination


def _build_operator_view(summary: dict, fields: HydraulicFieldData) -> dict:
    solver = summary["solver"]
    metrics = summary["metrics"]
    geometry = summary["geometry"]
    quality_tier = summary.get("run_quality_tier", "unknown")
    quality_reasons = summary.get("quality_reasons", [])
    speed_values = [value for row in fields.speed_m_s for value in row]
    mean_speed = sum(speed_values) / max(len(speed_values), 1)
    max_speed = max(speed_values) if speed_values else 0.0
    low_speed_threshold = max(mean_speed * 0.45, max_speed * 0.18)
    low_speed_fraction = sum(1 for value in speed_values if value <= low_speed_threshold) / max(len(speed_values), 1)

    last_column = fields.speed_m_s[-1] if fields.speed_m_s else []
    if last_column:
        outlet_mean = sum(last_column) / len(last_column)
        outlet_variation = (
            sum((value - outlet_mean) ** 2 for value in last_column) / len(last_column)
        ) ** 0.5 / max(outlet_mean, 1.0e-12)
    else:
        outlet_variation = 0.0

    transverse_ratio = solver["max_transverse_velocity_m_s"] / max(solver["max_velocity_m_s"], 1.0e-12)

    if low_speed_fraction > 0.34 or transverse_ratio > 0.45:
        status_label = "Watch"
        status_color = "#9a6700"
        status_reason = "Some parts of the basin may not be using the full area evenly."
    else:
        status_label = "Stable"
        status_color = "#146c43"
        status_reason = "The basin looks reasonably even for a first-pass screening run."

    dead_zone_plain = _describe_dead_zone_screening(low_speed_fraction)
    outlet_plain = _describe_outlet_uniformity(outlet_variation)
    transverse_plain = _describe_transverse_redistribution(transverse_ratio)

    return {
        "overview": "A plain-language view of the current basin scenario. Use it to see where flow is concentrating, where water may be moving too slowly, and how evenly flow is approaching the outlet.",
        "statusLabel": status_label,
        "statusColor": status_color,
        "statusReason": status_reason,
        "kpis": [
            {"label": "Detention time", "value": f"{metrics['detention_time_h']:.2f} h"},
            {"label": "Surface overflow rate", "value": f"{metrics['surface_overflow_rate_m_per_d']:.1f} m/day"},
            {"label": "Peak water speed", "value": f"{solver['max_velocity_m_s']:.4f} m/s"},
            {"label": "Slow-moving area", "value": f"{low_speed_fraction * 100:.1f}%"},
        ],
        "metricList": [
            {"label": "Mass balance check", "value": f"{solver['mass_balance_error']:.3e}"},
            {"label": "Run quality tier", "value": str(quality_tier)},
            {"label": "Outlet flow variation", "value": f"{outlet_variation:.2f}"},
            {"label": "Peak side-flow speed", "value": f"{solver['max_transverse_velocity_m_s']:.4f} m/s"},
            {"label": "Baffle count", "value": str(summary["baffle_count"])},
            {"label": "Basin plan size", "value": f"{geometry['length_m']:.1f} × {geometry['width_m']:.1f} m"},
            {"label": "Mesh cells", "value": str(summary["mesh"]["cell_count"])},
        ],
        "engineeringList": [
            {"label": "Solver name", "value": solver["solver_name"]},
            {"label": "Solver model", "value": solver["solver_model"]},
            {"label": "Turbulence model", "value": solver["turbulence_model"]},
            {"label": "Converged?", "value": "Yes" if solver["converged"] else "No"},
            {"label": "Iterations", "value": str(solver["iterations"])},
            {"label": "Final head-change tolerance", "value": f"{solver['max_head_delta']:.3e}"},
            {"label": "Inlet discharge", "value": f"{solver['inlet_discharge_m3_s']:.4f} m3/s"},
            {"label": "Outlet discharge", "value": f"{solver['outlet_discharge_m3_s']:.4f} m3/s"},
            {"label": "Mean water speed", "value": f"{solver['mean_velocity_m_s']:.4f} m/s"},
            {"label": "Blocked mesh faces", "value": str(solver["blocked_face_count"])},
            {
                "label": "Quality reasons",
                "value": "; ".join(str(reason) for reason in quality_reasons) if quality_reasons else "n/a",
            },
        ],
        "scenarioTable": [
            {"label": "Case ID", "value": summary["metadata"]["case_id"]},
            {"label": "Scenario title", "value": summary["metadata"]["title"]},
            {"label": "Model stage", "value": summary["metadata"]["stage"]},
            {"label": "Flow rate", "value": f"{summary['hydraulics']['flow_rate_m3_s']:.4f} m3/s"},
            {"label": "Water temperature", "value": f"{summary['hydraulics']['temperature_c']:.1f} C"},
            {
                "label": "Basin dimensions",
                "value": (
                    f"{geometry['length_m']:.1f} m × {geometry['width_m']:.1f} m × "
                    f"{geometry['water_depth_m']:.1f} m"
                ),
            },
            {"label": "Baffle count", "value": str(summary["baffle_count"])},
            {"label": "Mesh", "value": f"{summary['mesh']['nx']} × {summary['mesh']['ny']}"},
        ],
        "hydraulicTable": [
            {
                "label": "Detention time",
                "value": f"{metrics['detention_time_h']:.2f} h",
                "valueSecondary": f"{metrics['detention_time_s']:.0f} s",
            },
            {
                "label": "Surface overflow rate",
                "value": f"{metrics['surface_overflow_rate_m_per_d']:.2f} m/day",
                "valueSecondary": f"{metrics['surface_overflow_rate_m_per_h']:.2f} m/h",
            },
            {"label": "Mean water speed", "value": f"{solver['mean_velocity_m_s']:.4f} m/s"},
            {"label": "Peak water speed", "value": f"{solver['max_velocity_m_s']:.4f} m/s"},
            {"label": "Peak side-flow speed", "value": f"{solver['max_transverse_velocity_m_s']:.4f} m/s"},
            {"label": "Slow-moving area", "value": f"{low_speed_fraction * 100:.1f}%"},
            {"label": "Outlet flow variation", "value": f"{outlet_variation:.2f}"},
            {"label": "Mass balance check", "value": f"{solver['mass_balance_error']:.3e}"},
        ],
        "boundaryTable": [
            {
                "label": "Inlet opening",
                "value": (
                    f"{summary['inlet']['side']} side, center {summary['inlet']['center_m']:.1f} m, "
                    f"span {summary['inlet']['span_m']:.1f} m"
                ),
            },
            {
                "label": "Outlet opening",
                "value": (
                    f"{summary['outlet']['side']} side, center {summary['outlet']['center_m']:.1f} m, "
                    f"span {summary['outlet']['span_m']:.1f} m"
                ),
            },
            {"label": "Wall condition", "value": summary["boundaries"]["wall_condition"].replace("_", " ")},
            {"label": "Baffle condition", "value": summary["boundaries"]["baffle_condition"].replace("_", " ")},
        ],
        "baffleTable": [
            {
                "name": baffle["name"],
                "kind": baffle["kind"].replace("_", " "),
                "segment": f"({baffle['x1_m']:.1f}, {baffle['y1_m']:.1f}) → ({baffle['x2_m']:.1f}, {baffle['y2_m']:.1f})",
            }
            for baffle in summary["baffles"]
        ],
        "scopeList": solver["supported_scope"],
        "solverNotes": solver["notes"],
        "takeaways": [
            {
                "title": "Dead-zone screening",
                "plain": dead_zone_plain,
                "technical": (
                    f"Technical basis: {low_speed_fraction * 100:.1f}% of cells fall in the low-speed screening band "
                    f"(speed <= {low_speed_threshold:.4f} m/s)."
                ),
            },
            {
                "title": "Outlet approach uniformity",
                "plain": outlet_plain,
                "technical": (
                    f"Technical basis: outlet approach coefficient of variation = {outlet_variation:.2f}. "
                    "Lower is better when comparing alternatives."
                ),
            },
            {
                "title": "Cross-basin redistribution",
                "plain": transverse_plain,
                "technical": (
                    f"Technical basis: peak transverse-to-total velocity ratio = {transverse_ratio:.2f}. "
                    "Higher values indicate stronger lateral redistribution around basin features."
                ),
            },
        ],
        "actions": [
            {
                "title": "Use this as a baseline run",
                "detail": "The report is most useful when compared directly against an alternative inlet, outlet, or baffle configuration with the same flow rate.",
            },
            {
                "title": "Watch low-speed pockets",
                "detail": "If an alternative scenario reduces the low-speed fraction while keeping outlet behavior smooth, it is usually a better screening candidate.",
            },
            {
                "title": "Keep the physics boundary in mind",
                "detail": "This interface is built on a V0.1 screening solve. Treat it as a decision-support preview, not final hydraulic certification.",
            },
        ],
    }


def _describe_dead_zone_screening(low_speed_fraction: float) -> str:
    percent = low_speed_fraction * 100
    if low_speed_fraction >= 0.55:
        return f"Large slow-moving zones are showing up across about {percent:.0f}% of the basin area."
    if low_speed_fraction >= 0.35:
        return f"Slow-moving zones are showing up across about {percent:.0f}% of the basin area."
    if low_speed_fraction >= 0.20:
        return f"Some slower pockets are showing up across about {percent:.0f}% of the basin area."
    return f"Only a small part of the basin, about {percent:.0f}% of the area, is in the slow-moving screening band."


def _describe_outlet_uniformity(outlet_variation: float) -> str:
    if outlet_variation >= 0.45:
        return "Flow is reaching the outlet unevenly, which can point to channeling or poor redistribution."
    if outlet_variation >= 0.25:
        return "Flow approaching the outlet is somewhat uneven."
    return "Flow approaching the outlet looks fairly even in this screening run."


def _describe_transverse_redistribution(transverse_ratio: float) -> str:
    if transverse_ratio >= 0.55:
        return "The layout is pushing flow strongly across the basin instead of keeping it in a mostly straight path."
    if transverse_ratio >= 0.30:
        return "The layout is causing a moderate amount of side-to-side flow redistribution."
    return "Most of the flow is staying in a mainly forward path with limited side-to-side redistribution."


_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>__TITLE__</title>
  <style>
    :root {
      --bg: #f4efe4;
      --paper: #fbf7ef;
      --ink: #182028;
      --muted: #5f6a73;
      --line: rgba(24, 32, 40, 0.14);
      --accent: #c25b2f;
      --accent-2: #134e4a;
      --shadow: 0 18px 60px rgba(24, 32, 40, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(194, 91, 47, 0.12), transparent 26%),
        linear-gradient(180deg, #f6f2e8 0%, #f1ebdf 100%);
    }
    .shell { min-height: 100vh; padding: 24px; }
    .frame {
      max-width: 1380px;
      margin: 0 auto;
      background: rgba(251, 247, 239, 0.88);
      backdrop-filter: blur(10px);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
    }
    .hero {
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      min-height: 78vh;
    }
    .hero-copy {
      padding: 48px 48px 40px;
      border-right: 1px solid var(--line);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }
    .eyebrow {
      font-size: 12px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 16px;
    }
    h1 {
      margin: 0;
      font-family: "IBM Plex Serif", Georgia, serif;
      font-size: clamp(2.9rem, 7vw, 5.6rem);
      line-height: 0.94;
      letter-spacing: -0.05em;
      max-width: 9ch;
    }
    .hero-sub {
      max-width: 34rem;
      margin-top: 18px;
      font-size: 1rem;
      line-height: 1.7;
      color: var(--muted);
    }
    .status-band {
      margin-top: 28px;
      display: inline-flex;
      align-items: center;
      gap: 10px;
      border: 1px solid var(--line);
      padding: 12px 14px;
      width: fit-content;
      background: rgba(255,255,255,0.45);
    }
    .status-dot {
      width: 10px;
      height: 10px;
      border-radius: 999px;
      background: var(--status-color);
      box-shadow: 0 0 0 8px color-mix(in srgb, var(--status-color) 12%, transparent);
    }
    .metric-row {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 16px;
      margin-top: 40px;
    }
    .metric {
      padding: 16px 0 0;
      border-top: 1px solid var(--line);
    }
    .metric-label {
      font-size: 12px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 8px;
    }
    .metric-value {
      font-family: "IBM Plex Serif", Georgia, serif;
      font-size: clamp(1.5rem, 2.2vw, 2.2rem);
      line-height: 1;
    }
    .hero-side {
      padding: 28px 28px 24px;
      display: grid;
      grid-template-rows: auto auto 1fr;
      gap: 18px;
      background: linear-gradient(180deg, rgba(19, 78, 74, 0.06) 0%, rgba(19, 78, 74, 0.02) 100%);
    }
    .panel-title {
      font-size: 12px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 10px;
    }
    .toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--line);
    }
    .toolbar strong { font-weight: 600; font-size: 0.98rem; }
    .mode-switch {
      display: inline-flex;
      gap: 6px;
      background: rgba(255,255,255,0.55);
      padding: 4px;
      border: 1px solid var(--line);
    }
    .mode-switch button {
      appearance: none;
      border: 0;
      background: transparent;
      color: var(--muted);
      font: inherit;
      padding: 8px 12px;
      cursor: pointer;
    }
    .mode-switch button.active { background: var(--ink); color: #fff; }
    .canvas-wrap {
      position: relative;
      background: linear-gradient(180deg, #fdf9f2 0%, #ede4d6 100%);
      border: 1px solid var(--line);
      min-height: 420px;
      overflow: hidden;
    }
    canvas { display: block; width: 100%; height: auto; }
    .legend {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      font-size: 0.88rem;
      color: var(--muted);
    }
    .legend-bar {
      flex: 1;
      height: 10px;
      background: linear-gradient(90deg, #1457eb 0%, #48a8d8 42%, #f1ca52 70%, #dd4b2f 100%);
      border: 1px solid rgba(24, 32, 40, 0.12);
    }
    .sections {
      display: grid;
      grid-template-columns: 1fr 1fr;
      border-top: 1px solid var(--line);
    }
    .section {
      padding: 28px;
      border-right: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
    }
    .section:nth-child(2n) { border-right: 0; }
    .takeaways { display: grid; gap: 12px; }
    .takeaway {
      padding: 14px 0;
      border-top: 1px solid var(--line);
    }
    .takeaway:first-child { border-top: 0; padding-top: 0; }
    .takeaway strong { display: block; font-size: 1rem; margin-bottom: 5px; }
    .takeaway .takeaway-plain { display: block; color: var(--ink); line-height: 1.55; }
    .takeaway .takeaway-technical {
      display: block;
      margin-top: 8px;
      color: var(--muted);
      line-height: 1.55;
      font-size: 0.92rem;
    }
    .plain-list {
      margin: 0;
      padding: 0;
      list-style: none;
      display: grid;
      gap: 10px;
    }
    .plain-list li {
      display: flex;
      justify-content: space-between;
      gap: 20px;
      padding-top: 10px;
      border-top: 1px solid var(--line);
      color: var(--muted);
    }
    .plain-list li strong { color: var(--ink); font-weight: 600; }
    .stack-list {
      margin: 0;
      padding: 0;
      list-style: none;
      display: grid;
      gap: 10px;
    }
    .stack-list li {
      padding-top: 10px;
      border-top: 1px solid var(--line);
      color: var(--muted);
      line-height: 1.55;
    }
    .stack-list li strong {
      display: block;
      margin-bottom: 4px;
      color: var(--ink);
      font-weight: 600;
    }
    .footer-note {
      padding: 20px 28px 28px;
      font-size: 0.88rem;
      color: var(--muted);
    }
    .appendix {
      padding: 28px;
      border-top: 1px solid var(--line);
      background: rgba(255,255,255,0.28);
    }
    .appendix-head {
      margin-bottom: 18px;
    }
    .appendix-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
    }
    .table-card {
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.42);
    }
    .table-card h3 {
      margin: 0;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      font-size: 0.95rem;
    }
    .data-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.92rem;
    }
    .data-table th,
    .data-table td {
      text-align: left;
      padding: 10px 16px;
      border-top: 1px solid var(--line);
      vertical-align: top;
    }
    .data-table tr:first-child th,
    .data-table tr:first-child td {
      border-top: 0;
    }
    .data-table th {
      width: 42%;
      color: var(--muted);
      font-weight: 600;
    }
    .data-table td {
      color: var(--ink);
    }
    .data-table__secondary {
      display: block;
      margin-top: 3px;
      color: var(--muted);
      font-size: 0.86rem;
    }
    @media (max-width: 1024px) {
      .hero { grid-template-columns: 1fr; min-height: auto; }
      .hero-copy { border-right: 0; border-bottom: 1px solid var(--line); }
      .metric-row, .sections { grid-template-columns: 1fr 1fr; }
      .appendix-grid { grid-template-columns: 1fr; }
    }
    @media (max-width: 720px) {
      .shell { padding: 12px; }
      .hero-copy, .hero-side, .section, .appendix, .footer-note { padding-left: 18px; padding-right: 18px; }
      .metric-row, .sections { grid-template-columns: 1fr; }
      .section { border-right: 0; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <div class="frame">
      <section class="hero" id="app"></section>
      <div class="footer-note" id="footer-note"></div>
    </div>
  </div>

  <script id="report-data" type="application/json">__PAYLOAD__</script>
  <script>
    const data = JSON.parse(document.getElementById('report-data').textContent);
    const app = document.getElementById('app');
    const footer = document.getElementById('footer-note');
    const summary = data.summary;
    const fields = data.fields;
    const operatorView = data.operatorView;
    document.documentElement.style.setProperty('--status-color', operatorView.statusColor);

    app.innerHTML = `
      <div class="hero-copy">
        <div>
          <div class="eyebrow">sed_model22 operator report</div>
          <h1>${summary.metadata.title}</h1>
          <div class="hero-sub">${operatorView.overview}</div>
          <div class="status-band">
            <span class="status-dot"></span>
            <div>
              <strong>${operatorView.statusLabel}</strong><br />
              <span style="color: var(--muted); font-size: 0.9rem;">${operatorView.statusReason}</span>
            </div>
          </div>
          <div class="metric-row">
            ${operatorView.kpis.map(kpi => `
              <div class="metric">
                <div class="metric-label">${kpi.label}</div>
                <div class="metric-value">${kpi.value}</div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
      <div class="hero-side">
        <div class="toolbar">
          <div>
            <div class="panel-title">Basin view</div>
            <strong>Interactive field view</strong>
          </div>
          <div class="mode-switch">
            <button class="active" data-mode="speed">Speed</button>
            <button data-mode="head">Head</button>
          </div>
        </div>
        <div class="canvas-wrap">
          <canvas id="heatmap" width="960" height="${Math.max(240, Math.round(960 * (summary.geometry.width_m / summary.geometry.length_m)))}"></canvas>
        </div>
        <div class="legend">
          <span id="legend-min">low</span>
          <div class="legend-bar"></div>
          <span id="legend-max">high</span>
        </div>
      </div>
    `;

    const sections = document.createElement('section');
    sections.className = 'sections';
    sections.innerHTML = `
      <section class="section">
        <div class="panel-title">Operator takeaways</div>
        <div class="takeaways">
          ${operatorView.takeaways.map(item => `
            <div class="takeaway">
              <strong>${item.title}</strong>
              <span class="takeaway-plain">${item.plain}</span>
              <span class="takeaway-technical">${item.technical}</span>
            </div>
          `).join('')}
        </div>
      </section>
      <section class="section">
        <div class="panel-title">Run metrics</div>
        <ul class="plain-list">
          ${operatorView.metricList.map(item => `
            <li><span>${item.label}</span><strong>${item.value}</strong></li>
          `).join('')}
        </ul>
      </section>
      <section class="section">
        <div class="panel-title">Recommended next actions</div>
        <div class="takeaways">
          ${operatorView.actions.map(item => `
            <div class="takeaway">
              <strong>${item.title}</strong>
              <span>${item.detail}</span>
            </div>
          `).join('')}
        </div>
      </section>
      <section class="section">
        <div class="panel-title">Scenario context</div>
        <ul class="plain-list">
          <li><span>Case</span><strong>${summary.metadata.case_id}</strong></li>
          <li><span>Inlet side / span</span><strong>${summary.inlet.side} / ${summary.inlet.span_m.toFixed(1)} m</strong></li>
          <li><span>Outlet side / span</span><strong>${summary.outlet.side} / ${summary.outlet.span_m.toFixed(1)} m</strong></li>
          <li><span>Baffles</span><strong>${summary.baffle_count}</strong></li>
          <li><span>Mesh</span><strong>${summary.mesh.nx} × ${summary.mesh.ny}</strong></li>
          <li><span>Generated</span><strong>${data.generatedAtUtc}</strong></li>
        </ul>
      </section>
      <section class="section">
        <div class="panel-title">Engineering detail</div>
        <ul class="plain-list">
          ${operatorView.engineeringList.map(item => `
            <li><span>${item.label}</span><strong>${item.value}</strong></li>
          `).join('')}
        </ul>
      </section>
      <section class="section">
        <div class="panel-title">Scope and limits</div>
        <ul class="stack-list">
          ${operatorView.scopeList.map(item => `
            <li><strong>Supported use</strong>${item}</li>
          `).join('')}
          ${operatorView.solverNotes.map(item => `
            <li><strong>Solver note</strong>${item}</li>
          `).join('')}
        </ul>
      </section>
    `;
    app.insertAdjacentElement('afterend', sections);

    const appendix = document.createElement('section');
    appendix.className = 'appendix';
    appendix.innerHTML = `
      <div class="appendix-head">
        <div class="panel-title">Technical appendix</div>
      </div>
      <div class="appendix-grid">
        ${renderTableCard('Scenario summary', operatorView.scenarioTable)}
        ${renderTableCard('Hydraulic metrics', operatorView.hydraulicTable)}
        ${renderTableCard('Solver details', operatorView.engineeringList)}
        ${renderTableCard('Boundary conditions', operatorView.boundaryTable)}
        ${renderBaffleTableCard(operatorView.baffleTable)}
        ${renderScopeCard(operatorView.scopeList, operatorView.solverNotes)}
      </div>
    `;
    sections.insertAdjacentElement('afterend', appendix);

    footer.textContent =
      'This report is a V0.1 screening view built from a steady structured-grid solve. It is for operator interpretation and scenario comparison, not final design certification.';

    function renderTableCard(title, rows) {
      return `
        <section class="table-card">
          <h3>${title}</h3>
          <table class="data-table">
            <tbody>
              ${rows.map(row => `
                <tr>
                  <th>${row.label}</th>
                  <td>
                    ${row.value || ''}
                    ${row.valueSecondary ? `<span class="data-table__secondary">${row.valueSecondary}</span>` : ''}
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </section>
      `;
    }

    function renderBaffleTableCard(rows) {
      if (!rows.length) {
        return `
          <section class="table-card">
            <h3>Baffles</h3>
            <table class="data-table">
              <tbody>
                <tr>
                  <th>Status</th>
                  <td>No baffles defined for this scenario.</td>
                </tr>
              </tbody>
            </table>
          </section>
        `;
      }

      return `
        <section class="table-card">
          <h3>Baffles</h3>
          <table class="data-table">
            <tbody>
              ${rows.map(row => `
                <tr>
                  <th>${row.name}</th>
                  <td>
                    ${row.kind}
                    <span class="data-table__secondary">${row.segment}</span>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </section>
      `;
    }

    function renderScopeCard(scopeList, solverNotes) {
      const rows = [
        ...scopeList.map(item => ({ label: 'Supported use', value: item })),
        ...solverNotes.map(item => ({ label: 'Solver note', value: item })),
      ];
      return renderTableCard('Scope and limits', rows);
    }

    const canvas = document.getElementById('heatmap');
    const ctx = canvas.getContext('2d');
    let currentMode = 'speed';

    function draw(mode) {
      const values = mode === 'head' ? fields.head : fields.speed_m_s;
      const flat = values.flat();
      const maxValue = Math.max(...flat);
      const minValue = Math.min(...flat);
      const range = Math.max(maxValue - minValue, 1e-12);
      const nx = fields.x_centers_m.length;
      const ny = fields.y_centers_m.length;
      const cellW = canvas.width / nx;
      const cellH = canvas.height / ny;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      for (let i = 0; i < nx; i++) {
        for (let j = 0; j < ny; j++) {
          const value = values[i][j];
          const t = (value - minValue) / range;
          ctx.fillStyle = colorRamp(t);
          ctx.fillRect(i * cellW, canvas.height - ((j + 1) * cellH), cellW + 0.5, cellH + 0.5);
        }
      }

      ctx.strokeStyle = 'rgba(24, 32, 40, 0.7)';
      ctx.lineWidth = 3;
      ctx.strokeRect(0, 0, canvas.width, canvas.height);
      drawBoundary(summary.inlet, '#18a957');
      drawBoundary(summary.outlet, '#d63e30');
      drawBaffles(summary.baffles || []);

      document.getElementById('legend-min').textContent =
        mode === 'head' ? `${minValue.toFixed(2)} head` : `${minValue.toFixed(4)} m/s`;
      document.getElementById('legend-max').textContent =
        mode === 'head' ? `${maxValue.toFixed(2)} head` : `${maxValue.toFixed(4)} m/s`;
    }

    function drawBoundary(boundary, color) {
      const sx = (x) => (x / summary.geometry.length_m) * canvas.width;
      const sy = (y) => canvas.height - ((y / summary.geometry.width_m) * canvas.height);
      const lower = boundary.center_m - (boundary.span_m / 2);
      const upper = boundary.center_m + (boundary.span_m / 2);
      ctx.strokeStyle = color;
      ctx.lineWidth = 8;
      ctx.beginPath();
      if (boundary.side === 'west') {
        ctx.moveTo(sx(0), sy(lower));
        ctx.lineTo(sx(0), sy(upper));
      } else if (boundary.side === 'east') {
        ctx.moveTo(sx(summary.geometry.length_m), sy(lower));
        ctx.lineTo(sx(summary.geometry.length_m), sy(upper));
      } else if (boundary.side === 'south') {
        ctx.moveTo(sx(lower), sy(0));
        ctx.lineTo(sx(upper), sy(0));
      } else {
        ctx.moveTo(sx(lower), sy(summary.geometry.width_m));
        ctx.lineTo(sx(upper), sy(summary.geometry.width_m));
      }
      ctx.stroke();
    }

    function drawBaffles(baffles) {
      const sx = (x) => (x / summary.geometry.length_m) * canvas.width;
      const sy = (y) => canvas.height - ((y / summary.geometry.width_m) * canvas.height);
      ctx.strokeStyle = '#182028';
      ctx.lineWidth = 5;
      baffles.forEach((baffle) => {
        ctx.beginPath();
        ctx.moveTo(sx(baffle.x1_m), sy(baffle.y1_m));
        ctx.lineTo(sx(baffle.x2_m), sy(baffle.y2_m));
        ctx.stroke();
      });
    }

    function colorRamp(t) {
      const x = Math.max(0, Math.min(1, t));
      const red = Math.round(20 + (220 * x));
      const green = Math.round(90 + (110 * (1 - x)));
      const blue = Math.round(235 - (180 * x));
      return `rgb(${red}, ${green}, ${blue})`;
    }

    document.querySelectorAll('[data-mode]').forEach((button) => {
      button.addEventListener('click', () => {
        currentMode = button.dataset.mode;
        document.querySelectorAll('[data-mode]').forEach((node) => node.classList.remove('active'));
        button.classList.add('active');
        draw(currentMode);
      });
    });

    draw(currentMode);
  </script>
</body>
</html>
"""

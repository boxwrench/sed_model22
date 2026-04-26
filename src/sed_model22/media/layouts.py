from __future__ import annotations

from .manifest import VisualScene


def build_comparison_html(*, scene: VisualScene) -> str:
    case_cards = "".join(
        f"""
      <section class="case-card">
        <div class="case-head">
          <div>
            <p class="eyebrow">Case</p>
            <h2>{case.label}</h2>
          </div>
          <p class="model-form">{case.model_form}</p>
        </div>
        <img src="{case.still_filename}" alt="{case.label}">
        <dl class="metric-grid">
          {_metric_items(case.highlighted_metrics)}
        </dl>
      </section>
"""
        for case in scene.cases[:2]
    )
    focus_html = "".join(f"<li>{line}</li>" for line in scene.executive_summary)
    comparison_html = "".join(f"<li>{line}</li>" for line in scene.comparison_lines)
    warning_html = "".join(f"<li>{line}</li>" for line in scene.warning_lines)
    narrative_html = f"<p class=\"narrative\">{scene.narrative}</p>" if scene.narrative else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{scene.title}</title>
  <style>
    :root {{
      --bg: #f3efe7;
      --paper: #fcfaf5;
      --panel: rgba(255, 255, 255, 0.82);
      --ink: #15212b;
      --muted: #566674;
      --line: rgba(21, 33, 43, 0.12);
      --accent: #b5532f;
      --accent-soft: #f2d6c8;
      --teal: #0f766e;
      --warn: #a0431c;
      --shadow: 0 24px 60px rgba(21, 33, 43, 0.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at top left, rgba(181, 83, 47, 0.12), transparent 28%),
        radial-gradient(circle at top right, rgba(15, 118, 110, 0.12), transparent 24%),
        linear-gradient(180deg, #f7f2eb 0%, var(--bg) 52%, #ece7dd 100%);
      color: var(--ink);
      font-family: "Aptos", "Trebuchet MS", sans-serif;
    }}
    .wrap {{
      max-width: 1560px;
      margin: 0 auto;
      padding: 28px 28px 40px;
    }}
    .hero {{
      background: linear-gradient(135deg, rgba(252, 250, 245, 0.94), rgba(255, 255, 255, 0.74));
      border: 1px solid var(--line);
      border-radius: 28px;
      box-shadow: var(--shadow);
      overflow: hidden;
      margin-bottom: 22px;
    }}
    .hero-grid {{
      display: grid;
      grid-template-columns: 1.3fr 0.9fr;
      gap: 22px;
      padding: 26px;
    }}
    .eyebrow {{
      margin: 0 0 10px;
      color: var(--accent);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.16em;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 0 0 10px;
      font-family: "Georgia", "Palatino Linotype", serif;
      font-size: 42px;
      line-height: 1.05;
    }}
    .subtitle {{
      margin: 0;
      max-width: 54rem;
      font-size: 17px;
      color: var(--muted);
      line-height: 1.55;
    }}
    .narrative {{
      margin: 18px 0 0;
      color: var(--ink);
      line-height: 1.6;
      font-size: 16px;
    }}
    .hero-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 22px;
      padding: 18px 18px 16px;
    }}
    .hero-card h2, .section-card h2, .case-card h2 {{
      margin: 0;
      font-size: 22px;
    }}
    .badge {{
      display: inline-block;
      margin-right: 8px;
      margin-bottom: 8px;
      padding: 7px 11px;
      background: var(--accent-soft);
      color: var(--accent);
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }}
    .case-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 22px;
    }}
    .case-card, .section-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 24px;
      padding: 18px;
      box-shadow: var(--shadow);
    }}
    .case-head {{
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: baseline;
      margin-bottom: 12px;
    }}
    .case-head h2 {{
      font-size: 28px;
      text-transform: capitalize;
    }}
    .model-form {{
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      text-align: right;
    }}
    img {{
      width: 100%;
      height: auto;
      display: block;
      border-radius: 16px;
      background: #fff;
      border: 1px solid rgba(21, 33, 43, 0.08);
    }}
    .metric-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px 16px;
      margin: 16px 0 0;
    }}
    dt {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    dd {{
      margin: 4px 0 0;
      font-size: 18px;
      font-weight: 700;
    }}
    .notes-grid {{
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 18px;
      margin-top: 22px;
    }}
    ul {{
      margin: 10px 0 0 18px;
      padding: 0;
    }}
    li {{
      margin: 8px 0;
      color: var(--muted);
      line-height: 1.45;
    }}
    .takeaways li {{
      color: var(--ink);
    }}
    .warnings li {{
      color: var(--warn);
    }}
    .comparison li strong {{
      color: var(--teal);
    }}
    .footnote {{
      margin: 16px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }}
    @media (max-width: 1100px) {{
      .hero-grid, .case-grid, .notes-grid, .metric-grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="hero-grid">
        <div>
          <p class="eyebrow">Leadership Review Artifact</p>
          <h1>{scene.title}</h1>
          <p class="subtitle">{scene.subtitle}</p>
          {narrative_html}
        </div>
        <div class="hero-card">
          <p class="eyebrow">Executive Takeaways</p>
          {"".join(f'<span class="badge">{point}</span>' for point in scene.focus_points[:4])}
          <ul class="takeaways">{focus_html}</ul>
        </div>
      </div>
    </section>
    <div class="case-grid">
      {case_cards}
    </div>
    <div class="notes-grid">
      <section class="section-card comparison">
        <p class="eyebrow">Comparison Notes</p>
        <h2>Directional Differences</h2>
        <ul>{comparison_html}</ul>
        <p class="footnote">Use these comparisons to discuss what changed hydraulically, not to imply a full 3D or field-calibrated prediction.</p>
      </section>
      <section class="section-card warnings">
        <p class="eyebrow">Model Boundaries</p>
        <h2>Screening Warnings</h2>
        <ul>{warning_html}</ul>
      </section>
    </div>
  </div>
</body>
</html>
"""


def _metric_items(metrics: dict[str, object]) -> str:
    labels = {
        "run_quality_tier": "Run Quality",
        "flow_rate_m3_s": "Flow",
        "transition_headloss_m": "Headloss",
        "post_transition_velocity_uniformity_index": "Post-Transition VUI",
        "plate_inlet_mean_velocity_m_s": "Plate Inlet Mean",
        "launder_peak_upward_velocity_m_s": "Launder Peak Up",
        "dead_zone_fraction": "Dead Zone Fraction",
        "t10_s": "t10",
        "t50_s": "t50",
        "t90_s": "t90",
        "morrill_index": "Morrill Index",
        "solver_mass_balance_error": "Mass Balance Error",
    }
    rows: list[str] = []
    for key, label in labels.items():
        value = metrics.get(key)
        if value is None:
            continue
        rows.append(f"<div><dt>{label}</dt><dd>{_format_metric_value(key, value)}</dd></div>")
        if len(rows) >= 6:
            break
    return "".join(rows)


def _format_metric_value(key: str, value: object) -> str:
    if not isinstance(value, (int, float)):
        return str(value)
    if key.endswith("_m3_s") or key.endswith("_m_s"):
        return f"{value:.4g}"
    if key.endswith("_fraction") or key.endswith("_index"):
        return f"{value:.4f}"
    if key.endswith("_s"):
        return f"{value:.0f} s"
    if key.endswith("_m"):
        return f"{value:.4f} m"
    return f"{value:.4g}"

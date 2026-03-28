from __future__ import annotations


def build_comparison_html(
    *,
    title: str,
    subtitle: str,
    left_label: str,
    left_filename: str,
    right_label: str,
    right_filename: str,
    comparison_lines: list[str],
    warning_lines: list[str],
) -> str:
    comparison_html = "".join(f"<li>{line}</li>" for line in comparison_lines)
    warning_html = "".join(f"<li>{line}</li>" for line in warning_lines)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    :root {{
      --bg: #f4f8fb;
      --card: #ffffff;
      --ink: #0f172a;
      --muted: #475569;
      --line: #d7e2ee;
      --accent: #d26a3b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: linear-gradient(180deg, #eff6ff 0%, var(--bg) 55%, #eef2f7 100%);
      color: var(--ink);
      font-family: Consolas, "SFMono-Regular", monospace;
    }}
    .wrap {{
      max-width: 1760px;
      margin: 0 auto;
      padding: 28px;
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 32px;
    }}
    .subtitle {{
      margin: 0 0 22px;
      font-size: 16px;
      color: var(--muted);
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 22px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
      box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
    }}
    .label {{
      margin: 0 0 10px;
      font-size: 18px;
      font-weight: 700;
    }}
    img {{
      width: 100%;
      height: auto;
      display: block;
      border-radius: 12px;
      background: #fff;
    }}
    .notes {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
      margin-top: 18px;
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
    .warnings li {{
      color: #9a3412;
    }}
    @media (max-width: 1100px) {{
      .grid, .notes {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>{title}</h1>
    <p class="subtitle">{subtitle}</p>
    <div class="grid">
      <section class="card">
        <h2 class="label">{left_label}</h2>
        <img src="{left_filename}" alt="{left_label}">
      </section>
      <section class="card">
        <h2 class="label">{right_label}</h2>
        <img src="{right_filename}" alt="{right_label}">
      </section>
    </div>
    <div class="notes">
      <section class="card">
        <h2 class="label">Comparison Notes</h2>
        <ul>{comparison_html}</ul>
      </section>
      <section class="card warnings">
        <h2 class="label">Screening Warnings</h2>
        <ul>{warning_html}</ul>
      </section>
    </div>
  </div>
</body>
</html>
"""

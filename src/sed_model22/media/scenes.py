from __future__ import annotations

from pathlib import Path


def write_title_card(
    output_path: str | Path,
    *,
    title: str,
    subtitle: str,
    template_id: str,
) -> Path:
    body = _card_svg(
        title=title,
        subtitle=subtitle,
        eyebrow=f"Template: {template_id}",
        lines=[
            "Preview-first basin media output",
            "Generated from code-rendered stills and fixed scene templates",
        ],
    )
    return _write_text(output_path, body)


def write_metrics_card(
    output_path: str | Path,
    *,
    title: str,
    lines: list[str],
) -> Path:
    body = _card_svg(
        title=title,
        subtitle="Key comparison readout",
        eyebrow="Metric Summary",
        lines=lines,
    )
    return _write_text(output_path, body)


def write_warnings_card(
    output_path: str | Path,
    *,
    title: str,
    lines: list[str],
) -> Path:
    body = _card_svg(
        title=title,
        subtitle="Read these outputs as screening media, not as a fidelity upgrade",
        eyebrow="Warnings",
        lines=lines,
        accent="#d26a3b",
    )
    return _write_text(output_path, body)


def _card_svg(
    *,
    title: str,
    subtitle: str,
    eyebrow: str,
    lines: list[str],
    accent: str = "#4e99d3",
) -> str:
    wrapped = []
    for line in lines[:8]:
        wrapped.append(line)
    line_elements = []
    for index, line in enumerate(wrapped):
        y = 258 + index * 42
        line_elements.append(
            f"  <text x='84' y='{y}' font-family='Consolas, monospace' font-size='24' fill='#334155'>{line}</text>"
        )
    return "\n".join(
        [
            "<svg xmlns='http://www.w3.org/2000/svg' width='1280' height='720' viewBox='0 0 1280 720'>",
            "  <rect width='100%' height='100%' fill='#f4f8fb' />",
            "  <defs>",
            "    <linearGradient id='bg' x1='0' x2='0' y1='0' y2='1'>",
            "      <stop offset='0%' stop-color='#eff6ff' />",
            "      <stop offset='100%' stop-color='#eef2f7' />",
            "    </linearGradient>",
            "  </defs>",
            "  <rect x='44' y='42' width='1192' height='636' rx='26' fill='url(#bg)' stroke='#d7e2ee' stroke-width='2' />",
            f"  <rect x='84' y='86' width='220' height='28' rx='14' fill='{accent}' fill-opacity='0.14' />",
            f"  <text x='98' y='105' font-family='Consolas, monospace' font-size='14' font-weight='700' fill='{accent}'>{eyebrow}</text>",
            f"  <text x='84' y='164' font-family='Consolas, monospace' font-size='36' font-weight='700' fill='#0f172a'>{title}</text>",
            f"  <text x='84' y='204' font-family='Consolas, monospace' font-size='18' fill='#475569'>{subtitle}</text>",
            *line_elements,
            "  <text x='84' y='648' font-family='Consolas, monospace' font-size='16' fill='#64748b'>sed_model22 preview media pipeline | screening output</text>",
            "</svg>",
        ]
    )


def _write_text(path: str | Path, body: str) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(body, encoding="utf-8")
    return destination

"""Graphiques du vault : une fiche par actif + vue d'ensemble du positionnement Apex."""
import json, sys, os
import datetime as dt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

for f in fm.findSystemFonts():
    if "Inter" in f:
        fm.fontManager.addfont(f)
plt.rcParams.update({
    "font.family": "Inter", "font.size": 10,
    "axes.edgecolor": "#c3c2b7", "axes.linewidth": 0.8,
    "xtick.color": "#52514e", "ytick.color": "#52514e",
    "axes.labelcolor": "#52514e", "text.color": "#0b0b0b",
})
SURF = "#fcfcfb"; INK = "#0b0b0b"; INK2 = "#52514e"; MUTED = "#8a8984"; GRID = "#e6e5e0"
APEX = "#2a78d6"; SHARPS = "#eb6834"; OIBAR = "#c9c8c1"
MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]

def fdate(s):
    d = dt.date.fromisoformat(s); return f"{d.day} {MOIS[d.month-1]}"

def style(ax):
    ax.set_facecolor(SURF)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=0.8); ax.set_axisbelow(True)
    ax.tick_params(length=0)

def asset_chart(ticker, name, rows, out):
    """rows: list of dicts date, cours, oi_usd, apex_biais, sharps_biais (None if absent)."""
    dates = [r["date"] for r in rows]; x = list(range(len(dates)))
    fig, axes = plt.subplots(3, 1, figsize=(8, 7.2), sharex=True,
                             gridspec_kw={"height_ratios": [2.2, 1.1, 1.8], "hspace": 0.42})
    fig.patch.set_facecolor(SURF)
    fig.suptitle(f"{name} ({ticker}) — contrat Hyperliquid", x=0.07, y=0.975, ha="left",
                 fontsize=14, fontweight="semibold", color=INK)
    fig.text(0.07, 0.932, f"Du {fdate(dates[0])} au {fdate(dates[-1])} {dates[-1][:4]} · source : Coinversa Pulse",
             ha="left", va="top", fontsize=9.5, color=INK2)

    ax = axes[0]; style(ax)
    px = [r["cours"] for r in rows]
    ax.plot(x, px, color=INK2, linewidth=2, marker="o" if len(x) < 20 else None, markersize=4.5, markerfacecolor=INK2)
    ax.set_title("Cours du contrat (USD)", loc="left", fontsize=10.5, color=INK, pad=6)
    ax.annotate(f"{px[-1]:,.2f}".replace(",", " "), (x[-1], px[-1]), xytext=(6, 0),
                textcoords="offset points", va="center", fontsize=9.5, color=INK)
    pad = (max(px) - min(px)) * 0.25 or px[-1] * 0.01
    ax.set_ylim(min(px) - pad, max(px) + pad)

    ax = axes[1]; style(ax)
    oi = [r["oi_usd"] / 1e6 for r in rows]
    ax.bar(x, oi, color=OIBAR, width=0.62)
    ax.set_title("Open interest (millions USD)", loc="left", fontsize=10.5, color=INK, pad=6)
    ax.annotate(f"{oi[-1]:,.1f}".replace(",", " "), (x[-1], oi[-1]), xytext=(0, 3),
                textcoords="offset points", ha="center", va="bottom", fontsize=9, color=INK)
    ax.set_ylim(0, max(oi) * 1.25)

    ax = axes[2]; style(ax)
    ax.axhline(0, color=MUTED, linewidth=1)
    ax.set_ylim(-110, 110); ax.set_yticks([-100, -50, 0, 50, 100])
    ax.set_title("Biais net des traders les plus rentables (−100 vendeurs · +100 acheteurs)",
                 loc="left", fontsize=10.5, color=INK, pad=6)
    gaps = False
    for key, col, lab in (("apex_biais", APEX, "Apex"), ("sharps_biais", SHARPS, "Sharps")):
        pts = [(i, r[key]) for i, r in enumerate(rows) if r.get(key) is not None]
        if not pts: continue
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            dashed = x1 - x0 > 1; gaps = gaps or dashed
            ax.plot([x0, x1], [y0, y1], color=col, linewidth=2, linestyle=(0, (4, 3)) if dashed else "-")
        xs, ys = zip(*pts)
        ax.scatter(xs, ys, s=64 if len(xs) < 20 else 18, color=col, edgecolor=SURF, linewidth=2 if len(xs) < 20 else 0.5,
                   zorder=3, label=lab)
        ax.annotate(f"{lab} {ys[-1]:+.0f}".replace("-", "−"), (xs[-1], ys[-1]), xytext=(8, 0), textcoords="offset points",
                    va="center", fontsize=9.5, color=INK)
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.18), ncol=2, frameon=False, fontsize=9.5)
    step = max(1, -(-len(x) // 8))
    ticks = list(range(len(x) - 1, -1, -step))[::-1]
    ax.set_xticks(ticks); ax.set_xticklabels([fdate(dates[i]) for i in ticks])
    ax.set_xlim(-0.4, len(x) - 0.4 + 0.9)
    if gaps:
        fig.text(0.07, 0.012, "Pointillés : jours sans relevé de positionnement entre deux points.",
                 fontsize=8.5, color=MUTED, ha="left")
    fig.subplots_adjust(left=0.07, right=0.93, top=0.85, bottom=0.11)
    fig.savefig(out, dpi=130, facecolor=SURF); plt.close(fig)

def overview_chart(items, date_now, date_then, out):
    """items: list of (label, before, now, weak) sorted for display (top = first)."""
    n = len(items)
    fig, ax = plt.subplots(figsize=(8, 0.42 * n + 1.9)); fig.patch.set_facecolor(SURF); style(ax)
    ax.grid(axis="y", visible=False); ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.axvline(0, color=MUTED, linewidth=1)
    for i, (lab, b, a, weak) in enumerate(items):
        y = n - 1 - i
        ax.plot([b, a], [y, y], color="#d6d5cf", linewidth=2.2, zorder=1)
        ax.scatter([b], [y], s=58, color="#a9a8a1", edgecolor=SURF, linewidth=2, zorder=2)
        ax.scatter([a], [y], s=70, color=APEX if not weak else SURF, edgecolor=APEX,
                   linewidth=2 if weak else 2, zorder=3)
    ax.set_yticks(range(n)); ax.set_yticklabels([it[0] for it in reversed(items)], fontsize=9.5, color=INK)
    ax.set_xlim(-108, 108); ax.set_xticks([-100, -50, 0, 50, 100])
    ax.set_xticklabels(["−100\nvendeurs", "−50", "0", "+50", "+100\nacheteurs"], fontsize=9)
    ax.set_ylim(-0.7, n - 0.3)
    fig.suptitle("Biais net des traders Apex, par contrat", x=0.03, y=0.985, ha="left",
                 fontsize=14, fontweight="semibold", color=INK)
    fig.text(0.03, 0.985 - 0.36 / (0.42 * n + 1.9), f"Point gris : {date_then} · point bleu : {date_now} · cercle vide : moins de 5 M$ engagés (échantillon faible)",
             fontsize=9, color=INK2, ha="left", va="top")
    fig.subplots_adjust(left=0.2, right=0.97, top=1 - 0.95 / (0.42 * n + 1.9), bottom=0.62 / (0.42 * n + 1.9) + 0.04)
    fig.savefig(out, dpi=130, facecolor=SURF); plt.close(fig)

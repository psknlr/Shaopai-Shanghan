#!/usr/bin/env python3
"""
Nature Portfolio / Scientific Data house style for matplotlib, and the checks that go with it.

- Physical size is set in millimetres and never changed at save time (no tight bbox).
- Arial 5–7 pt, panel labels 8 pt bold lowercase; strokes 0.25–1 pt; white background, no grid.
- Colour: Okabe–Ito (colour-blind safe); hues only where they carry a variable.
- Text stays live in vector output (TrueType, fonttype 42); dense layers are rasterised at 800 dpi.
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.text import Text
from matplotlib.lines import Line2D
from PIL import Image

MM = 1 / 25.4
DPI = 800
DOUBLE, ONE_HALF, SINGLE = 183.0, 120.0, 89.0
MAX_H = 170.0

# Okabe–Ito
BLACK, ORANGE, SKY, GREEN, YELLOW, BLUE, VERMILLION, PURPLE, GREY = (
    '#000000', '#E69F00', '#56B4E9', '#009E73', '#F0E442', '#0072B2', '#D55E00', '#CC79A7', '#999999')
INK = '#1A1A1A'          # near-black for marks that should recede slightly behind text
DARK = '#4D4D4D'         # neutral single-series fill
LIGHT = '#C8C8C8'        # neutral secondary fill

_CJK = [f.name for f in fm.fontManager.ttflist
        if f.name in ('Noto Sans CJK SC', 'Source Han Sans SC', 'WenQuanYi Zen Hei', 'Noto Sans SC')]
CJK_FONT = _CJK[0] if _CJK else None


def apply():
    fams = ['Arial'] + ([CJK_FONT] if CJK_FONT else [])
    plt.rcParams.update({
        'font.family': fams, 'font.size': 6,
        'axes.labelsize': 6, 'axes.titlesize': 6.5, 'axes.titleweight': 'normal',
        'xtick.labelsize': 5.5, 'ytick.labelsize': 5.5, 'legend.fontsize': 5.5, 'legend.title_fontsize': 5.5,
        'axes.linewidth': 0.5, 'axes.edgecolor': BLACK, 'axes.labelcolor': BLACK,
        'xtick.color': BLACK, 'ytick.color': BLACK,
        'xtick.major.width': 0.5, 'ytick.major.width': 0.5, 'xtick.minor.width': 0.4, 'ytick.minor.width': 0.4,
        'xtick.major.size': 2.0, 'ytick.major.size': 2.0, 'xtick.minor.size': 1.2, 'ytick.minor.size': 1.2,
        'xtick.major.pad': 1.5, 'ytick.major.pad': 1.5,
        'xtick.direction': 'out', 'ytick.direction': 'out',
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': False,
        'axes.labelpad': 2.0, 'axes.titlepad': 3.0, 'axes.unicode_minus': True,
        'lines.linewidth': 1.0, 'lines.markersize': 3, 'patch.linewidth': 0.5,
        'legend.frameon': False, 'legend.handlelength': 1.2, 'legend.handletextpad': 0.4,
        'legend.borderaxespad': 0.2, 'legend.labelspacing': 0.3,
        'figure.facecolor': 'white', 'axes.facecolor': 'white', 'savefig.facecolor': 'white',
        'pdf.fonttype': 42, 'ps.fonttype': 42, 'svg.fonttype': 'none',
        'mathtext.fontset': 'custom', 'mathtext.rm': 'Arial', 'mathtext.it': 'Arial:italic',
        'mathtext.bf': 'Arial:bold', 'mathtext.default': 'regular',
        'savefig.bbox': 'standard', 'savefig.pad_inches': 0, 'figure.dpi': 100,
    })


class Canvas:
    """A figure laid out in millimetres from the top-left corner."""

    def __init__(self, w_mm, h_mm):
        assert h_mm <= MAX_H + 1e-6, f'height {h_mm} mm exceeds {MAX_H} mm'
        self.w, self.h = w_mm, h_mm
        self.fig = plt.figure(figsize=(w_mm * MM, h_mm * MM))

    def ax(self, x, y, w, h, **kw):
        return self.fig.add_axes([x / self.w, 1 - (y + h) / self.h, w / self.w, h / self.h], **kw)

    def label(self, x, y, s):
        """Panel label: 8 pt bold lowercase, placed by its top-left corner."""
        self.fig.text(x / self.w, 1 - y / self.h, s, fontsize=8, fontweight='bold',
                      ha='left', va='top', fontfamily='Arial')

    def text(self, x, y, s, **kw):
        kw.setdefault('fontsize', 6)
        return self.fig.text(x / self.w, 1 - y / self.h, s, **kw)


def check(fig, allow_label=8.0):
    """Report text outside 5–7 pt (panel labels excepted) and visible strokes under 0.25 pt."""
    issues = []
    for t in fig.findobj(Text):
        if not t.get_visible() or not t.get_text().strip():
            continue
        s = t.get_fontsize()
        if abs(s - allow_label) < 1e-6 and t.get_fontweight() in ('bold', 700):
            continue
        if s < 5 - 1e-6 or s > 7 + 1e-6:
            issues.append(f'text {s:.2f} pt: {t.get_text()[:30]!r}')
    for ln in fig.findobj(Line2D):
        if ln.get_visible() and ln.get_linestyle() not in ('None', '') and 0 < ln.get_linewidth() < 0.25:
            issues.append(f'line {ln.get_linewidth():.2f} pt')
    return issues


def save(canvas, name, outdir):
    """PDF (vector, live text; rasterised layers at 800 dpi) + PNG + LZW TIFF at 800 dpi.
    Returns the measured physical size and any style issues."""
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    fig = canvas.fig
    fig.savefig(outdir / f'{name}.pdf', dpi=DPI)
    fig.savefig(outdir / f'{name}.png', dpi=DPI)
    # Nature asks for RGB: flatten matplotlib's RGBA onto the white background, keep 800 dpi metadata
    with Image.open(outdir / f'{name}.png') as im:
        rgb = Image.new('RGB', im.size, (255, 255, 255))
        rgb.paste(im, mask=im.getchannel('A') if im.mode == 'RGBA' else None)
    rgb.save(outdir / f'{name}.png', dpi=(DPI, DPI), optimize=True)
    rgb.save(outdir / f'{name}.tif', dpi=(DPI, DPI), compression='tiff_lzw')
    wpx, hpx = rgb.size
    size = (wpx / DPI * 25.4, hpx / DPI * 25.4)
    issues = check(fig)
    if abs(size[0] - canvas.w) > 0.2 or abs(size[1] - canvas.h) > 0.2:
        issues.append(f'physical size {size[0]:.1f}×{size[1]:.1f} mm differs from {canvas.w}×{canvas.h} mm')
    plt.close(fig)
    return {'name': name, 'mm': tuple(round(v, 1) for v in size), 'px': (wpx, hpx), 'issues': issues}

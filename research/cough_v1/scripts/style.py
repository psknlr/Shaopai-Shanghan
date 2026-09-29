"""中文期刊作图样式：中文思源宋体（Noto Serif SC），数字与西文 Liberation Serif（Times New Roman 等宽替代）。

尺寸按中文期刊版心：通栏 17 cm，半栏 8 cm。正文字号 7.5 pt（六号），轴标题 8 pt，分图标号 9 pt 粗体。
配色取经校验的默认分类色板（validate_palette.js：白底相邻 CVD ΔE≥9.1，前三色两两 ΔE≥9.2）。
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from PIL import Image

CM = 1 / 2.54
FULL_W = 17 * CM
HALF_W = 8 * CM

INK = '#0b0b0b'
INK2 = '#52514e'
MUTED = '#898781'
GRID = '#e1e0d9'
AXIS = '#c3c2b7'
DEEMPH = '#b9b8b1'            # 强调式作图中的「其余」灰
SERIES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948']
ACCENT = SERIES[0]
BLUE_RAMP = ['#f3f8fe', '#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b']
RED_ARM = ['#fbe3e2', '#f3aeac', '#e87574', '#e34948', '#b52f2f']
NEUTRAL_MID = '#f0efec'

FONT_FAMILY = ['Liberation Serif', 'Noto Serif SC']


def setup():
    for f in fm.findSystemFonts(fontpaths=[str(Path.home() / '.fonts')]):
        try:
            fm.fontManager.addfont(f)
        except Exception:
            pass
    plt.rcParams.update({
        'font.family': FONT_FAMILY,
        'font.size': 7.5,
        'axes.titlesize': 8,
        'axes.labelsize': 8,
        'xtick.labelsize': 7.5,
        'ytick.labelsize': 7.5,
        'legend.fontsize': 7.5,
        'axes.edgecolor': AXIS,
        'axes.linewidth': 0.6,
        'axes.labelcolor': INK,
        'xtick.color': INK2,
        'ytick.color': INK2,
        'xtick.major.width': 0.6,
        'ytick.major.width': 0.6,
        'xtick.major.size': 2.5,
        'ytick.major.size': 2.5,
        'text.color': INK,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': False,
        'grid.color': GRID,
        'grid.linewidth': 0.5,
        'pdf.fonttype': 42,
        'ps.fonttype': 42,
        'svg.fonttype': 'none',
        'axes.unicode_minus': False,
        'figure.dpi': 150,
        'savefig.dpi': 600,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.04,
        'legend.frameon': False,
    })


def panel(ax, letter, x=-0.02, y=1.02):
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=9, fontweight='bold', va='bottom', ha='right',
            family=['Liberation Serif'])


def save(fig, out_dir, name):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f'{name}.pdf')
    png = out_dir / f'{name}.png'
    fig.savefig(png, dpi=600)
    im = Image.open(png).convert('RGB')
    im.save(out_dir / f'{name}.tif', compression='tiff_lzw', dpi=(600, 600))
    im.save(png, dpi=(600, 600), optimize=True)
    plt.close(fig)

#!/usr/bin/env node
/*
 * 绍派伤寒辨治咳嗽用药规律 · Word 版图表（中文期刊三线表）。
 *   python3 scripts/make_tables.py && node scripts/make_docx.js
 * 需要 docx 包（npm install --no-save docx@9，或以 NODE_PATH 指向已安装处）。
 * 输出：
 *   tables/cough_v1_tables.docx        七张三线表（可编辑），每表一页
 *   cough_v1_figures_tables.docx       图（300 dpi 缩样，图题在下）与表（表题在上）合编本
 * 版式：A4 纵向，上下 25 mm、左右 20 mm（版心 170 mm，与表格列宽之和一致）；
 * 中文宋体、西文 Times New Roman；表内小五号（9 pt），表题五号加粗；三线：顶线、底线 1.5 pt，栏目线 0.75 pt。
 */
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, BorderStyle, ImageRun,
  AlignmentType, VerticalAlign, TableLayoutType, PageOrientation, LineRuleType, PageBreak, Footer, PageNumber,
} = require('docx');

const ROOT = path.join(__dirname, '..');
const tables = JSON.parse(fs.readFileSync(path.join(ROOT, 'tables/tables.json'), 'utf8'));
const legends = JSON.parse(fs.readFileSync(path.join(ROOT, 'figures/legends.json'), 'utf8'));
const MM = 56.6929;                                     // DXA / mm
const FONT = { ascii: 'Times New Roman', hAnsi: 'Times New Roman', cs: 'Times New Roman', eastAsia: '宋体' };
const HEI = { ascii: 'Times New Roman', hAnsi: 'Times New Roman', cs: 'Times New Roman', eastAsia: '黑体' };
const PT = (p) => Math.round(p * 2);                     // half-points
const NONE = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const RULE = (pt) => ({ style: BorderStyle.SINGLE, size: Math.round(pt * 8), color: '000000' });
const ALIGN = { l: AlignmentType.LEFT, c: AlignmentType.CENTER, r: AlignmentType.RIGHT, j: AlignmentType.JUSTIFIED };

/** 文本 → TextRun 列表；{sup:x} 转为上标。 */
function runs(text, o = {}) {
  const out = [];
  String(text).split(/(\{sup:[^}]+\})/).forEach((seg) => {
    if (!seg) return;
    const m = seg.match(/^\{sup:([^}]+)\}$/);
    out.push(new TextRun({
      text: m ? m[1] : seg, font: o.font || FONT, size: PT(o.size || 9), bold: !!o.b, italics: !!o.i,
      superScript: !!m,
    }));
  });
  return out;
}

function para(text, o = {}) {
  return new Paragraph({
    children: runs(text, o),
    alignment: ALIGN[o.align || 'l'],
    spacing: { before: o.before || 0, after: o.after || 0, line: o.line || 260, lineRule: LineRuleType.EXACT },
    indent: o.indent ? { firstLine: o.indent } : undefined,
    keepNext: !!o.keepNext, keepLines: true,
  });
}

function cell(text, width, o = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    columnSpan: o.span || 1,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 30, bottom: 30, left: 40, right: 40 },
    borders: { top: o.top || NONE, bottom: o.bottom || NONE, left: NONE, right: NONE },
    children: (Array.isArray(text) ? text : [text]).map((t) => para(t, { align: o.align, b: o.b, size: 9, line: 250 })),
  });
}

function buildTable(t) {
  const widths = t.columns.map((c) => Math.round(c.mm * MM));
  const total = widths.reduce((a, b) => a + b, 0);
  const header = new TableRow({
    tableHeader: true, cantSplit: true,
    children: t.columns.map((c, j) => cell(c.h, widths[j], {
      b: true, align: c.align === 'l' ? 'l' : 'c', top: RULE(1.5), bottom: RULE(0.75),
    })),
  });
  const body = t.rows.map((r, i) => {
    const bottom = i === t.rows.length - 1 ? RULE(1.5) : undefined;
    if (!Array.isArray(r)) {
      return new TableRow({ cantSplit: true, children: [cell(r.group, total, { span: t.columns.length, b: true, bottom })] });
    }
    return new TableRow({ cantSplit: true, children: r.map((c, j) => cell(c, widths[j], { align: t.columns[j].align, bottom })) });
  });
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths, layout: TableLayoutType.FIXED,
    alignment: AlignmentType.CENTER,
    borders: { top: NONE, bottom: NONE, left: NONE, right: NONE, insideHorizontal: NONE, insideVertical: NONE },
    rows: [header, ...body],
  });
}

function tableBlock(t, first) {
  const out = [
    new Paragraph({
      pageBreakBefore: !first, keepNext: true, alignment: AlignmentType.CENTER,
      spacing: { after: 0, line: 300, lineRule: LineRuleType.EXACT },
      children: runs(`表${t.id}　${t.title}`, { b: true, size: 10.5, font: HEI }),
    }),
    new Paragraph({
      keepNext: true, alignment: AlignmentType.CENTER, spacing: { after: 100, line: 260, lineRule: LineRuleType.EXACT },
      children: runs(`Table ${t.id}　${t.title_en}`, { b: true, size: 9 }),
    }),
    buildTable(t),
  ];
  t.notes.forEach((n, i) => out.push(para(n, { size: 8, line: 220, before: i === 0 ? 80 : 0, align: 'j' })));
  return out;
}

function figureBlock(g, k, first) {
  const file = path.join(ROOT, '.build/fig300', `${g.file}.png`);
  const buf = fs.readFileSync(file);
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);   // PNG IHDR
  const widthPx = Math.round((170 / 25.4) * 96);              // 版心 170 mm
  return [
    new Paragraph({
      pageBreakBefore: !first, alignment: AlignmentType.CENTER, keepNext: true, spacing: { after: 120 },
      children: [new ImageRun({ type: 'png', data: buf, transformation: { width: widthPx, height: Math.round(widthPx * h / w) },
        altText: { title: `图${k}`, description: g.title, name: g.file } })],
    }),
    new Paragraph({
      keepNext: true, alignment: AlignmentType.CENTER, spacing: { after: 0, line: 300, lineRule: LineRuleType.EXACT },
      children: runs(`图${k}　${g.title}`, { b: true, size: 10.5, font: HEI }),
    }),
    new Paragraph({
      keepNext: true, alignment: AlignmentType.CENTER, spacing: { after: 80, line: 260, lineRule: LineRuleType.EXACT },
      children: runs(`Fig. ${k}　${g.title_en}`, { b: true, size: 9 }),
    }),
    para(`注：${g.note}`, { size: 9, line: 260, align: 'j' }),
  ];
}

function pageProps() {
  return {
    page: {
      size: { width: 11906, height: 16838, orientation: PageOrientation.PORTRAIT },
      margin: { top: Math.round(25 * MM), bottom: Math.round(25 * MM), left: Math.round(20 * MM), right: Math.round(20 * MM) },
    },
  };
}

const footer = new Footer({
  children: [new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: PT(9) })] })],
});

function write(file, children, title) {
  const doc = new Document({
    creator: '越医·绍派伤寒数智传承智能体', title,
    styles: { default: { document: { run: { font: FONT, size: PT(9) } } } },
    sections: [{ properties: pageProps(), footers: { default: footer }, children }],
  });
  return Packer.toBuffer(doc).then((buf) => {
    fs.writeFileSync(file, buf);
    console.log('wrote', path.relative(ROOT, file), (buf.length / 1024).toFixed(0), 'KB');
  });
}

// ---------------------------------------------------------------- 表格单行本
const tChildren = [];
tables.forEach((t, k) => tChildren.push(...tableBlock(t, k === 0)));

// ---------------------------------------------------------------- 图表合编本
const TITLE = '绍派伤寒辨治咳嗽用药规律研究';
const SUB = '——基于越医·绍派伤寒数智传承智能体 V1 两书版知识图谱';
const cover = [
  para('', { line: 1800 }),
  para(TITLE, { size: 18, b: true, font: HEI, align: 'c', line: 440 }),
  para(SUB, { size: 12, align: 'c', line: 360, after: 240 }),
  para(`论文图表：图 ${legends.length} 幅，表 ${tables.length} 张`, { size: 12, align: 'c', line: 360, after: 480 }),
  para('说明', { size: 10.5, b: true, font: HEI, line: 320, after: 60 }),
  ...[
    '1. 数据：《俞根初临证经验集要》《何廉臣医案》两书构成的 V1 知识图谱（8,226 节点，17,498 条关系）；研究对象为案名或诊断含「咳」「嗽」、且图谱中有用药关系的何廉臣医案 125 例。不含 2022–2026 年现代病案。',
    '2. 全部数字由 research/cough_v1/scripts 下脚本自图谱计算生成（analysis.py → make_figures.py → make_tables.py → make_docx.js），图与表同源。',
    '3. 本文件中的图为 300 dpi 缩样，投稿请用 figures/ 下的矢量 PDF（文字可编辑）或 600 dpi PNG/TIFF；表格为可编辑三线表，单行本见 tables/cough_v1_tables.docx。',
    '4. 药名规范、性味归经、病机与治法归类规则、聚类组合的配伍释义及方证判读均列于附表 S1–S6，待专家核对。马兜铃含马兜铃酸，现行药典已不收载，文中仅作文献用药规律描述。',
  ].map((s) => para(s, { size: 10.5, line: 360 })),
  para('', { line: 240 }),
  para('目录', { size: 10.5, b: true, font: HEI, line: 320, after: 60 }),
  ...legends.map((g, k) => para(`图${k + 1}　${g.title}`, { size: 10.5, line: 330 })),
  ...tables.map((t) => para(`表${t.id}　${t.title}`, { size: 10.5, line: 330 })),
];
const cChildren = [...cover];
legends.forEach((g, k) => cChildren.push(...figureBlock(g, k + 1, false)));
tables.forEach((t) => cChildren.push(...tableBlock(t, false)));

write(path.join(ROOT, 'tables/cough_v1_tables.docx'), tChildren, `${TITLE} · 表`)
  .then(() => write(path.join(ROOT, 'cough_v1_figures_tables.docx'), cChildren, `${TITLE} · 图表`));

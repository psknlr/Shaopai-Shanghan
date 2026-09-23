#!/usr/bin/env node
/*
 * Word version of the Data Descriptor tables (three-line style), from paper/tables/tables.json.
 *   python3 paper/make_tables.py && node paper/make_tables_docx.js
 * Needs the `docx` package (npm install docx); set NODE_PATH if it is installed elsewhere.
 * A4 portrait, 20 mm margins, Arial 7 pt (Chinese in Microsoft YaHei), one table per page;
 * rules above and below the header and at the foot only; numbers right-aligned; symbol footnotes.
 */
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, BorderStyle,
  AlignmentType, VerticalAlign, TableLayoutType, PageOrientation, LineRuleType,
} = require('docx');

const DIR = path.join(__dirname, 'tables');
const tables = JSON.parse(fs.readFileSync(path.join(DIR, 'tables.json'), 'utf8'));
const MM = 56.6929;                         // DXA per millimetre
const FONT = { ascii: 'Arial', hAnsi: 'Arial', cs: 'Arial', eastAsia: 'Microsoft YaHei' };
const BODY = 14, TITLE = 16;                // half-points: 7 pt and 8 pt
const NONE = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const RULE = (sz) => ({ style: BorderStyle.SINGLE, size: sz, color: '000000' });

const run = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size || BODY, bold: !!o.b, italics: !!o.i });
const para = (children, o = {}) => new Paragraph({
  children, alignment: o.align || AlignmentType.LEFT,
  // exact 8.5 pt leading: otherwise the CJK fallback font's tall line box doubles the row height
  spacing: { before: o.before || 0, after: o.after || 0, line: o.line || 170, lineRule: LineRuleType.EXACT },
  keepNext: !!o.keepNext,
});

function cell(content, width, o = {}) {
  const c = typeof content === 'object' && content !== null ? content : { t: String(content) };
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    columnSpan: o.span || 1,
    verticalAlign: VerticalAlign.TOP,
    margins: { top: 28, bottom: 28, left: 70, right: 70 },
    borders: { top: o.top || NONE, bottom: o.bottom || NONE, left: NONE, right: NONE },
    children: [para([run(c.t, { b: c.b || o.header, i: c.i })], { align: o.align })],
  });
}

function buildTable(t) {
  const widths = t.columns.map(([, , w]) => Math.round(w * MM));
  const total = widths.reduce((a, b) => a + b, 0);
  const align = t.columns.map(([, a]) => (a === 'r' ? AlignmentType.RIGHT : AlignmentType.LEFT));
  const header = new TableRow({
    tableHeader: true,
    children: t.columns.map(([h], j) => cell(h, widths[j], { header: true, align: align[j], top: RULE(6), bottom: RULE(4) })),
  });
  const rows = t.rows.map((r, i) => {
    const last = i === t.rows.length - 1;
    const bottom = last ? RULE(6) : undefined;
    if (r[0] && typeof r[0] === 'object' && r[0].span) {
      return new TableRow({ cantSplit: true, children: [cell(r[0], total, { span: t.columns.length, bottom })] });
    }
    return new TableRow({
      cantSplit: true,
      children: r.map((c, j) => cell(c, widths[j], { align: align[j], bottom })),
    });
  });
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths, layout: TableLayoutType.FIXED,
    borders: { top: NONE, bottom: NONE, left: NONE, right: NONE, insideHorizontal: NONE, insideVertical: NONE },
    rows: [header, ...rows],
  });
}

const children = [];
tables.forEach((t, k) => {
  children.push(new Paragraph({
    pageBreakBefore: k > 0, keepNext: true,
    spacing: { after: 120, line: 200, lineRule: LineRuleType.EXACT },
    children: [run(`Table ${t.id} | `, { b: true, size: TITLE }), run(t.title, { b: true, size: TITLE })],
  }));
  children.push(buildTable(t));
  t.foot.forEach((f, i) => children.push(para([run(f)], { before: i === 0 ? 80 : 20 })));
});

const doc = new Document({
  creator: 'Shaopai Shanghan knowledge graph', title: 'Tables — Shaopai Shanghan knowledge graph and corpus',
  styles: { default: { document: { run: { font: FONT, size: BODY } } } },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838, orientation: PageOrientation.PORTRAIT },
        margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 },
      },
    },
    children,
  }],
});
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(path.join(DIR, 'Tables.docx'), buf);
  console.log('wrote', path.join(DIR, 'Tables.docx'), buf.length, 'bytes');
});

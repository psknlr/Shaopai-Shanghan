#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
当代病案（2022—2026）的公开发布前去标识化与核验。

本模块**只含模式，不含任何真实姓名或编号**：待删的姓名在运行时从输入文本的患者抬头里
推导出来，用来核验输出中是否还有残留，从不写入仓库。

去标识化规则（redact）：
  1. 患者抬头 ——「[关系词][姓名][性别][年龄]岁[7–8 位住院号]」整段替换为「患者（女，55岁）」。
     针对的格式：多名患者的记录连排在同一段落时，后一名患者的抬头以行内形式出现，
     不在逐行抬头的位置上，按行首匹配的规则会漏掉它。关系词（姐姐 / 妹妹…）一并删除。
  2. 残留的 7–8 位数字（住院号、病历号）→「〔编号已删〕」。
  3. 日历日期只保留年份：2022年7月1日 / 2023.5.12 / 2022-04-11 / 20221017 → 2022年；
     无年份的「4月20日」→「某日」；「去年8月」→「去年」。时长（「3个月」「半年」）不动。
  4. 就诊跨度「4 visits 2022-07-01..2022-07-22」→「4 visits over 21 days (2022)」，保留病程长短；
     结构化的逐次就诊日期（visit_dates）由导入脚本换成跨度天数（span_days）。
  5. 90 岁及以上 →「90岁以上」。

核验（verify）：在输出文本上断言以上各类模式计数为 0，且运行时推导出的姓名一个都不出现。
"""
import re
import datetime

CJK = r'一-龥'

# 患者抬头：年龄后紧跟 7–8 位住院号是这一格式的锚点；性别可缺（形如「某某某54岁NNNNNNNN」）
HEADER = re.compile(
    rf'(?P<rel>姐姐|妹妹|哥哥|弟弟|患者|病人)?'
    rf'(?P<name>[{CJK}]{{1,4}}?)\s*'
    rf'(?P<sex>[男女])?\s*'
    rf'(?P<age>\d{{1,3}})\s*岁\s*'
    rf'(?P<mrn>\d{{7,8}})(?!\d)')

# 日期（顺序有意义：先长后短）
_Y = r'((?:19|20)\d{2})'
_M = r'(?:0?[1-9]|1[0-2])'
_D = r'(?:0?[1-9]|[12]\d|3[01])'
DATE_RULES = [
    # 2022年7月01日 · 2025年9年15日（原文笔误）· 2022年7月1号
    (re.compile(rf'{_Y}\s*年\s*{_M}\s*[月年]\s*{_D}\s*[日号]'), r'\1年'),
    # 2022-04-11 · 2023.5.12 · 2023/5/12
    (re.compile(rf'(?<!\d){_Y}[-/.]{_M}[-/.]{_D}(?!\d)'), r'\1年'),
    # 20221017
    (re.compile(rf'(?<!\d){_Y}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])(?!\d)'), r'\1年'),
    # 2022年7月（仅到月）——「年」字锚定，不会误伤「3个月」
    (re.compile(rf'{_Y}\s*年\s*{_M}\s*月(?!\s*\d)'), r'\1年'),
    # 4月20日（无年份）
    (re.compile(rf'(?<![年\d]){_M}\s*月\s*{_D}\s*[日号]'), '某日'),
    # 去年8月 → 去年
    (re.compile(r'(去年|今年|前年|上年)\s*\d{1,2}\s*月'), r'\1'),
]
VISIT_SPAN = re.compile(
    r'(\d+)\s*visits?\s*((?:19|20)\d{2})-(\d{1,2})-(\d{1,2})\s*\.\.\s*((?:19|20)\d{2})-(\d{1,2})-(\d{1,2})')
VISIT_EMPTY = re.compile(r'(\d+)\s*visits?\s*\.\.')
LONG_NUM = re.compile(r'(?<![\d.])\d{7,8}(?![\d.])')
AGE_90 = re.compile(r'(?<!\d)(9\d|1\d\d)\s*岁')

# 核验用：任何残留的完整日期 / 月日 / 抬头 / 编号
RESIDUAL = {
    'patient_header': HEADER,
    'full_date': re.compile(
        rf'{_Y}\s*年\s*{_M}\s*[月年]\s*{_D}\s*[日号]|(?<!\d){_Y}[-/.]{_M}[-/.]{_D}(?!\d)'
        rf'|(?<!\d){_Y}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])(?!\d)'),
    'month_day': re.compile(rf'(?<![年\d]){_M}\s*月\s*{_D}\s*[日号]'),
    'record_number': LONG_NUM,
    'national_id': re.compile(r'(?<!\d)\d{17}[\dXx](?!\d)'),
    'phone': re.compile(r'(?<!\d)1[3-9]\d{9}(?!\d)'),
    'age_90_plus': AGE_90,
}


def names_from_headers(texts):
    """从患者抬头推导姓名（仅在内存中用于核验，不落盘）。"""
    out = set()
    for t in texts:
        for m in HEADER.finditer(t or ''):
            nm = m.group('name')
            if nm and len(nm) >= 2:
                out.add(nm)
    return out


def _visit_span(m):
    n = int(m.group(1))
    try:
        a = datetime.date(int(m.group(2)), int(m.group(3)), int(m.group(4)))
        b = datetime.date(int(m.group(5)), int(m.group(6)), int(m.group(7)))
        days = (b - a).days
        return f'{n} visits over {days} days ({m.group(2)})'
    except ValueError:
        return f'{n} visits ({m.group(2)})'


def span_days(dates):
    """就诊日期列表（YYYY-MM-DD）→ 首末次相隔天数；无可解析日期时为 None。"""
    ds = []
    for x in dates or []:
        try:
            ds.append(datetime.date.fromisoformat(str(x).strip()[:10]))
        except ValueError:
            pass
    return (max(ds) - min(ds)).days if ds else None


def redact(text):
    """返回 (去标识化后的文本, 各规则命中次数)。None / 空串原样返回。"""
    if not text:
        return text, {}
    hits = {}

    def count(k, n):
        if n:
            hits[k] = hits.get(k, 0) + n

    def header_sub(m):
        sex = m.group('sex')
        age = int(m.group('age'))
        age_s = '90岁以上' if age >= 90 else f'{age}岁'
        return f'患者（{sex}，{age_s}）' if sex else f'患者（{age_s}）'

    text, n = HEADER.subn(header_sub, text); count('patient_header', n)
    text, n = VISIT_SPAN.subn(_visit_span, text); count('visit_span', n)
    text, n = VISIT_EMPTY.subn(lambda m: f'{m.group(1)} visits', text); count('visit_span', n)
    for i, (pat, rep) in enumerate(DATE_RULES):
        text, n = pat.subn(rep, text); count('date', n)
    text, n = LONG_NUM.subn('〔编号已删〕', text); count('record_number', n)
    text, n = AGE_90.subn('90岁以上', text); count('age_90_plus', n)
    return text, hits


def residuals(text, names=()):
    """输出文本上的残留计数；names 为运行时推导的姓名集合。"""
    out = {}
    if not text:
        return out
    for k, pat in RESIDUAL.items():
        n = len(pat.findall(text))
        if n:
            out[k] = n
    leaked = [nm for nm in names if nm in text]
    if leaked:
        out['derived_name'] = len(leaked)
    return out


if __name__ == '__main__':
    # 自检：只用虚构的示例
    demo = ('复投前方7剂。 / 甲乙丙 女55岁12345678 / 2023.5.5初诊 / 右膝疼痛半个月，'
            '4月20日跌倒。DR（20221017本院）。姐姐丁某戊女14岁8765432 / 2026年5月4日来诊。'
            ' note: 4 visits 2022-07-01..2022-07-22')
    out, hits = redact(demo)
    print(out)
    print(hits)
    names = names_from_headers([demo])
    print('residual:', residuals(out, names))
    assert residuals(out, names) == {}, '自检失败'
    assert span_days(['2022-07-01', '2022-07-22', 'bad']) == 21 and span_days([]) is None
    print('deidentify 自检通过')

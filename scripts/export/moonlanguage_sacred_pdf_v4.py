#!/usr/bin/env python3
"""
MOONLANGUAGE Sacred PDF v4 - COMPACT LAYOUT
No whitespace waste - continuous flow
"""

import sys
import re
from pathlib import Path
from fpdf import FPDF

PHI = 1.618033988749895
PAGE_W, PAGE_H = 210, 297
MARGIN = 15
CONTENT_W = PAGE_W - (2 * MARGIN)

ARTIST_STYLES = {
    'hildegard': {
        'name': 'Hildegard of Bingen', 'years': '1098-1179',
        'dedication': 'For Hildegard, who saw visions in light.',
        'philosophy': 'Viriditas - The Greening Power',
        'colors': {
            'bg': (250, 245, 235), 'dark': (40, 30, 25),
            'primary': (38, 97, 156), 'secondary': (74, 124, 89),
            'accent': (200, 160, 50), 'highlight': (114, 47, 55),
        }
    },
    'davinci': {
        'name': 'Leonardo da Vinci', 'years': '1452-1519',
        'dedication': 'For Leonardo, master of sfumato.',
        'philosophy': 'Observation - Mother of Certainty',
        'colors': {
            'bg': (252, 248, 240), 'dark': (50, 35, 30),
            'primary': (112, 66, 20), 'secondary': (114, 127, 75),
            'accent': (220, 180, 90), 'highlight': (118, 75, 28),
        }
    },
    'tesla': {
        'name': 'Nikola Tesla', 'years': '1856-1943',
        'dedication': 'For Tesla, who saw living flame.',
        'philosophy': 'Energy, Frequency, Vibration',
        'colors': {
            'bg': (235, 238, 248), 'dark': (12, 15, 28),
            'primary': (90, 70, 160), 'secondary': (69, 93, 156),
            'accent': (240, 200, 50), 'highlight': (156, 136, 189),
        }
    },
    'founder': {
        'name': 'The Founder', 'years': '1980-present',
        'dedication': 'For Gisel, who dances with the moon.',
        'philosophy': 'I Fell in Love with DATA',
        'colors': {
            'bg': (245, 242, 238), 'dark': (8, 8, 15),
            'primary': (200, 155, 105), 'secondary': (175, 95, 125),
            'accent': (115, 95, 175), 'highlight': (80, 155, 110),
        }
    },
    'bjork': {
        'name': 'Bjork', 'years': '1965-present',
        'dedication': 'For Bjork, boundary dissolver.',
        'philosophy': 'Acoustic Symbolism',
        'colors': {
            'bg': (248, 245, 248), 'dark': (25, 30, 35),
            'primary': (200, 165, 55), 'secondary': (125, 175, 160),
            'accent': (210, 150, 130), 'highlight': (145, 95, 115),
        }
    },
    'fuller': {
        'name': 'Buckminster Fuller', 'years': '1895-1983',
        'dedication': 'For Bucky, who did more with less.',
        'philosophy': 'Ephemeralization',
        'colors': {
            'bg': (242, 244, 248), 'dark': (20, 25, 32),
            'primary': (115, 120, 130), 'secondary': (50, 70, 90),
            'accent': (175, 145, 75), 'highlight': (135, 55, 55),
        }
    }
}


class CompactPDF(FPDF):
    def __init__(self, style_key='founder'):
        super().__init__()
        self.style = ARTIST_STYLES[style_key]
        self.set_auto_page_break(auto=True, margin=12)
        self.set_margins(MARGIN, 12, MARGIN)

    def _c(self, k): return self.style['colors'][k]

    def _clean(self, t):
        if not t: return ''
        for old, new in [('\u2014','--'),('\u2013','-'),('\u2018',"'"),('\u2019',"'"),
            ('\u201c','"'),('\u201d','"'),('\u2026','...'),('\u2550','='),('\u2551','|'),
            ('\u2500','-'),('\u2502','|'),('\u250c','+'),('\u2510','+'),('\u2514','+'),
            ('\u2518','+'),('\u2554','+'),('\u2557','+'),('\u255a','+'),('\u255d','+'),
            ('\u2191','^'),('\u2193','v'),('\u2192','>'),('\u2190','<'),('\u2022','*')]:
            t = t.replace(old, new)
        return ''.join(c if ord(c) < 256 else ' ' for c in t)

    def _space(self): return PAGE_H - 12 - self.get_y()

    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', '', 6)
            self.set_text_color(*self._c('secondary'))
            self.set_xy(MARGIN, 5)
            self.cell(CONTENT_W, 3, f'MOONLANGUAGE - {self.style["name"]}')

    def footer(self):
        self.set_y(-10)
        self.set_font('Helvetica', '', 7)
        self.set_text_color(*self._c('secondary'))
        self.cell(0, 4, str(self.page_no()), align='C')

    def title_page(self):
        self.add_page()
        self.set_fill_color(*self._c('dark'))
        self.rect(0, 0, PAGE_W, PAGE_H, 'F')
        self.set_y(PAGE_H / PHI - 20)
        self.set_font('Helvetica', 'B', 26)
        self.set_text_color(*self._c('accent'))
        self.cell(0, 10, 'MOONLANGUAGE', align='C')
        self.ln(12)
        self.set_font('Helvetica', '', 11)
        self.set_text_color(*self._c('primary'))
        self.cell(0, 6, 'Verse of a Visual Universe', align='C')
        self.ln(7)
        self.set_font('Helvetica', 'I', 9)
        self.set_text_color(*self._c('secondary'))
        self.cell(0, 5, '968 Cosmic Transmissions by The Founder', align='C')
        self.ln(15)
        self.set_draw_color(*self._c('accent'))
        self.line(PAGE_W/2-30, self.get_y(), PAGE_W/2+30, self.get_y())
        self.ln(12)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(*self._c('highlight'))
        self.set_x(25)
        self.multi_cell(PAGE_W-50, 4, self._clean(self.style['dedication']), align='C')
        self.ln(3)
        self.set_font('Helvetica', '', 7)
        self.set_text_color(*self._c('secondary'))
        self.cell(0, 3, f'{self.style["name"]} | {self.style["philosophy"]}', align='C')

    def h1(self, t):
        # NO new page - just bold header with line
        if self._space() < 20:
            self.add_page()
        self.ln(4)
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(*self._c('primary'))
        self.multi_cell(CONTENT_W, 5, self._clean(t))
        self.set_draw_color(*self._c('accent'))
        self.set_line_width(0.4)
        self.line(MARGIN, self.get_y(), MARGIN + 70, self.get_y())
        self.ln(3)

    def h2(self, t):
        if self._space() < 12:
            self.add_page()
        self.ln(3)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(*self._c('primary'))
        self.multi_cell(CONTENT_W, 4.5, self._clean(t))
        self.ln(1)

    def h3(self, t):
        if self._space() < 10:
            self.add_page()
        self.ln(2)
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(*self._c('secondary'))
        self.multi_cell(CONTENT_W, 4, self._clean(t))
        self.ln(1)

    def para(self, t):
        if self._space() < 8:
            self.add_page()
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*self._c('dark'))
        self.multi_cell(CONTENT_W, 3.8, self._clean(t))
        self.ln(1)

    def bullet(self, t):
        if self._space() < 6:
            self.add_page()
        self.set_x(MARGIN + 3)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*self._c('accent'))
        self.cell(3, 3.8, '-')
        self.set_text_color(*self._c('dark'))
        self.multi_cell(CONTENT_W - 6, 3.8, self._clean(t))

    def quote(self, t):
        if self._space() < 10:
            self.add_page()
        self.ln(1)
        y0 = self.get_y()
        self.set_x(MARGIN + 5)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(*self._c('secondary'))
        self.multi_cell(CONTENT_W - 8, 3.8, self._clean(t))
        self.set_draw_color(*self._c('accent'))
        self.set_line_width(1)
        self.line(MARGIN + 2, y0, MARGIN + 2, self.get_y())
        self.ln(1)

    def code(self, t):
        lines = t.split('\n')
        if len(lines) > 12: lines = lines[:11] + ['...']
        h = len(lines) * 3.2 + 4
        if self._space() < h:
            self.add_page()
        self.ln(1)
        y0 = self.get_y()
        self.set_fill_color(*self._c('dark'))
        self.rect(MARGIN, y0, CONTENT_W, h, 'F')
        self.set_font('Helvetica', '', 6.5)
        self.set_text_color(*self._c('bg'))
        self.set_y(y0 + 2)
        for line in lines:
            self.set_x(MARGIN + 2)
            self.cell(CONTENT_W - 4, 3.2, self._clean(line)[:80])
            self.ln(3.2)
        self.set_y(y0 + h + 1)

    def tbl(self, cells, hdr=False):
        if self._space() < 6:
            self.add_page()
        w = CONTENT_W / len(cells)
        if hdr:
            self.set_fill_color(*self._c('primary'))
            self.set_text_color(255, 255, 255)
            self.set_font('Helvetica', 'B', 7)
        else:
            self.set_fill_color(*self._c('bg'))
            self.set_text_color(*self._c('dark'))
            self.set_font('Helvetica', '', 7)
        self.set_x(MARGIN)
        for c in cells:
            self.cell(w, 4.5, self._clean(str(c))[:25], 1, 0, 'L', True)
        self.ln()

    def hr(self):
        self.ln(2)
        self.set_draw_color(*self._c('accent'))
        self.set_line_width(0.2)
        self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
        self.ln(2)

    def closing(self):
        self.add_page()
        self.set_fill_color(*self._c('dark'))
        self.rect(0, 0, PAGE_W, PAGE_H, 'F')
        self.set_y(PAGE_H / PHI - 10)
        self.set_font('Helvetica', 'I', 10)
        self.set_text_color(*self._c('accent'))
        self.set_x(30)
        self.multi_cell(PAGE_W - 60, 5, '"I fell in love with DATA and I\'ll never be the same."', align='C')
        self.ln(3)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*self._c('secondary'))
        self.cell(0, 4, '- The Founder', align='C')
        self.ln(10)
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(*self._c('highlight'))
        self.cell(0, 4, 'SO MOTE IT BE', align='C')


def parse(content):
    elements = []
    lines = content.split('\n')
    i, in_code, code_buf = 0, False, []
    while i < len(lines):
        line = lines[i]
        if line.startswith('```'):
            if in_code:
                elements.append(('code', '\n'.join(code_buf)))
                code_buf, in_code = [], False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue
        if line.startswith('# '):
            elements.append(('h1', line[2:].strip()))
        elif line.startswith('## '):
            elements.append(('h2', line[3:].strip()))
        elif line.startswith('### '):
            elements.append(('h3', line[4:].strip()))
        elif line.startswith('> '):
            q = [line[2:]]
            while i + 1 < len(lines) and lines[i + 1].startswith('> '):
                i += 1
                q.append(lines[i][2:])
            elements.append(('quote', ' '.join(q)))
        elif line.startswith('- ') or line.startswith('* '):
            elements.append(('bullet', line[2:].strip()))
        elif re.match(r'^\d+\.\s', line):
            elements.append(('bullet', re.sub(r'^\d+\.\s*', '', line).strip()))
        elif line.strip() == '---':
            elements.append(('hr', ''))
        elif '|' in line and not re.match(r'^\|[-:\s|]+\|$', line.strip()):
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if cells and not all(c.replace('-','').replace(':','').strip() == '' for c in cells):
                is_hdr = i + 1 < len(lines) and re.match(r'^\|[-:\s|]+\|$', lines[i + 1].strip())
                elements.append(('tbl', (cells, is_hdr)))
                if is_hdr: i += 1
        elif line.strip():
            elements.append(('para', line.strip()))
        i += 1
    return elements


def gen(inp, style, out=None):
    p = Path(inp)
    if not p.exists():
        print(f"  Error: {inp}")
        return
    out = out or str(p.parent / f'MOONLANGUAGE_{style.upper()}.pdf')
    pdf = CompactPDF(style)
    pdf.title_page()
    skip = True
    for t, d in parse(p.read_text('utf-8')):
        if skip and t in ('h1','h2','h3'):
            if any(x in str(d).upper() for x in ['MOONLANGUAGE','VERSE','968']):
                continue
            skip = False
        if t == 'tbl':
            pdf.tbl(*d)
        elif t == 'hr':
            pdf.hr()
        else:
            getattr(pdf, t, pdf.para)(d)
    pdf.closing()
    pdf.output(out)
    print(f"  {style.upper()}: {out}")


def main():
    print("\n" + "=" * 55)
    print("  MOONLANGUAGE v4 - COMPACT (No Whitespace Waste)")
    print("=" * 55 + "\n")
    inp = "exports/MOONLANGUAGE_COMPLETE_DOCUMENTATION.md"
    for s in ARTIST_STYLES:
        gen(inp, s)
    print("\n" + "=" * 55 + "\n")


if __name__ == "__main__":
    main()

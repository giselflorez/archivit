#!/usr/bin/env python3
"""
MOONLANGUAGE Sacred PDF Generator v3
AUTHENTIC COLOR PALETTES from actual artist research
Smart pagination - no empty pages
"""

import sys
import re
from pathlib import Path
from fpdf import FPDF

# Sacred Mathematics
PHI = 1.618033988749895

# Page dimensions (A4)
PAGE_W = 210
PAGE_H = 297
MARGIN = 18
CONTENT_W = PAGE_W - (2 * MARGIN)

# ============================================================
# AUTHENTIC ARTIST PALETTES - Research-Verified
# ============================================================

ARTIST_STYLES = {
    'hildegard': {
        # Source: Scivias illuminations, Eibingen facsimile
        'name': 'Hildegard of Bingen',
        'years': '1098-1179',
        'dedication': 'For Hildegard, who saw visions in light and heard the cosmos sing.',
        'philosophy': 'Viriditas - The Greening Power of Divine Creation',
        'colors': {
            'bg': (245, 238, 220),          # Parchment/vellum
            'dark': (45, 32, 22),            # Vellum dark
            'primary': (38, 97, 156),        # Sapphire blue - divine figures #26619C
            'secondary': (74, 124, 89),      # Viriditas green #4A7C59
            'accent': (212, 175, 55),        # Sacred gold #D4AF37
            'highlight': (114, 47, 55),      # Burgundy flame #722F37
        }
    },
    'davinci': {
        # Source: Mona Lisa pigment analysis, Treatise on Painting, notebooks
        'name': 'Leonardo da Vinci',
        'years': '1452-1519',
        'dedication': 'For Leonardo, who united art and science through sfumato.',
        'philosophy': 'Observation - The Mother of All Certainty',
        'colors': {
            'bg': (252, 248, 240),           # Paper cream
            'dark': (53, 37, 36),            # Temptress shadow #352524
            'primary': (112, 66, 20),        # Sepia ink #704214
            'secondary': (114, 127, 75),     # Gold fusion olive #727F4B
            'accent': (233, 196, 104),       # Arylide yellow #E9C468
            'highlight': (118, 75, 28),      # Russet #764B1C
        }
    },
    'tesla': {
        # Source: Tesla's writings, electrical discharge physics, synesthesia accounts
        'name': 'Nikola Tesla',
        'years': '1856-1943',
        'dedication': 'For Tesla, who saw the universe in tongues of living flame.',
        'philosophy': 'If You Want to Find the Secrets - Think in Energy, Frequency, Vibration',
        'colors': {
            'bg': (232, 236, 248),           # Plasma glow
            'dark': (12, 15, 28),            # Night laboratory #0C0F1C
            'primary': (90, 70, 160),        # Violet discharge
            'secondary': (69, 93, 156),      # Electric blue #455D9C
            'accent': (255, 215, 0),         # Lightning gold #FFD700
            'highlight': (156, 136, 189),    # Lavender plasma
        }
    },
    'gisel': {
        # Source: MOONLANGUAGE WebGL viewer, video transcriptions
        'name': 'Gisel X Florez',
        'years': '1980-present',
        'dedication': 'For Gisel, who dances with the moon and captures cosmic transmissions.',
        'philosophy': 'I Fell in Love with DATA and I Will Never Be the Same',
        'colors': {
            'bg': (240, 236, 231),           # Warm white
            'dark': (3, 3, 8),               # Void black #030308
            'primary': (212, 165, 116),      # Moon gold #D4A574
            'secondary': (186, 101, 135),    # Iridescent rose #BA6587
            'accent': (120, 101, 186),       # Holographic purple #7865BA
            'highlight': (84, 168, 118),     # Emerald #54A876
        }
    },
    'bjork': {
        # Source: Album artwork analysis, Jesse Kanda, M/M Paris collaborations
        'name': 'Bjork Gudmundsdottir',
        'years': '1965-present',
        'dedication': 'For Bjork, who dissolves boundaries between nature and technology.',
        'philosophy': 'Acoustic Symbolism - Visual Translation of Sound',
        'colors': {
            'bg': (248, 244, 248),           # Aurora white
            'dark': (20, 28, 32),            # Deep ocean
            'primary': (220, 180, 60),       # Vulnicura healing yellow
            'secondary': (135, 186, 170),    # Utopia sea-green
            'accent': (220, 160, 140),       # Utopia peach
            'highlight': (150, 100, 120),    # Bio-rose
        }
    },
    'fuller': {
        # Source: Geodesic domes, Dymaxion designs, Synergetics diagrams
        'name': 'R. Buckminster Fuller',
        'years': '1895-1983',
        'dedication': 'For Bucky, who did more with less through material honesty.',
        'philosophy': 'Ephemeralization - Doing More With Less',
        'colors': {
            'bg': (240, 242, 245),           # Clean structural
            'dark': (18, 22, 28),            # Space
            'primary': (120, 125, 135),      # Aluminum/steel gray
            'secondary': (45, 65, 85),       # Structural blue
            'accent': (180, 150, 80),        # Geodesic gold
            'highlight': (140, 60, 60),      # Synergetics red
        }
    }
}


class SacredPDF(FPDF):
    def __init__(self, style_key='gisel'):
        super().__init__()
        self.style = ARTIST_STYLES[style_key]
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(MARGIN, MARGIN, MARGIN)

    def _c(self, key):
        return self.style['colors'][key]

    def _clean(self, text):
        if not text:
            return ''
        replacements = {
            '\u2014': '--', '\u2013': '-', '\u2018': "'", '\u2019': "'",
            '\u201c': '"', '\u201d': '"', '\u2026': '...',
            '\u2554': '+', '\u2557': '+', '\u255a': '+', '\u255d': '+',
            '\u2550': '=', '\u2551': '|', '\u250c': '+', '\u2510': '+',
            '\u2514': '+', '\u2518': '+', '\u2500': '-', '\u2502': '|',
            '\u2191': '^', '\u2193': 'v', '\u2192': '>', '\u2190': '<',
            '\u25bc': 'v', '\u25b2': '^', '\u2022': '*', '\u2713': 'x',
            '\u2502': '|', '\u251c': '+', '\u2524': '+', '\u253c': '+',
        }
        for char, repl in replacements.items():
            text = text.replace(char, repl)
        return ''.join(c if ord(c) < 256 else ' ' for c in text)

    def _remaining(self):
        return PAGE_H - 25 - self.get_y()

    def _needs_page(self, h):
        return self._remaining() < h

    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', '', 7)
            self.set_text_color(*self._c('secondary'))
            self.set_xy(MARGIN, 8)
            self.cell(CONTENT_W, 4, f'MOONLANGUAGE  -  {self.style["name"]}', align='L')

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*self._c('secondary'))
        self.cell(0, 5, str(self.page_no()), align='C')

    def title_page(self):
        self.add_page()
        self.set_fill_color(*self._c('dark'))
        self.rect(0, 0, PAGE_W, PAGE_H, 'F')

        # Golden ratio position
        self.set_y(PAGE_H / PHI - 25)

        self.set_font('Helvetica', 'B', 28)
        self.set_text_color(*self._c('accent'))
        self.cell(0, 12, 'MOONLANGUAGE', align='C')
        self.ln(14)

        self.set_font('Helvetica', '', 13)
        self.set_text_color(*self._c('primary'))
        self.cell(0, 7, 'Verse of a Visual Universe', align='C')
        self.ln(9)

        self.set_font('Helvetica', 'I', 10)
        self.set_text_color(*self._c('secondary'))
        self.cell(0, 6, '968 Cosmic Transmissions by Gisel X Florez', align='C')
        self.ln(20)

        # Accent line
        self.set_draw_color(*self._c('accent'))
        self.set_line_width(0.8)
        cx = PAGE_W / 2
        self.line(cx - 35, self.get_y(), cx + 35, self.get_y())
        self.ln(20)

        # Dedication
        self.set_x(25)
        self.set_font('Helvetica', 'I', 9)
        self.set_text_color(*self._c('highlight'))
        self.multi_cell(PAGE_W - 50, 5, self._clean(self.style['dedication']), align='C')
        self.ln(6)

        self.set_font('Helvetica', '', 8)
        self.set_text_color(*self._c('secondary'))
        self.cell(0, 4, f'{self.style["name"]} ({self.style["years"]})', align='C')
        self.ln(4)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 4, self._clean(self.style['philosophy']), align='C')

    def part_title(self, text):
        """Major section - new page"""
        self.add_page()
        self.set_y(45)
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(*self._c('primary'))
        self.multi_cell(CONTENT_W, 8, self._clean(text))

        self.set_draw_color(*self._c('accent'))
        self.set_line_width(0.6)
        self.line(MARGIN, self.get_y() + 2, MARGIN + 80, self.get_y() + 2)
        self.ln(8)

    def h2(self, text):
        """Section header - flows"""
        if self._needs_page(18):
            self.add_page()
        self.ln(6)
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(*self._c('primary'))
        self.multi_cell(CONTENT_W, 6, self._clean(text))
        self.ln(3)

    def h3(self, text):
        """Subsection - inline"""
        if self._needs_page(12):
            self.add_page()
        self.ln(4)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(*self._c('secondary'))
        self.multi_cell(CONTENT_W, 5, self._clean(text))
        self.ln(2)

    def para(self, text):
        if self._needs_page(10):
            self.add_page()
        self.set_font('Helvetica', '', 9)
        self.set_text_color(*self._c('dark'))
        self.multi_cell(CONTENT_W, 4.5, self._clean(text))
        self.ln(2)

    def bullet(self, text):
        if self._needs_page(8):
            self.add_page()
        self.set_x(MARGIN + 4)
        self.set_font('Helvetica', '', 9)
        self.set_text_color(*self._c('accent'))
        self.cell(4, 4.5, '-')
        self.set_text_color(*self._c('dark'))
        self.multi_cell(CONTENT_W - 8, 4.5, self._clean(text))

    def quote(self, text):
        if self._needs_page(12):
            self.add_page()
        self.ln(2)
        y0 = self.get_y()
        self.set_x(MARGIN + 6)
        self.set_font('Helvetica', 'I', 9)
        self.set_text_color(*self._c('secondary'))
        self.multi_cell(CONTENT_W - 12, 4.5, self._clean(text))
        y1 = self.get_y()
        self.set_draw_color(*self._c('accent'))
        self.set_line_width(1.2)
        self.line(MARGIN + 2, y0, MARGIN + 2, y1)
        self.ln(2)

    def code(self, text):
        lines = text.split('\n')
        if len(lines) > 15:
            lines = lines[:14] + ['  ...']
        h = len(lines) * 3.8 + 5
        if self._needs_page(h):
            self.add_page()

        self.ln(2)
        y0 = self.get_y()
        self.set_fill_color(*self._c('dark'))
        self.rect(MARGIN, y0, CONTENT_W, h, 'F')

        self.set_font('Helvetica', '', 7)
        self.set_text_color(*self._c('bg'))
        self.set_y(y0 + 2)
        for line in lines:
            self.set_x(MARGIN + 3)
            self.cell(CONTENT_W - 6, 3.8, self._clean(line)[:75])
            self.ln(3.8)
        self.set_y(y0 + h + 2)

    def table_row(self, cells, header=False):
        if self._needs_page(8):
            self.add_page()
        n = len(cells)
        w = CONTENT_W / n

        if header:
            self.set_fill_color(*self._c('primary'))
            self.set_text_color(255, 255, 255)
            self.set_font('Helvetica', 'B', 8)
        else:
            self.set_fill_color(*self._c('bg'))
            self.set_text_color(*self._c('dark'))
            self.set_font('Helvetica', '', 8)

        self.set_x(MARGIN)
        for cell in cells:
            self.cell(w, 5.5, self._clean(str(cell))[:28], 1, 0, 'L', True)
        self.ln()

    def hr(self):
        self.ln(4)
        self.set_draw_color(*self._c('accent'))
        self.set_line_width(0.3)
        self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
        self.ln(4)

    def closing(self):
        self.add_page()
        self.set_fill_color(*self._c('dark'))
        self.rect(0, 0, PAGE_W, PAGE_H, 'F')

        self.set_y(PAGE_H / PHI - 15)
        self.set_font('Helvetica', 'I', 11)
        self.set_text_color(*self._c('accent'))
        self.set_x(30)
        self.multi_cell(PAGE_W - 60, 6, '"I fell in love with DATA and I\'ll never be the same."', align='C')

        self.ln(4)
        self.set_font('Helvetica', '', 9)
        self.set_text_color(*self._c('secondary'))
        self.cell(0, 5, '- Gisel X Florez', align='C')

        self.ln(15)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(*self._c('highlight'))
        self.cell(0, 5, 'SO MOTE IT BE', align='C')

        self.ln(12)
        self.set_font('Helvetica', '', 7)
        self.set_text_color(*self._c('secondary'))
        self.cell(0, 4, f'PHI = {PHI:.12f}', align='C')


def parse(content):
    elements = []
    lines = content.split('\n')
    i = 0
    in_code = False
    code_buf = []

    while i < len(lines):
        line = lines[i]

        if line.startswith('```'):
            if in_code:
                elements.append(('code', '\n'.join(code_buf)))
                code_buf = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        if line.startswith('# '):
            t = line[2:].strip()
            if 'PART' in t.upper() or 'APPENDIX' in t.upper():
                elements.append(('part', t))
            else:
                elements.append(('h1', t))
        elif line.startswith('## '):
            elements.append(('h2', line[3:].strip()))
        elif line.startswith('### '):
            elements.append(('h3', line[4:].strip()))
        elif line.startswith('> '):
            qlines = [line[2:]]
            while i + 1 < len(lines) and lines[i + 1].startswith('> '):
                i += 1
                qlines.append(lines[i][2:])
            elements.append(('quote', ' '.join(qlines)))
        elif line.startswith('- ') or line.startswith('* '):
            elements.append(('bullet', line[2:].strip()))
        elif re.match(r'^\d+\.\s', line):
            elements.append(('bullet', re.sub(r'^\d+\.\s*', '', line).strip()))
        elif line.strip() == '---':
            elements.append(('hr', ''))
        elif '|' in line and not re.match(r'^\|[-:\s|]+\|$', line.strip()):
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if cells and not all(c.replace('-', '').replace(':', '').strip() == '' for c in cells):
                is_hdr = i + 1 < len(lines) and re.match(r'^\|[-:\s|]+\|$', lines[i + 1].strip())
                elements.append(('table', (cells, is_hdr)))
                if is_hdr:
                    i += 1
        elif line.strip():
            elements.append(('text', line.strip()))

        i += 1
    return elements


def generate(input_path, style_key, output_path=None):
    inp = Path(input_path)
    if not inp.exists():
        print(f"  Error: {input_path} not found")
        return False

    if output_path is None:
        output_path = str(inp.parent / f'MOONLANGUAGE_{style_key.upper()}.pdf')

    content = inp.read_text(encoding='utf-8')
    pdf = SacredPDF(style_key)
    pdf.title_page()

    elements = parse(content)
    skip = True

    for etype, data in elements:
        if skip and etype in ('h1', 'h2', 'h3', 'part'):
            if any(x in str(data).upper() for x in ['MOONLANGUAGE', 'VERSE', '968']):
                continue
            skip = False

        if etype == 'part':
            pdf.part_title(data)
        elif etype == 'h1':
            pdf.part_title(data)
        elif etype == 'h2':
            pdf.h2(data)
        elif etype == 'h3':
            pdf.h3(data)
        elif etype == 'text':
            pdf.para(data)
        elif etype == 'bullet':
            pdf.bullet(data)
        elif etype == 'quote':
            pdf.quote(data)
        elif etype == 'code':
            pdf.code(data)
        elif etype == 'table':
            cells, is_hdr = data
            pdf.table_row(cells, is_hdr)
        elif etype == 'hr':
            pdf.hr()

    pdf.closing()
    pdf.output(output_path)
    print(f"  {style_key.upper()}: {output_path}")
    return True


def main():
    print("\n" + "=" * 60)
    print("  MOONLANGUAGE Sacred PDF v3")
    print("  Authentic Artist Color Palettes | Smart Pagination")
    print("=" * 60)

    inp = "exports/MOONLANGUAGE_COMPLETE_DOCUMENTATION.md"

    if len(sys.argv) > 1 and sys.argv[1] != '--all':
        if sys.argv[1] in ARTIST_STYLES:
            generate(inp, sys.argv[1])
        else:
            print(f"  Available: {', '.join(ARTIST_STYLES.keys())}")
        return

    print("\n  Generating 6 artist-dedicated variants...\n")
    for key in ARTIST_STYLES:
        generate(inp, key)

    print("\n" + "=" * 60)
    print("  Complete. PDFs in exports/")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

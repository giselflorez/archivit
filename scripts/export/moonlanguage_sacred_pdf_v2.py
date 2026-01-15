#!/usr/bin/env python3
"""
MOONLANGUAGE Sacred PDF Generator v2
Improved pagination - no empty pages, smart content flow
6 artist dedications with golden ratio mathematics
"""

import sys
import re
import math
from pathlib import Path
from fpdf import FPDF

# Sacred Mathematics
PHI = 1.618033988749895
GOLDEN_ANGLE = 137.5077640500378
SCHUMANN = 7.83

# Page dimensions (A4)
PAGE_WIDTH = 210
PAGE_HEIGHT = 297
MARGIN = 20
CONTENT_WIDTH = PAGE_WIDTH - (2 * MARGIN)
USABLE_HEIGHT = PAGE_HEIGHT - 50  # Account for header/footer

# Artist Styles
ARTIST_STYLES = {
    'hildegard': {
        'name': 'Hildegard of Bingen',
        'years': '1098-1179',
        'dedication': 'For Hildegard, who saw visions in light and heard the cosmos sing.',
        'philosophy': 'Sacred Geometry & Divine Sound',
        'colors': {
            'primary': (139, 90, 43),
            'secondary': (84, 130, 53),
            'accent': (186, 135, 89),
            'dark': (45, 32, 22),
            'light': (245, 238, 220),
            'bg': (255, 255, 255)
        }
    },
    'davinci': {
        'name': 'Leonardo da Vinci',
        'years': '1452-1519',
        'dedication': 'For Leonardo, who united art and science in the spiral of nature.',
        'philosophy': 'Art-Science Unity through Observation',
        'colors': {
            'primary': (101, 67, 33),
            'secondary': (139, 119, 101),
            'accent': (212, 165, 116),
            'dark': (28, 24, 20),
            'light': (252, 248, 240),
            'bg': (255, 255, 255)
        }
    },
    'tesla': {
        'name': 'Nikola Tesla',
        'years': '1856-1943',
        'dedication': 'For Tesla, who understood the universe speaks in frequency.',
        'philosophy': 'Energy, Frequency, Vibration',
        'colors': {
            'primary': (69, 93, 156),
            'secondary': (156, 136, 189),
            'accent': (200, 170, 50),
            'dark': (12, 15, 28),
            'light': (232, 236, 248),
            'bg': (255, 255, 255)
        }
    },
    'gisel': {
        'name': 'Gisel X Florez',
        'years': '1980-present',
        'dedication': 'For Gisel, who dances with the moon and captures cosmic transmissions.',
        'philosophy': 'Light Photography & Lunar Dance',
        'colors': {
            'primary': (180, 140, 90),
            'secondary': (84, 140, 100),
            'accent': (186, 101, 135),
            'dark': (20, 20, 30),
            'light': (240, 236, 231),
            'bg': (255, 255, 255)
        }
    },
    'bjork': {
        'name': 'Bjork Gudmundsdottir',
        'years': '1965-present',
        'dedication': 'For Bjork, who dissolves boundaries between nature and technology.',
        'philosophy': 'Boundary Dissolution & Organic Synthesis',
        'colors': {
            'primary': (150, 100, 120),
            'secondary': (100, 140, 150),
            'accent': (150, 150, 100),
            'dark': (20, 28, 32),
            'light': (248, 244, 248),
            'bg': (255, 255, 255)
        }
    },
    'fuller': {
        'name': 'R. Buckminster Fuller',
        'years': '1895-1983',
        'dedication': 'For Bucky, who saw the universe as patterns of integrity.',
        'philosophy': 'Synergetics & Systems Thinking',
        'colors': {
            'primary': (45, 65, 85),
            'secondary': (85, 105, 85),
            'accent': (180, 150, 80),
            'dark': (18, 22, 28),
            'light': (240, 242, 245),
            'bg': (255, 255, 255)
        }
    }
}


class SacredPDF(FPDF):
    """PDF with smart pagination and artist styling"""

    def __init__(self, style_key='gisel'):
        super().__init__()
        self.style = ARTIST_STYLES[style_key]
        self.style_key = style_key
        self.set_auto_page_break(auto=True, margin=25)
        self.set_margins(MARGIN, MARGIN, MARGIN)

    def _rgb(self, key):
        return self.style['colors'][key]

    def _clean(self, text):
        """Clean text for Latin-1 encoding"""
        replacements = {
            '\u2014': '--', '\u2013': '-',
            '\u2018': "'", '\u2019': "'",
            '\u201c': '"', '\u201d': '"',
            '\u2026': '...', '\u00b7': '*',
            '\u2554': '+', '\u2557': '+', '\u255a': '+', '\u255d': '+',
            '\u2550': '=', '\u2551': '|',
            '\u250c': '+', '\u2510': '+', '\u2514': '+', '\u2518': '+',
            '\u2500': '-', '\u2502': '|',
            '\u2191': '^', '\u2193': 'v', '\u2190': '<', '\u2192': '>',
            '\u25bc': 'v', '\u25b2': '^', '\u2022': '*', '\u2713': 'x',
        }
        for char, repl in replacements.items():
            text = text.replace(char, repl)
        return ''.join(c if ord(c) < 256 else ' ' for c in text)

    def _space_left(self):
        """Return remaining vertical space on page"""
        return USABLE_HEIGHT - self.get_y()

    def _need_page(self, height_needed):
        """Check if we need a new page for content"""
        return self._space_left() < height_needed

    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', '', 8)
            self.set_text_color(*self._rgb('secondary'))
            self.set_y(10)
            self.cell(0, 5, f'MOONLANGUAGE  |  {self.style["name"]}', align='L')
            self.set_y(MARGIN)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*self._rgb('secondary'))
        self.cell(0, 10, f'{self.page_no()}', align='C')

    def title_page(self):
        """Elegant title page"""
        self.add_page()
        self.set_fill_color(*self._rgb('dark'))
        self.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, style='F')

        # Centered title at golden position
        self.set_y(PAGE_HEIGHT / PHI - 30)
        self.set_font('Helvetica', 'B', 32)
        self.set_text_color(*self._rgb('accent'))
        self.cell(0, 12, 'MOONLANGUAGE', align='C')
        self.ln(15)

        self.set_font('Helvetica', '', 14)
        self.set_text_color(*self._rgb('light'))
        self.cell(0, 8, 'Verse of a Visual Universe', align='C')
        self.ln(10)

        self.set_font('Helvetica', 'I', 11)
        self.set_text_color(*self._rgb('secondary'))
        self.cell(0, 6, '968 Cosmic Transmissions by Gisel X Florez', align='C')
        self.ln(25)

        # Decorative line
        self.set_draw_color(*self._rgb('accent'))
        self.set_line_width(0.5)
        cx = PAGE_WIDTH / 2
        self.line(cx - 40, self.get_y(), cx + 40, self.get_y())
        self.ln(25)

        # Artist dedication
        self.set_font('Helvetica', 'I', 10)
        self.set_text_color(*self._rgb('light'))
        self.set_x(30)
        self.multi_cell(PAGE_WIDTH - 60, 6, self._clean(self.style['dedication']), align='C')
        self.ln(8)

        self.set_font('Helvetica', '', 9)
        self.set_text_color(*self._rgb('secondary'))
        self.cell(0, 5, f'Styled in honor of {self.style["name"]} ({self.style["years"]})', align='C')
        self.ln(5)
        self.cell(0, 5, self.style['philosophy'], align='C')

    def part_header(self, title):
        """Major section header - gets its own page"""
        self.add_page()
        self.set_y(60)
        self.set_font('Helvetica', 'B', 18)
        self.set_text_color(*self._rgb('primary'))
        self.cell(0, 10, self._clean(title), align='L')

        # Accent line
        self.ln(5)
        self.set_draw_color(*self._rgb('accent'))
        self.set_line_width(0.8)
        self.line(MARGIN, self.get_y(), MARGIN + 100, self.get_y())
        self.ln(12)

    def section_header(self, title):
        """H2 - subsection, flows with content"""
        if self._need_page(25):
            self.add_page()
        else:
            self.ln(8)

        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(*self._rgb('primary'))
        self.cell(0, 8, self._clean(title), align='L')
        self.ln(6)

    def subsection_header(self, title):
        """H3 - minor header, inline"""
        if self._need_page(15):
            self.add_page()
        else:
            self.ln(5)

        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(*self._rgb('secondary'))
        self.cell(0, 6, self._clean(title), align='L')
        self.ln(4)

    def body(self, text):
        """Body text with flow"""
        if self._need_page(12):
            self.add_page()

        self.set_font('Helvetica', '', 10)
        self.set_text_color(*self._rgb('dark'))
        self.multi_cell(CONTENT_WIDTH, 5, self._clean(text))
        self.ln(3)

    def bullet(self, text):
        """Bullet point"""
        if self._need_page(10):
            self.add_page()

        self.set_font('Helvetica', '', 10)
        self.set_text_color(*self._rgb('accent'))
        self.set_x(MARGIN + 5)
        self.cell(5, 5, '-')
        self.set_text_color(*self._rgb('dark'))
        self.multi_cell(CONTENT_WIDTH - 10, 5, self._clean(text))

    def quote(self, text):
        """Blockquote with accent bar"""
        if self._need_page(15):
            self.add_page()
        self.ln(3)

        y_start = self.get_y()
        self.set_x(MARGIN + 8)
        self.set_font('Helvetica', 'I', 10)
        self.set_text_color(*self._rgb('secondary'))
        self.multi_cell(CONTENT_WIDTH - 15, 5, self._clean(text))
        y_end = self.get_y()

        self.set_draw_color(*self._rgb('accent'))
        self.set_line_width(1.5)
        self.line(MARGIN + 3, y_start, MARGIN + 3, y_end)
        self.ln(3)

    def code(self, text):
        """Code block - compact"""
        lines = text.split('\n')
        # Limit to reasonable size
        if len(lines) > 20:
            lines = lines[:18] + ['...']

        height = len(lines) * 4 + 6
        if self._need_page(height):
            self.add_page()

        self.ln(3)
        self.set_fill_color(*self._rgb('dark'))
        self.set_text_color(*self._rgb('light'))
        self.set_font('Helvetica', '', 8)

        y_start = self.get_y()
        self.rect(MARGIN, y_start, CONTENT_WIDTH, height, style='F')
        self.set_y(y_start + 3)

        for line in lines:
            self.set_x(MARGIN + 3)
            self.cell(0, 4, self._clean(line)[:85])
            self.ln(4)

        self.set_y(y_start + height + 3)

    def table_start(self):
        """Prepare for table"""
        if self._need_page(20):
            self.add_page()
        self.ln(2)

    def table_row(self, cells, header=False):
        """Table row - calculate width dynamically"""
        if self._need_page(10):
            self.add_page()

        num_cols = len(cells)
        col_width = CONTENT_WIDTH / num_cols

        if header:
            self.set_fill_color(*self._rgb('dark'))
            self.set_text_color(*self._rgb('light'))
            self.set_font('Helvetica', 'B', 9)
        else:
            self.set_fill_color(*self._rgb('light'))
            self.set_text_color(*self._rgb('dark'))
            self.set_font('Helvetica', '', 9)

        self.set_x(MARGIN)
        for cell in cells:
            # Truncate long cells
            text = self._clean(str(cell))[:35]
            self.cell(col_width, 6, text, border=1, fill=True)
        self.ln()

    def divider(self):
        """Horizontal rule - no page break"""
        self.ln(5)
        self.set_draw_color(*self._rgb('accent'))
        self.set_line_width(0.3)
        self.line(MARGIN, self.get_y(), PAGE_WIDTH - MARGIN, self.get_y())
        self.ln(5)

    def closing_page(self):
        """Final dedication page"""
        self.add_page()
        self.set_fill_color(*self._rgb('dark'))
        self.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, style='F')

        self.set_y(PAGE_HEIGHT / PHI - 20)
        self.set_font('Helvetica', 'I', 12)
        self.set_text_color(*self._rgb('accent'))
        self.set_x(30)
        self.multi_cell(PAGE_WIDTH - 60, 8, '"I fell in love with DATA and I\'ll never be the same."', align='C')

        self.ln(5)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(*self._rgb('secondary'))
        self.cell(0, 6, '- Gisel X Florez', align='C')

        self.ln(20)
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(*self._rgb('light'))
        self.cell(0, 6, 'SO MOTE IT BE', align='C')

        self.ln(15)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*self._rgb('secondary'))
        self.cell(0, 4, f'PHI = {PHI:.10f}', align='C')


def parse_markdown(content):
    """Parse markdown with better structure detection"""
    elements = []
    lines = content.split('\n')
    i = 0
    in_code = False
    code_buf = []

    while i < len(lines):
        line = lines[i]

        # Code blocks
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

        # Headers - detect PART headers specially
        if line.startswith('# '):
            title = line[2:].strip()
            if 'PART' in title.upper() or title == 'APPENDIX: TECHNICAL METADATA':
                elements.append(('part', title))
            else:
                elements.append(('h1', title))
        elif line.startswith('## '):
            elements.append(('h2', line[3:].strip()))
        elif line.startswith('### '):
            elements.append(('h3', line[4:].strip()))
        # Blockquotes
        elif line.startswith('> '):
            quote_lines = [line[2:]]
            while i + 1 < len(lines) and lines[i + 1].startswith('> '):
                i += 1
                quote_lines.append(lines[i][2:])
            elements.append(('quote', ' '.join(quote_lines)))
        # Bullets
        elif line.startswith('- ') or line.startswith('* '):
            elements.append(('bullet', line[2:].strip()))
        elif re.match(r'^\d+\. ', line):
            elements.append(('bullet', re.sub(r'^\d+\. ', '', line).strip()))
        # Horizontal rule
        elif line.strip() == '---':
            elements.append(('hr', ''))
        # Tables
        elif '|' in line and not line.strip().startswith('|--') and not re.match(r'^\|[-:\s|]+\|$', line.strip()):
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if cells:
                is_header = i + 1 < len(lines) and '---' in lines[i + 1]
                elements.append(('table', (cells, is_header)))
                if is_header:
                    i += 1
        # Regular text
        elif line.strip():
            elements.append(('text', line.strip()))

        i += 1

    return elements


def generate_pdf(input_path: str, style_key: str, output_path: str = None):
    """Generate PDF with smart pagination"""
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"Error: {input_path} not found")
        return False

    if output_path is None:
        output_path = str(input_file.with_suffix(f'.{style_key}.pdf'))

    content = input_file.read_text(encoding='utf-8')
    pdf = SacredPDF(style_key)

    # Title page
    pdf.title_page()

    # Parse content
    elements = parse_markdown(content)

    # Skip document header (already in title page)
    skip_intro = True
    in_table = False

    for elem_type, data in elements:
        # Skip initial MOONLANGUAGE headers
        if skip_intro:
            if elem_type in ('h1', 'h2', 'h3', 'part'):
                if 'MOONLANGUAGE' in str(data).upper() or 'VERSE' in str(data).upper() or '968' in str(data):
                    continue
                else:
                    skip_intro = False

        if elem_type == 'part':
            in_table = False
            pdf.part_header(data)
        elif elem_type == 'h1':
            in_table = False
            pdf.part_header(data)  # Treat remaining H1s as parts
        elif elem_type == 'h2':
            in_table = False
            pdf.section_header(data)
        elif elem_type == 'h3':
            in_table = False
            pdf.subsection_header(data)
        elif elem_type == 'text':
            in_table = False
            pdf.body(data)
        elif elem_type == 'bullet':
            in_table = False
            pdf.bullet(data)
        elif elem_type == 'quote':
            in_table = False
            pdf.quote(data)
        elif elem_type == 'code':
            in_table = False
            pdf.code(data)
        elif elem_type == 'table':
            cells, is_header = data
            if not in_table:
                pdf.table_start()
                in_table = True
            pdf.table_row(cells, is_header)
        elif elem_type == 'hr':
            in_table = False
            pdf.divider()

    # Closing page
    pdf.closing_page()

    pdf.output(output_path)
    print(f"  Generated: {output_path}")
    return True


def generate_all(input_path: str):
    """Generate all 6 variants"""
    print("\n" + "=" * 55)
    print("  MOONLANGUAGE Sacred PDF Generator v2")
    print("  Smart Pagination | No Empty Pages | 6 Artist Styles")
    print("=" * 55 + "\n")

    for i, (key, style) in enumerate(ARTIST_STYLES.items(), 1):
        print(f"[{i}/6] {style['name']}")
        generate_pdf(input_path, key)

    print("\n" + "=" * 55)
    print("  All variants generated in exports/")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    input_file = "exports/MOONLANGUAGE_COMPLETE_DOCUMENTATION.md"

    if len(sys.argv) > 1:
        if sys.argv[1] == '--all':
            generate_all(input_file)
        elif sys.argv[1] in ARTIST_STYLES:
            generate_pdf(input_file, sys.argv[1])
        else:
            print(f"Styles: {', '.join(ARTIST_STYLES.keys())}")
            print("Use --all to generate all 6")
    else:
        generate_all(input_file)

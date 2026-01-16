#!/usr/bin/env python3
"""
MOONLANGUAGE Sacred PDF Generator
Creates elegantly styled PDFs using golden ratio mathematics and artist dedications
6 style variants framed by different NORTHSTAR masters

Sacred Constants:
- PHI = 1.618033988749895 (Golden Ratio)
- GOLDEN_ANGLE = 137.5077640500378
- SCHUMANN = 7.83 (Earth's resonance)
- TESLA_PATTERN = [3, 6, 9]
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
TESLA = [3, 6, 9]

# Golden Ratio page calculations (A4 = 210 x 297mm)
PAGE_WIDTH = 210
PAGE_HEIGHT = 297
GOLDEN_MARGIN = PAGE_WIDTH / (PHI * 4)  # ~32.4mm
GOLDEN_INNER = PAGE_WIDTH / PHI  # ~129.8mm - main content width

# 6 Artist Style Configurations
ARTIST_STYLES = {
    'hildegard': {
        'name': 'Hildegard of Bingen',
        'years': '1098-1179',
        'dedication': 'For Hildegard, who saw visions in light and heard the cosmos sing.',
        'philosophy': 'Sacred Geometry & Divine Sound',
        'colors': {
            'primary': (139, 90, 43),      # Earthen gold
            'secondary': (84, 130, 53),     # Viriditas green
            'accent': (186, 135, 89),       # Illuminated manuscript
            'dark': (45, 32, 22),           # Vellum dark
            'light': (245, 238, 220)        # Parchment
        },
        'pattern': 'mandala'  # Circular sacred patterns
    },
    'davinci': {
        'name': 'Leonardo da Vinci',
        'years': '1452-1519',
        'dedication': 'For Leonardo, who united art and science in the spiral of nature.',
        'philosophy': 'Art-Science Unity through Observation',
        'colors': {
            'primary': (101, 67, 33),       # Sepia
            'secondary': (139, 119, 101),   # Warm gray
            'accent': (212, 165, 116),      # Gold
            'dark': (28, 24, 20),           # Ink dark
            'light': (252, 248, 240)        # Paper cream
        },
        'pattern': 'spiral'  # Fibonacci spirals
    },
    'tesla': {
        'name': 'Nikola Tesla',
        'years': '1856-1943',
        'dedication': 'For Tesla, who understood the universe speaks in frequency.',
        'philosophy': 'Energy, Frequency, Vibration',
        'colors': {
            'primary': (69, 93, 156),       # Electric blue
            'secondary': (156, 136, 189),   # Violet
            'accent': (255, 215, 0),        # Lightning gold
            'dark': (12, 15, 28),           # Night sky
            'light': (232, 236, 248)        # Plasma glow
        },
        'pattern': 'wave'  # 3-6-9 wave patterns
    },
    'founder': {
        'name': 'The Founder',
        'years': '1980-present',
        'dedication': 'For Gisel, who dances with the moon and captures cosmic transmissions.',
        'philosophy': 'Light Photography & Lunar Dance',
        'colors': {
            'primary': (212, 165, 116),     # Moon gold
            'secondary': (84, 168, 118),    # Emerald
            'accent': (186, 101, 135),      # Rose
            'dark': (3, 3, 8),              # Void
            'light': (240, 236, 231)        # Warm white
        },
        'pattern': 'lunar'  # Moon phase patterns
    },
    'bjork': {
        'name': 'Björk Guðmundsdóttir',
        'years': '1965-present',
        'dedication': 'For Björk, who dissolves boundaries between nature and technology.',
        'philosophy': 'Boundary Dissolution & Organic Synthesis',
        'colors': {
            'primary': (186, 135, 135),     # Bio-rose
            'secondary': (135, 186, 186),   # Ice
            'accent': (186, 186, 135),      # Moss
            'dark': (20, 28, 32),           # Deep ocean
            'light': (248, 244, 248)        # Aurora
        },
        'pattern': 'organic'  # Crystalline organic forms
    },
    'fuller': {
        'name': 'R. Buckminster Fuller',
        'years': '1895-1983',
        'dedication': 'For Bucky, who saw the universe as patterns of integrity.',
        'philosophy': 'Synergetics & Systems Thinking',
        'colors': {
            'primary': (45, 65, 85),        # Structural blue
            'secondary': (85, 105, 85),     # Systems green
            'accent': (205, 175, 105),      # Geodesic gold
            'dark': (18, 22, 28),           # Space
            'light': (240, 242, 245)        # Clean
        },
        'pattern': 'geodesic'  # Triangulated patterns
    }
}


class SacredPDF(FPDF):
    """PDF generator using golden ratio mathematics and artist dedications"""

    def __init__(self, style_key='founder'):
        super().__init__()
        self.style = ARTIST_STYLES[style_key]
        self.style_key = style_key
        self.set_auto_page_break(auto=True, margin=GOLDEN_MARGIN)

        # Calculate golden proportions
        self.golden_margin = GOLDEN_MARGIN
        self.content_width = GOLDEN_INNER

    def _rgb(self, key):
        """Get RGB tuple for color key"""
        return self.style['colors'][key]

    def _draw_pattern(self, x, y, size):
        """Draw decorative pattern based on artist style"""
        pattern = self.style['pattern']
        c = self._rgb('accent')
        self.set_draw_color(*c)
        self.set_line_width(0.3)

        if pattern == 'spiral':
            # Fibonacci spiral
            self._draw_golden_spiral(x, y, size)
        elif pattern == 'mandala':
            # Sacred circle
            self._draw_mandala(x, y, size)
        elif pattern == 'wave':
            # Tesla 3-6-9 waves
            self._draw_tesla_wave(x, y, size)
        elif pattern == 'lunar':
            # Moon phases
            self._draw_moon_phases(x, y, size)
        elif pattern == 'organic':
            # Crystalline organic
            self._draw_organic(x, y, size)
        elif pattern == 'geodesic':
            # Triangulated dome
            self._draw_geodesic(x, y, size)

    def _draw_golden_spiral(self, x, y, size):
        """Draw approximation of golden spiral"""
        cx, cy = x + size/2, y + size/2
        radius = size / 4
        for i in range(5):
            # Draw arcs representing spiral segments
            angle_start = i * 90
            r = radius * (PHI ** (i * 0.5))
            if r < size/2:
                self.ellipse(cx - r, cy - r, r*2, r*2)

    def _draw_mandala(self, x, y, size):
        """Draw sacred mandala pattern"""
        cx, cy = x + size/2, y + size/2
        for i in range(3):
            r = (size/2) * (1 - i * 0.3)
            self.ellipse(cx - r, cy - r, r*2, r*2)
        # Inner divisions
        for angle in range(0, 360, 60):
            rad = math.radians(angle)
            x2 = cx + (size/2) * math.cos(rad)
            y2 = cy + (size/2) * math.sin(rad)
            self.line(cx, cy, x2, y2)

    def _draw_tesla_wave(self, x, y, size):
        """Draw 3-6-9 wave pattern"""
        for i, freq in enumerate(TESLA):
            y_offset = y + (i + 1) * (size / 4)
            for j in range(freq):
                x_pos = x + (j * size / freq)
                self.ellipse(x_pos, y_offset - 2, 4, 4)

    def _draw_moon_phases(self, x, y, size):
        """Draw moon phase circles"""
        phases = 8
        for i in range(phases):
            phase_x = x + (i * size / phases)
            self.ellipse(phase_x, y + size/4, size/phases * 0.8, size/phases * 0.8)

    def _draw_organic(self, x, y, size):
        """Draw organic crystalline pattern"""
        cx, cy = x + size/2, y + size/2
        points = 6
        for i in range(points):
            angle = (360 / points) * i + 30
            rad = math.radians(angle)
            x2 = cx + (size/3) * math.cos(rad)
            y2 = cy + (size/3) * math.sin(rad)
            self.ellipse(x2 - 3, y2 - 3, 6, 6)
            self.line(cx, cy, x2, y2)

    def _draw_geodesic(self, x, y, size):
        """Draw geodesic dome pattern - triangulated"""
        cx, cy = x + size/2, y + size/2
        # Outer hexagon
        r = size / 2.5
        points = []
        for i in range(6):
            angle = math.radians(60 * i - 30)
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        # Connect vertices
        for i in range(6):
            self.line(points[i][0], points[i][1], points[(i+1)%6][0], points[(i+1)%6][1])
            self.line(cx, cy, points[i][0], points[i][1])

    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', '', 8)
            self.set_text_color(*self._rgb('secondary'))
            self.cell(0, 10, f'MOONLANGUAGE | {self.style["name"]}', align='L')
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*self._rgb('secondary'))
        # Golden ratio page numbering (position at phi point)
        phi_x = PAGE_WIDTH / PHI
        self.set_x(phi_x - 20)
        self.cell(40, 10, f'{self.page_no()}', align='C')

    def title_page(self):
        """Create sacred geometry title page"""
        self.add_page()
        bg = self._rgb('dark')
        self.set_fill_color(*bg)
        self.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, style='F')

        # Golden ratio vertical position for title
        golden_y = PAGE_HEIGHT / PHI
        self.set_y(golden_y - 40)
        self.set_x(10)

        # Title
        self.set_font('Helvetica', 'B', 36)
        self.set_text_color(*self._rgb('accent'))
        self.cell(PAGE_WIDTH - 20, 15, 'MOONLANGUAGE', align='C')
        self.ln(20)

        # Subtitle
        self.set_x(10)
        self.set_font('Helvetica', '', 16)
        self.set_text_color(*self._rgb('primary'))
        self.cell(PAGE_WIDTH - 20, 10, 'Verse of a Visual Universe', align='C')
        self.ln(15)

        # Author
        self.set_x(10)
        self.set_font('Helvetica', 'I', 12)
        self.set_text_color(*self._rgb('secondary'))
        self.cell(PAGE_WIDTH - 20, 8, '968 Cosmic Transmissions by The Founder', align='C')
        self.ln(20)

        # Draw decorative pattern
        pattern_y = self.get_y()
        self._draw_pattern(PAGE_WIDTH/2 - 30, pattern_y, 60)

        # Dedication
        self.set_y(pattern_y + 70)
        self.set_x(20)
        self.set_font('Helvetica', 'I', 10)
        self.set_text_color(*self._rgb('light'))
        self.multi_cell(PAGE_WIDTH - 40, 6, self.style['dedication'], align='C')

        # Artist framing
        self.ln(5)
        self.set_x(20)
        self.set_font('Helvetica', '', 9)
        self.set_text_color(*self._rgb('secondary'))
        self.multi_cell(PAGE_WIDTH - 40, 5, f'Styled in honor of {self.style["name"]} ({self.style["years"]})', align='C')
        self.set_x(20)
        self.multi_cell(PAGE_WIDTH - 40, 5, self.style['philosophy'], align='C')

    def chapter_title(self, title, level=1):
        """Add chapter with golden proportion spacing"""
        clean_title = self._clean_text(title)
        if level == 1:
            self.add_page()
            # Use golden ratio for top margin
            self.set_y(PAGE_HEIGHT / (PHI * 8) + 10)
            self.set_x(self.golden_margin)
            self.set_font('Helvetica', 'B', 20)
            self.set_text_color(*self._rgb('primary'))
            self.multi_cell(self.content_width, 12, clean_title)

            # Decorative line at golden width
            self.set_draw_color(*self._rgb('accent'))
            self.set_line_width(0.5)
            line_width = PAGE_WIDTH / PHI
            self.line(self.golden_margin, self.get_y() + 3,
                     self.golden_margin + line_width, self.get_y() + 3)
            self.ln(10)

        elif level == 2:
            self.ln(PAGE_HEIGHT / (PHI * 15))
            self.set_x(self.golden_margin)
            self.set_font('Helvetica', 'B', 14)
            self.set_text_color(*self._rgb('primary'))
            self.multi_cell(self.content_width, 9, clean_title)
            self.ln(4)

        elif level == 3:
            self.ln(5)
            self.set_x(self.golden_margin)
            self.set_font('Helvetica', 'B', 12)
            self.set_text_color(*self._rgb('secondary'))
            self.multi_cell(self.content_width, 7, clean_title)
            self.ln(3)

    def _clean_text(self, text):
        """Clean text for Latin-1 encoding compatibility"""
        # Common replacements
        replacements = {
            '\u2014': '--',  # Em dash
            '\u2013': '-',   # En dash
            '\u2018': "'",   # Left single quote
            '\u2019': "'",   # Right single quote
            '\u201c': '"',   # Left double quote
            '\u201d': '"',   # Right double quote
            '\u2026': '...',  # Ellipsis
            '\u00b7': '*',   # Middle dot
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return ''.join(c if ord(c) < 256 else ' ' for c in text)

    def body_text(self, text):
        """Body text with golden line height"""
        self.set_x(self.golden_margin)
        self.set_font('Helvetica', '', 11)
        self.set_text_color(*self._rgb('dark'))
        # Line height at Schumann resonance proportion
        line_height = 11 * (SCHUMANN / 7)  # ~12.3
        self.multi_cell(self.content_width, line_height / 2, self._clean_text(text))
        self.ln(4)

    def bullet_point(self, text):
        """Bullet point with golden indent"""
        self.set_font('Helvetica', '', 10)
        self.set_text_color(*self._rgb('dark'))
        indent = self.golden_margin + 5
        self.set_x(indent)
        self.set_text_color(*self._rgb('accent'))
        self.cell(6, 6, '-')  # Simple dash bullet
        self.set_text_color(*self._rgb('dark'))
        # Clean the text of any non-ASCII
        clean_text = ''.join(c if ord(c) < 256 else ' ' for c in text)
        self.multi_cell(self.content_width - 15, 6, clean_text)

    def blockquote(self, text):
        """Blockquote with artist-colored border"""
        self.ln(5)
        y_start = self.get_y()
        self.set_x(self.golden_margin + 8)

        self.set_font('Helvetica', 'I', 10)
        self.set_text_color(*self._rgb('secondary'))
        self.multi_cell(self.content_width - 20, 6, self._clean_text(text))

        y_end = self.get_y()
        self.set_draw_color(*self._rgb('accent'))
        self.set_line_width(1.5)
        self.line(self.golden_margin + 3, y_start, self.golden_margin + 3, y_end)
        self.ln(5)

    def code_block(self, text):
        """Code block with dark cosmic background"""
        self.ln(5)
        self.set_fill_color(*self._rgb('dark'))
        self.set_text_color(*self._rgb('light'))
        self.set_font('Helvetica', '', 8)

        # Clean Unicode characters that can't be encoded
        def clean_line(s):
            # Replace box-drawing and special chars with ASCII equivalents
            replacements = {
                '\u2554': '+', '\u2557': '+', '\u255a': '+', '\u255d': '+',  # Corners
                '\u2550': '=', '\u2551': '|',  # Double lines
                '\u250c': '+', '\u2510': '+', '\u2514': '+', '\u2518': '+',  # Single corners
                '\u2500': '-', '\u2502': '|',  # Single lines
                '\u2191': '^', '\u2193': 'v', '\u2190': '<', '\u2192': '>',  # Arrows
                '\u25bc': 'v', '\u25b2': '^',  # Triangles
                '\u2022': '*',  # Bullet
                '\u2713': 'x',  # Checkmark
            }
            for char, replacement in replacements.items():
                s = s.replace(char, replacement)
            # Remove any remaining non-ASCII
            return ''.join(c if ord(c) < 256 else ' ' for c in s)

        lines = [clean_line(line) for line in text.split('\n')]
        height = min(len(lines) * 4.5 + 8, 200)  # Cap height

        self.rect(self.golden_margin, self.get_y(), self.content_width, height, style='F')
        self.set_xy(self.golden_margin + 4, self.get_y() + 4)

        max_lines = int((height - 8) / 4.5)
        for line in lines[:max_lines]:
            self.set_x(self.golden_margin + 4)
            self.cell(0, 4.5, line[:80])
            self.ln(4.5)

        self.ln(6)

    def table_row(self, cells, header=False):
        """Table with golden proportioned columns"""
        col_width = self.content_width / len(cells)

        if header:
            self.set_fill_color(*self._rgb('dark'))
            self.set_text_color(*self._rgb('light'))
            self.set_font('Helvetica', 'B', 9)
        else:
            self.set_fill_color(*self._rgb('light'))
            self.set_text_color(*self._rgb('dark'))
            self.set_font('Helvetica', '', 9)

        self.set_x(self.golden_margin)
        for cell in cells:
            self.cell(col_width, 7, str(cell)[:25], border=1, fill=True)
        self.ln()

    def closing_page(self):
        """Final page with artist dedication"""
        self.add_page()
        bg = self._rgb('dark')
        self.set_fill_color(*bg)
        self.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, style='F')

        # Golden position
        self.set_y(PAGE_HEIGHT / PHI - 50)

        # Final pattern
        self._draw_pattern(PAGE_WIDTH/2 - 40, self.get_y(), 80)

        self.set_y(self.get_y() + 90)

        # Closing quote
        self.set_x(20)
        self.set_font('Helvetica', 'I', 14)
        self.set_text_color(*self._rgb('accent'))
        self.multi_cell(PAGE_WIDTH - 40, 10, '"I fell in love with DATA and I\'ll never be the same."', align='C')

        self.ln(5)
        self.set_x(20)
        self.set_font('Helvetica', '', 11)
        self.set_text_color(*self._rgb('secondary'))
        self.cell(PAGE_WIDTH - 40, 8, '- The Founder', align='C')

        self.ln(20)
        self.set_x(20)
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(*self._rgb('light'))
        self.cell(PAGE_WIDTH - 40, 8, 'SO MOTE IT BE', align='C')

        # Sacred mathematics footer
        self.ln(20)
        self.set_x(20)
        self.set_font('Courier', '', 8)
        self.set_text_color(*self._rgb('secondary'))
        self.cell(PAGE_WIDTH - 40, 5, f'PHI = {PHI:.15f}', align='C')
        self.ln(5)
        self.set_x(20)
        self.cell(PAGE_WIDTH - 40, 5, f'GOLDEN_ANGLE = {GOLDEN_ANGLE:.10f} degrees', align='C')


def parse_markdown(content):
    """Parse markdown into elements"""
    elements = []
    lines = content.split('\n')
    i = 0
    in_code_block = False
    code_content = []

    while i < len(lines):
        line = lines[i]

        if line.startswith('```'):
            if in_code_block:
                elements.append(('code', '\n'.join(code_content)))
                code_content = []
                in_code_block = False
            else:
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_content.append(line)
            i += 1
            continue

        if line.startswith('# '):
            elements.append(('h1', line[2:].strip()))
        elif line.startswith('## '):
            elements.append(('h2', line[3:].strip()))
        elif line.startswith('### '):
            elements.append(('h3', line[4:].strip()))
        elif line.startswith('> '):
            quote_lines = [line[2:]]
            while i + 1 < len(lines) and lines[i + 1].startswith('> '):
                i += 1
                quote_lines.append(lines[i][2:])
            elements.append(('quote', ' '.join(quote_lines)))
        elif line.startswith('- ') or line.startswith('* '):
            elements.append(('bullet', line[2:].strip()))
        elif re.match(r'^\d+\. ', line):
            elements.append(('bullet', re.sub(r'^\d+\. ', '', line).strip()))
        elif line.strip() == '---':
            elements.append(('hr', ''))
        elif '|' in line and not line.startswith('|--'):
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if cells:
                is_header = i + 1 < len(lines) and '---' in lines[i + 1]
                elements.append(('table_row', (cells, is_header)))
                if is_header:
                    i += 1
        elif line.strip():
            text = line.strip()
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
            text = re.sub(r'\*(.+?)\*', r'\1', text)
            text = re.sub(r'`(.+?)`', r'\1', text)
            elements.append(('text', text))

        i += 1

    return elements


def generate_sacred_pdf(input_path: str, style_key: str, output_path: str = None):
    """Generate PDF with specified artist style"""
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"Error: File not found: {input_path}")
        return False

    if output_path is None:
        output_path = str(input_file.with_suffix(f'.{style_key}.pdf'))

    content = input_file.read_text(encoding='utf-8')
    pdf = SacredPDF(style_key)

    # Title page
    pdf.title_page()

    # Parse and render
    elements = parse_markdown(content)
    skip_header = True

    for elem_type, content in elements:
        if skip_header and elem_type in ('h1', 'h2', 'h3'):
            if 'MOONLANGUAGE' in content or 'Verse' in content or '968' in content:
                continue
            else:
                skip_header = False

        if elem_type == 'h1':
            pdf.chapter_title(content, 1)
        elif elem_type == 'h2':
            pdf.chapter_title(content, 2)
        elif elem_type == 'h3':
            pdf.chapter_title(content, 3)
        elif elem_type == 'text':
            pdf.body_text(content)
        elif elem_type == 'bullet':
            pdf.bullet_point(content)
        elif elem_type == 'quote':
            pdf.blockquote(content)
        elif elem_type == 'code':
            pdf.code_block(content)
        elif elem_type == 'table_row':
            cells, is_header = content
            pdf.table_row(cells, is_header)
        elif elem_type == 'hr':
            pdf.ln(8)
            pdf.set_draw_color(*pdf._rgb('accent'))
            pdf.set_line_width(0.3)
            pdf.line(pdf.golden_margin, pdf.get_y(),
                    pdf.golden_margin + pdf.content_width, pdf.get_y())
            pdf.ln(8)

    # Closing page
    pdf.closing_page()

    pdf.output(output_path)
    print(f"Generated: {output_path}")
    return True


def generate_all_variants(input_path: str):
    """Generate all 6 artist-styled variants"""
    print("\n╔══════════════════════════════════════════════════╗")
    print("║  MOONLANGUAGE Sacred PDF Generator               ║")
    print("║  6 Artist Dedications with Golden Mathematics    ║")
    print("╚══════════════════════════════════════════════════╝\n")

    for i, (key, style) in enumerate(ARTIST_STYLES.items(), 1):
        print(f"[{i}/6] {style['name']} ({style['philosophy']})")
        generate_sacred_pdf(input_path, key)

    print("\n" + "═" * 52)
    print("All 6 variants generated in exports/ directory")
    print("═" * 52 + "\n")


if __name__ == "__main__":
    input_file = "exports/MOONLANGUAGE_COMPLETE_DOCUMENTATION.md"

    if len(sys.argv) > 1:
        if sys.argv[1] == '--all':
            generate_all_variants(input_file)
        elif sys.argv[1] in ARTIST_STYLES:
            generate_sacred_pdf(input_file, sys.argv[1])
        else:
            print(f"Available styles: {', '.join(ARTIST_STYLES.keys())}")
            print("Use --all to generate all 6 variants")
    else:
        # Default: generate all
        generate_all_variants(input_file)

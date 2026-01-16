#!/usr/bin/env python3
"""
MOONLANGUAGE PDF Export
Converts markdown documentation to elegantly styled PDF using fpdf2
Pure Python - no system dependencies required
"""

import sys
import re
from pathlib import Path
from fpdf import FPDF


class MoonLanguagePDF(FPDF):
    """Custom PDF class with MOONLANGUAGE styling"""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', '', 8)
            self.set_text_color(154, 150, 144)
            self.cell(0, 10, 'MOONLANGUAGE', align='L')
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(154, 150, 144)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def title_page(self, title, subtitle, author):
        """Create elegant title page"""
        self.add_page()
        self.ln(60)

        # Main title
        self.set_font('Helvetica', 'B', 36)
        self.set_text_color(26, 26, 26)
        self.multi_cell(0, 15, title, align='C')
        self.ln(5)

        # Subtitle
        self.set_font('Helvetica', '', 16)
        self.set_text_color(212, 165, 116)  # Gold
        self.multi_cell(0, 10, subtitle, align='C')
        self.ln(5)

        # Author
        self.set_font('Helvetica', 'I', 14)
        self.set_text_color(90, 90, 90)
        self.multi_cell(0, 10, author, align='C')
        self.ln(30)

        # Decorative line
        self.set_draw_color(212, 165, 116)
        self.set_line_width(0.5)
        x = self.w / 2 - 30
        self.line(x, self.get_y(), x + 60, self.get_y())

    def chapter_title(self, title, level=1):
        """Add chapter/section title"""
        if level == 1:
            self.add_page()
            self.ln(10)
            self.set_font('Helvetica', 'B', 20)
            self.set_text_color(26, 26, 26)
            self.multi_cell(0, 12, title)
            # Gold underline
            self.set_draw_color(212, 165, 116)
            self.set_line_width(0.3)
            self.line(10, self.get_y() + 2, 100, self.get_y() + 2)
            self.ln(8)
        elif level == 2:
            self.ln(8)
            self.set_font('Helvetica', 'B', 14)
            self.set_text_color(58, 58, 58)
            self.multi_cell(0, 10, title)
            self.ln(3)
        elif level == 3:
            self.ln(5)
            self.set_font('Helvetica', 'B', 12)
            self.set_text_color(74, 74, 74)
            self.multi_cell(0, 8, title)
            self.ln(2)

    def body_text(self, text):
        """Add body text"""
        self.set_font('Helvetica', '', 11)
        self.set_text_color(42, 42, 42)
        self.multi_cell(0, 6, text)
        self.ln(3)

    def bullet_point(self, text, indent=0):
        """Add bullet point"""
        self.set_font('Helvetica', '', 10)
        self.set_text_color(42, 42, 42)
        x = 15 + (indent * 5)
        self.set_x(x)
        self.cell(5, 6, chr(149))  # Bullet character
        self.multi_cell(0, 6, text)

    def code_block(self, text):
        """Add code block with dark background"""
        self.ln(3)
        self.set_fill_color(14, 14, 24)  # Dark cosmic
        self.set_text_color(240, 236, 231)  # Warm white
        self.set_font('Courier', '', 9)

        # Calculate height needed
        lines = text.split('\n')
        height = len(lines) * 5 + 6

        self.rect(10, self.get_y(), self.w - 20, height, style='F')
        self.set_xy(12, self.get_y() + 3)

        for line in lines:
            self.set_x(12)
            self.cell(0, 5, line[:100])  # Truncate long lines
            self.ln(5)

        self.ln(5)
        self.set_text_color(42, 42, 42)

    def blockquote(self, text):
        """Add blockquote with gold left border"""
        self.ln(3)
        self.set_draw_color(212, 165, 116)
        self.set_line_width(1)
        y_start = self.get_y()

        self.set_x(15)
        self.set_font('Helvetica', 'I', 10)
        self.set_text_color(90, 90, 90)
        self.multi_cell(self.w - 30, 6, text)

        y_end = self.get_y()
        self.line(12, y_start, 12, y_end)
        self.ln(3)

    def table_row(self, cells, header=False):
        """Add table row"""
        col_width = (self.w - 20) / len(cells)

        if header:
            self.set_fill_color(14, 14, 24)
            self.set_text_color(240, 236, 231)
            self.set_font('Helvetica', 'B', 9)
        else:
            self.set_fill_color(249, 249, 249)
            self.set_text_color(42, 42, 42)
            self.set_font('Helvetica', '', 9)

        for cell in cells:
            self.cell(col_width, 8, str(cell)[:30], border=1, fill=True)
        self.ln()


def parse_markdown(content):
    """Parse markdown content into structured elements"""
    elements = []
    lines = content.split('\n')
    i = 0
    in_code_block = False
    code_content = []

    while i < len(lines):
        line = lines[i]

        # Code blocks
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

        # Headers
        if line.startswith('# '):
            elements.append(('h1', line[2:].strip()))
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
        # Bullet points
        elif line.startswith('- ') or line.startswith('* '):
            elements.append(('bullet', line[2:].strip()))
        # Numbered lists
        elif re.match(r'^\d+\. ', line):
            elements.append(('bullet', re.sub(r'^\d+\. ', '', line).strip()))
        # Horizontal rules
        elif line.strip() == '---':
            elements.append(('hr', ''))
        # Tables (simplified)
        elif '|' in line and not line.startswith('|--'):
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if cells:
                is_header = i + 1 < len(lines) and '---' in lines[i + 1]
                elements.append(('table_row', (cells, is_header)))
                if is_header:
                    i += 1  # Skip separator line
        # Regular text
        elif line.strip():
            # Clean markdown formatting
            text = line.strip()
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
            text = re.sub(r'\*(.+?)\*', r'\1', text)  # Italic
            text = re.sub(r'`(.+?)`', r'\1', text)  # Inline code
            elements.append(('text', text))

        i += 1

    return elements


def convert_markdown_to_pdf(input_path: str, output_path: str = None):
    """Convert markdown file to styled PDF"""

    input_file = Path(input_path)
    if not input_file.exists():
        print(f"Error: File not found: {input_path}")
        return False

    if output_path is None:
        output_path = str(input_file.with_suffix('.pdf'))

    # Read markdown
    content = input_file.read_text(encoding='utf-8')

    # Create PDF
    pdf = MoonLanguagePDF()

    # Title page
    pdf.title_page(
        "MOONLANGUAGE",
        "Verse of a Visual Universe",
        "968 Cosmic Transmissions by The Founder"
    )

    # Parse and render content
    elements = parse_markdown(content)

    # Skip first few elements that were already in title
    skip_title = True

    for elem_type, content in elements:
        if skip_title and elem_type in ('h1', 'h2', 'h3'):
            if 'MOONLANGUAGE' in content or 'Verse' in content or '968' in content:
                continue
            else:
                skip_title = False

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
            pdf.ln(5)
            pdf.set_draw_color(212, 165, 116)
            pdf.set_line_width(0.3)
            pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())
            pdf.ln(5)

    # Save
    pdf.output(output_path)
    print(f"PDF generated: {output_path}")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default to MOONLANGUAGE documentation
        input_file = "exports/MOONLANGUAGE_COMPLETE_DOCUMENTATION.md"
        output_file = "exports/MOONLANGUAGE_COMPLETE_DOCUMENTATION.pdf"
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None

    convert_markdown_to_pdf(input_file, output_file)

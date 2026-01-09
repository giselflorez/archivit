#!/usr/bin/env python3
"""
Press Kit Generator
Generates professional press kit PDFs with WEB3GISEL branding and XMP metadata
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import WeasyPrint
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    HTML = None
    CSS = None
    logger.warning(f"WeasyPrint not available - PDF generation disabled: {e}")


class PressKitGenerator:
    """Generate professional press kit PDFs"""

    # Brand names for XMP metadata
    BRAND_NAMES = [
        "WEB3GISEL",
        "WEB3PHOTO",
        "GISEL FLOREZ",
        "GISELX",
        "GISELXFLOREZ"
    ]

    def __init__(self):
        self.output_dir = Path("exports/press_kits")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.template_dir = Path(__file__).parent / "templates"

    def is_available(self) -> bool:
        """Check if press kit generation is available"""
        return WEASYPRINT_AVAILABLE

    def generate_html(
        self,
        title: str,
        description: str,
        works: List[Dict],
        artist_bio: str = None,
        contact_info: Dict = None
    ) -> str:
        """
        Generate HTML for press kit

        Args:
            title: Press kit title
            description: Press kit description
            works: List of work dicts with keys: title, description, image_path, date, tags
            artist_bio: Artist biography
            contact_info: Contact information dict

        Returns:
            HTML string
        """
        # WEB3GISEL branded template
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - WEB3GISEL Press Kit</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@300;400;600&family=Work+Sans:wght@300;400;500&display=swap');

        :root {{
            --color-primary: #0a0a0a;
            --color-secondary: #1a1a1a;
            --color-accent: #d4a574;
            --color-text: #faf8f5;
            --color-text-muted: #b8b5b0;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Work Sans', sans-serif;
            line-height: 1.6;
            color: var(--color-text);
            background: var(--color-primary);
            font-size: 10pt;
        }}

        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 40px;
        }}

        .header {{
            text-align: center;
            margin-bottom: 60px;
            border-bottom: 1px solid var(--color-accent);
            padding-bottom: 30px;
        }}

        .brand-logo {{
            font-family: 'Crimson Pro', serif;
            font-size: 32pt;
            font-weight: 300;
            letter-spacing: 0.1em;
            margin-bottom: 10px;
        }}

        .brand-logo strong {{
            font-weight: 600;
            color: var(--color-accent);
        }}

        .subtitle {{
            font-size: 9pt;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            color: var(--color-text-muted);
        }}

        .press-kit-title {{
            font-family: 'Crimson Pro', serif;
            font-size: 24pt;
            font-weight: 400;
            margin: 40px 0 20px;
        }}

        .description {{
            font-size: 10pt;
            line-height: 1.8;
            margin-bottom: 40px;
            color: var(--color-text-muted);
        }}

        .section {{
            margin: 40px 0;
            page-break-inside: avoid;
        }}

        .section-title {{
            font-family: 'Crimson Pro', serif;
            font-size: 16pt;
            font-weight: 600;
            margin-bottom: 20px;
            color: var(--color-accent);
        }}

        .work {{
            margin-bottom: 40px;
            page-break-inside: avoid;
        }}

        .work-image {{
            width: 100%;
            height: auto;
            margin-bottom: 15px;
            border: 1px solid #2a2a2a;
        }}

        .work-title {{
            font-family: 'Crimson Pro', serif;
            font-size: 14pt;
            font-weight: 600;
            margin-bottom: 5px;
        }}

        .work-date {{
            font-size: 8pt;
            color: var(--color-text-muted);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 10px;
        }}

        .work-description {{
            font-size: 9pt;
            line-height: 1.6;
            color: var(--color-text-muted);
            margin-bottom: 10px;
        }}

        .work-tags {{
            font-size: 8pt;
            color: var(--color-accent);
        }}

        .bio {{
            font-size: 10pt;
            line-height: 1.8;
            margin: 20px 0;
        }}

        .contact {{
            font-size: 9pt;
            line-height: 1.8;
            margin: 20px 0;
        }}

        .footer {{
            margin-top: 60px;
            padding-top: 30px;
            border-top: 1px solid #2a2a2a;
            text-align: center;
            font-size: 8pt;
            color: var(--color-text-muted);
        }}

        .copyright {{
            font-size: 7pt;
            color: var(--color-text-muted);
            margin-top: 20px;
        }}

        @media print {{
            body {{
                background: white;
                color: black;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header with WEB3GISEL Branding -->
        <div class="header">
            <div class="brand-logo"><strong>WEB3GISEL</strong></div>
            <div class="subtitle">Digital Art & Photography Archive</div>
        </div>

        <!-- Press Kit Title -->
        <h1 class="press-kit-title">{title}</h1>

        <!-- Description -->
        <div class="description">
            {description}
        </div>

        <!-- Selected Works -->
        <div class="section">
            <h2 class="section-title">Selected Works</h2>
"""

        # Add works
        for work in works:
            work_title = work.get('title', 'Untitled')
            work_desc = work.get('description', '')
            work_date = work.get('date', '')
            work_tags = work.get('tags', [])
            work_image = work.get('image_path', '')

            html += f"""
            <div class="work">
                <img src="{work_image}" alt="{work_title}" class="work-image">
                <div class="work-title">{work_title}</div>
                <div class="work-date">{work_date}</div>
                <div class="work-description">{work_desc}</div>
                <div class="work-tags">{' • '.join(work_tags)}</div>
            </div>
"""

        # Add artist bio if provided
        if artist_bio:
            html += f"""
        </div>

        <!-- Artist Bio -->
        <div class="section">
            <h2 class="section-title">About the Artist</h2>
            <div class="bio">{artist_bio}</div>
        </div>
"""

        # Add contact info if provided
        if contact_info:
            contact_lines = []
            if contact_info.get('email'):
                contact_lines.append(f"Email: {contact_info['email']}")
            if contact_info.get('website'):
                contact_lines.append(f"Website: {contact_info['website']}")
            if contact_info.get('social'):
                contact_lines.append(f"Social: {contact_info['social']}")

            html += f"""
        <div class="section">
            <h2 class="section-title">Contact</h2>
            <div class="contact">
                {"<br>".join(contact_lines)}
            </div>
        </div>
"""

        # Footer with copyright
        html += f"""
        <!-- Footer -->
        <div class="footer">
            <div>WEB3GISEL Press Kit — {datetime.now().year}</div>
            <div class="copyright">
                © {datetime.now().year} WEB3GISEL / WEB3PHOTO / GISEL FLOREZ. All rights reserved.<br>
                This press kit and all images are for editorial use only.
            </div>
        </div>
    </div>
</body>
</html>
"""

        return html

    def generate_pdf(
        self,
        title: str,
        description: str,
        works: List[Dict],
        artist_bio: str = None,
        contact_info: Dict = None,
        output_filename: str = None
    ) -> Optional[Path]:
        """
        Generate PDF press kit

        Args:
            title: Press kit title
            description: Description
            works: List of works
            artist_bio: Artist biography
            contact_info: Contact information
            output_filename: Output filename (optional)

        Returns:
            Path to generated PDF or None if failed
        """
        if not self.is_available():
            logger.error("WeasyPrint not available - cannot generate PDF")
            return None

        # Generate HTML
        html_content = self.generate_html(
            title, description, works, artist_bio, contact_info
        )

        # Output filename
        if not output_filename:
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"{safe_title}_{timestamp}.pdf"

        output_path = self.output_dir / output_filename

        try:
            logger.info(f"Generating PDF: {output_path}")

            # Generate PDF with WeasyPrint
            HTML(string=html_content).write_pdf(output_path)

            logger.info(f"PDF generated successfully: {output_path}")

            # Embed XMP metadata
            self._embed_xmp_metadata(output_path)

            return output_path

        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return None

    def _embed_xmp_metadata(self, pdf_path: Path):
        """
        Embed XMP metadata with brand names using exiftool

        Args:
            pdf_path: Path to PDF file
        """
        try:
            # Check if exiftool is installed
            result = subprocess.run(['which', 'exiftool'], capture_output=True)

            if result.returncode != 0:
                logger.warning("exiftool not installed - skipping XMP metadata embedding")
                logger.warning("Install with: brew install exiftool (macOS) or apt-get install libimage-exiftool-perl (Linux)")
                return

            # Build metadata commands
            metadata_args = [
                'exiftool',
                '-overwrite_original',
                f'-Creator={"WEB3GISEL"}',
                f'-Rights=© {datetime.now().year} WEB3GISEL / WEB3PHOTO / GISEL FLOREZ. All rights reserved.',
                f'-Copyright=© {datetime.now().year} WEB3GISEL / WEB3PHOTO / GISEL FLOREZ',
                f'-Author=GISEL FLOREZ (GISELX / GISELXFLOREZ)',
                f'-Subject=WEB3GISEL Press Kit',
                f'-Keywords={", ".join(self.BRAND_NAMES)}',
                str(pdf_path)
            ]

            # Run exiftool
            result = subprocess.run(metadata_args, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("XMP metadata embedded successfully")
            else:
                logger.warning(f"exiftool warning: {result.stderr}")

        except Exception as e:
            logger.error(f"Error embedding XMP metadata: {e}")


# Test interface
if __name__ == '__main__':
    generator = PressKitGenerator()

    if not generator.is_available():
        print("WeasyPrint not installed!")
        print("Install with: pip install weasyprint")
        exit(1)

    # Test PDF generation
    test_works = [
        {
            'title': 'Digital Landscape #1',
            'description': 'An exploration of digital spaces and virtual environments.',
            'date': '2025',
            'tags': ['digital art', 'landscape', 'nft'],
            'image_path': 'https://via.placeholder.com/800x600'
        },
        {
            'title': 'Portrait Study',
            'description': 'Contemporary portrait exploring identity in the digital age.',
            'date': '2025',
            'tags': ['portrait', 'photography', 'nft'],
            'image_path': 'https://via.placeholder.com/800x600'
        }
    ]

    pdf_path = generator.generate_pdf(
        title="Featured Works 2025",
        description="A curated selection of digital artworks and photography from WEB3GISEL's archive.",
        works=test_works,
        artist_bio="GISEL FLOREZ (GISELX) is a digital artist and photographer working at the intersection of Web3 and visual art.",
        contact_info={
            'email': 'hello@web3gisel.com',
            'website': 'https://web3gisel.com'
        }
    )

    if pdf_path:
        print(f"\nPress kit generated successfully!")
        print(f"Location: {pdf_path}")
    else:
        print("\nFailed to generate press kit")

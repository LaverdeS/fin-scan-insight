import logging
import tempfile

import markdown2
import re
from pathlib import Path
from PIL import Image
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from PyPDF2 import PdfMerger
from weasyprint import HTML


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def generate_report_with_images(md_file, img_dir='input_images'):
    """
    Generate a report from a Markdown file, converting it to HTML and PDF,
    and including images referenced in the Markdown.
    """
    final_pdf = Path(md_file).with_suffix('.pdf')

    with open(md_file, 'r', encoding='utf-8') as f:
        md_text = f.read()
    html_content = markdown2.markdown(md_text)

    with tempfile.TemporaryDirectory() as tmpdir:
        text_pdf = Path(tmpdir) / "text_only_report.pdf"
        image_pdf = Path(tmpdir) / "images_only_report.pdf"

        # Convert HTML to PDF (text report)
        HTML(string=html_content).write_pdf(str(text_pdf))

        # Extract referenced images
        referenced_images = sorted(set(re.findall(r"page_\d+\.png", md_text)))
        logging.info(f"referenced image filenames: {referenced_images}")

        # Create images-only PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=10)
        img_dir = Path(img_dir)

        for img_name in referenced_images:
            img_path = img_dir / img_name
            if img_path.exists():
                with Image.open(img_path) as img:
                    img_w, img_h = img.size
                pdf.add_page()
                pdf.set_font("helvetica", size=12)
                pdf.cell(0, 10, f"Image: {img_name}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                max_w = 190
                scale = max_w / img_w
                pdf.image(str(img_path), x=10, y=25, w=max_w, h=img_h * scale)
            else:
                logging.warning(f"Image not found: {img_path}")

        pdf.output(str(image_pdf))
        logging.debug(f"✅ image PDF saved as temporary file: {image_pdf}")

        # Merge text and images PDFs
        merger = PdfMerger()
        merger.append(str(text_pdf))
        merger.append(str(image_pdf))
        merger.write(str(final_pdf))
        merger.close()

    logging.info(f"✅ final report with images saved as: {final_pdf}")


if __name__ == "__main__":
    generate_report_with_images("report_full_context_gemini-1.5-pro_v1.md")
import pytest
from src.ingredient_retrieval import Scraper


def test_extract_text_from_pdf():
    scraper = Scraper()
    pdf_content = b'%PDF-1.3\n%\xc4\xe5\xf2\xe5\xeb\xa7\xf3\xa0\xd0\xc4\xc6\n2 0 obj\n<<\n/Type /Page\n/Parent 1 0 R\n/Resources <<\n/Font <<\n/F1 4 0 R \n>>\n>>\n/Contents 3 0 R\n>>\nendobj\n3 0 obj\n<< /Length 72 >>\nstream\nBT\n/F1 24 Tf\n100 100 Td\n(Hello, World!) Tj\nET\nendstream\nendobj\n4 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n/Name /F1\n/BaseFont /Helvetica\n/Encoding /WinAnsiEncoding\n>>\nendobj\n1 0 obj\n<<\n/Type /Pages\n/Kids [2 0 R]\n/Count 1\n>>\nendobj\n5 0 obj\n<<\n/Type /Catalog\n/Pages 1 0 R\n>>\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000301 00000 n \n0000000009 00000 n \n0000000087 00000 n \n0000000210 00000 n \n0000000358 00000 n \ntrailer\n<<\n/Size 6\n/Root 5 0 R\n>>\nstartxref\n407\n%%EOF'
    text = scraper.extract_text_from_pdf(pdf_content)
    assert "Hello, World!" in text


def test_extract_text_from_html():
    scraper = Scraper()
    html = "<html><body><h1>Test Header</h1><p>Test paragraph</p></body></html>"
    text = scraper.extract_text_from_html(html)
    assert "Test Header" in text
    assert "Test paragraph" in text

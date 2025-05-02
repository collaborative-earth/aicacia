import pymupdf

def convert(input_pdf, output_dir) -> tuple[int, int]:
    doc = pymupdf.open(input_pdf)

    height, width = 0, 0

    for page in doc:
        pix = page.get_pixmap(dpi=150)
        pix.save(f"{output_dir}/page-{page.number + 1}.png")
        height = pix.height
        width = pix.width

    return height, width
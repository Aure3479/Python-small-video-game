import cairosvg

def convert_svg_to_png(svg_file, output_file):
    """Convertit un fichier SVG en PNG."""
    cairosvg.svg2png(url=svg_file, write_to=output_file)

def convert_svg_to_jpeg(svg_file, output_file):
    """Convertit un fichier SVG en JPEG."""
    cairosvg.svg2png(url=svg_file, write_to="temp.png")
    from PIL import Image
    with Image.open("temp.png") as img:
        img.convert("RGB").save(output_file, "JPEG")

# Exemple d'utilisation
convert_svg_to_png("lJRBNZ.svg", "background.png")  # Convertit en PNG
convert_svg_to_jpeg("lJRBNZ.svg", "background.jpeg")  # Convertit en JPEG

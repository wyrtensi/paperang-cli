from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    width = 576
    marker_distance_px = 720
    top_y = 80
    bottom_y = top_y + marker_distance_px
    height = bottom_y + 40

    image = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except OSError:
        font = ImageFont.load_default()

    left_x = 32
    right_x = width - 32
    for y in (top_y, bottom_y):
        draw.line((left_x, y, right_x, y), fill=0, width=6)
        draw.polygon([(left_x, y), (left_x + 24, y - 16), (left_x + 24, y + 16)], fill=0)
        draw.polygon([(right_x, y), (right_x - 24, y - 16), (right_x - 24, y + 16)], fill=0)

    draw.text((width // 2 - 78, 24), "P2 CAL 720 px", fill=0, font=font)
    draw.text((width // 2 - 162, bottom_y + 14), "measure vertical tip-to-tip", fill=0, font=font)

    output_path = Path("calibration-strip-p2-720.png")
    image.save(output_path)
    print(output_path.resolve())


if __name__ == "__main__":
    main()

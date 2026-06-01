#!/usr/bin/python3
# -*-coding:utf-8-*-

import numpy as np
import skimage.color, skimage.transform, skimage.filters, skimage.feature
import skimage as ski
import pilkit.processors
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
import numba
import os


FONT_CANDIDATES = {
    "sans": {
        "windows": ["segoeui.ttf", "arial.ttf"],
        "portable": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf"],
    },
    "mono": {
        "windows": ["consola.ttf", "cour.ttf"],
        "portable": ["DejaVuSansMono.ttf", "LiberationMono-Regular.ttf"],
    },
    "serif": {
        "windows": ["georgia.ttf", "times.ttf"],
        "portable": ["DejaVuSerif.ttf", "LiberationSerif-Regular.ttf"],
    },
}


def _pack_block(bits_str: str) -> bytearray:
    # bits_str are human way (MSB:LSB) of representing binary numbers (e.g. "1010" means 12)
    if len(bits_str) % 8 != 0:
        raise ValueError("bits_str should have the length of ")
    partitioned_str = [bits_str[i:i + 8] for i in range(0, len(bits_str), 8)]
    int_str = [int(i, 2) for i in partitioned_str]
    return bytes(int_str)


def _printer_width(printer_width=None):
    return printer_width or 384


def _resample_lanczos():
    if hasattr(Image, "Resampling"):
        return Image.Resampling.LANCZOS
    return Image.LANCZOS


def _load_text_font(font_size, font_family="sans"):
    font_candidates = []
    family = FONT_CANDIDATES.get((font_family or "sans").lower(), FONT_CANDIDATES["sans"])

    windir = os.environ.get("WINDIR")
    if windir:
        font_candidates.extend([os.path.join(windir, "Fonts", candidate) for candidate in family["windows"]])

    font_candidates.extend(family["portable"])
    font_candidates.extend(FONT_CANDIDATES["sans"]["portable"])

    for font_path in font_candidates:
        try:
            return ImageFont.truetype(font_path, font_size)
        except OSError:
            continue

    return ImageFont.load_default(size=font_size)


def _text_bbox(draw, text, font):
    if not text:
        text = " "
    return draw.textbbox((0, 0), text, font=font)


def _text_size(draw, text, font):
    bbox = _text_bbox(draw, text, font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1], bbox


def _split_word_to_width(draw, word, font, max_width):
    pieces = []
    remaining = word

    while remaining:
        split_index = 1
        while split_index <= len(remaining):
            candidate = remaining[:split_index]
            candidate_width, _, _ = _text_size(draw, candidate, font)
            if candidate_width > max_width:
                break
            split_index += 1

        fitted = remaining[: max(1, split_index - 1)]
        pieces.append(fitted)
        remaining = remaining[len(fitted):]

    return pieces


def _wrap_text(draw, text, font, max_width, break_long_words=False):
    paragraphs = text.splitlines() or [text]
    wrapped_lines = []

    for paragraph in paragraphs:
        words = paragraph.split()
        if not words:
            wrapped_lines.append("")
            continue

        current_line = words[0]
        if break_long_words:
            current_width, _, _ = _text_size(draw, current_line, font)
            if current_width > max_width:
                wrapped_lines.extend(_split_word_to_width(draw, current_line, font, max_width))
                current_line = ""

        for word in words[1:]:
            if not current_line:
                if break_long_words:
                    word_width, _, _ = _text_size(draw, word, font)
                    if word_width > max_width:
                        wrapped_lines.extend(_split_word_to_width(draw, word, font, max_width))
                        continue
                current_line = word
                continue

            candidate = f"{current_line} {word}"
            candidate_width, _, _ = _text_size(draw, candidate, font)
            if candidate_width <= max_width:
                current_line = candidate
                continue

            wrapped_lines.append(current_line)
            if break_long_words:
                word_width, _, _ = _text_size(draw, word, font)
                if word_width > max_width:
                    wrapped_lines.extend(_split_word_to_width(draw, word, font, max_width))
                    current_line = ""
                    continue
            current_line = word

        if current_line:
            wrapped_lines.append(current_line)

    return wrapped_lines or [""]


def binimage2bitstream(bin_image: np.ndarray):
    # bin_image is a numpy int array consists of only 1s and 0s
    # input follows thermal printer's mechanism: 1 is black (printed) and 0 is white (left untouched)
    assert bin_image.max() <= 1 and bin_image.min() >= 0
    return _pack_block(''.join(map(str, bin_image.flatten())))


def text2bitstream(text, font_size=36, horizontal_padding=16, vertical_padding=12, printer_width=None):
    printer_width = _printer_width(printer_width)
    message = text if text else " "

    font = _load_text_font(font_size)
    probe_image = Image.new('L', (1, 1), 255)
    probe_draw = ImageDraw.Draw(probe_image)
    max_text_width = max(1, printer_width - horizontal_padding * 2)
    lines = _wrap_text(probe_draw, message, font, max_text_width)

    line_metrics = [_text_size(probe_draw, line, font) for line in lines]
    text_width = max(metric[0] for metric in line_metrics)
    line_height = max(metric[1] for metric in line_metrics)
    line_spacing = max(6, font_size // 4)
    text_height = line_height * len(lines) + line_spacing * max(0, len(lines) - 1)

    image_width = min(printer_width, max(text_width + horizontal_padding * 2, 1))
    image_height = max(text_height + vertical_padding * 2, 1)
    text_image = Image.new('L', (image_width, image_height), 255)
    text_draw = ImageDraw.Draw(text_image)
    current_y = vertical_padding
    for line, (_, _, bbox) in zip(lines, line_metrics):
        text_draw.text(
            (horizontal_padding - bbox[0], current_y - bbox[1]),
            line,
            fill=0,
            font=font,
        )
        current_y += line_height + line_spacing

    canvas = Image.new('L', (printer_width, text_image.height), 255)
    offset_x = max(0, (printer_width - text_image.width) // 2)
    canvas.paste(text_image, (offset_x, 0))

    binary_image = (np.array(canvas) < 128).astype(int)
    return binimage2bitstream(binary_image)


def im2binimage(im, conversion="threshold", printer_width=None):
    # convert standard numpy array image to bin_image
    fixed_width = _printer_width(printer_width)
    if (len(im.shape) != 2):
        im = ski.color.rgb2gray(im)
    im = ski.transform.resize(im, (round( fixed_width /im.shape[1]  * im.shape[0]), fixed_width))
    if conversion == "threshold":
        ret = (im < ski.filters.threshold_li(im)).astype(int)
    elif conversion == "edge":
        ret = 1- (1 - (ski.feature.canny(im, sigma=2)))
    else:
        raise ValueError("Unsupported conversion method")
    return ret

# this is straight from https://github.com/tgray/hyperdither
@numba.jit
def dither(num, thresh = 127):
    derr = np.zeros(num.shape, dtype=int)

    div = 8
    for y in range(num.shape[0]):
        for x in range(num.shape[1]):
            newval = derr[y,x] + num[y,x]
            if newval >= thresh:
                errval = newval - 255
                num[y,x] = 1.
            else:
                errval = newval
                num[y,x] = 0.
            if x + 1 < num.shape[1]:
                derr[y, x + 1] += errval / div
                if x + 2 < num.shape[1]:
                    derr[y, x + 2] += errval / div
            if y + 1 < num.shape[0]:
                derr[y + 1, x - 1] += errval / div
                derr[y + 1, x] += errval / div
                if y + 2< num.shape[0]:
                    derr[y + 2, x] += errval / div
                if x + 1 < num.shape[1]:
                    derr[y + 1, x + 1] += errval / div
    return num[::-1,:] * 255

def im2binimage2(im):
    basewidth = 384
    # resizer = pilkit.processors.ResizeToFit(fixed_width)
    # import in B&W, probably does not matter
    img = Image.open(im).convert('L')
    # img = Image.open(im)
    # img.show()

    wpercent = (basewidth/float(img.size[0]))
    hsize = int((float(img.size[1])*float(wpercent)))
    img = img.resize((basewidth,hsize), Image.ANTIALIAS)
    # img.save('test.pgm', format="PPM")
    # os.system('pamditherbw -atkinson test.pgm > test2.pgm')
    # os.system('pamtopnm <test2.pgm >test3.pbm')
    # img2 = Image.open('/Users/ktamas/Prog/python-paperang/test3.pbm')
    # img2 = Image.open('test3.pbm').convert('1')
    # img2.show()
    # os.system('')

    # img.show()
    # resize to the size paperang needs
    # new_img = resizer.process(img)
    # new_img.show()
    # do atkinson dithering
    # s = atk.atk(img.size[0], img.size[1], img.tobytes())
    # o = Image.frombytes('L', img.size, s)
    # o = Image.fromstring('L', img.size, s)

    m = np.array(img)[:,:]
    m2 = dither(m)
    # out = Image.fromarray(m2[::-1,:]).convert('1')
    out = Image.fromarray(m2[::-1,:])
    out.show()
    # the ditherer is stupid and does not make black and white images, just... almost so this fixes that
    enhancer = ImageEnhance.Contrast(out)
    enhanced_img = enhancer.enhance(4.0)
    enhanced_img.show()
    # now convert it to true black and white
    # blackandwhite_img = enhanced_img.convert('1')
    # blackandwhite_img.show()
    np_img = np.array(enhanced_img).astype(int)
    # flipping the ones and zeros
    np_img[np_img == 1] = 100
    np_img[np_img == 0] = 1
    np_img[np_img == 100] = 0

    return binimage2bitstream(np_img)

def sirius(im):
    np_img = np.fromfile(im, dtype='uint8')
    # there must be a less stupid way to invert the array but i am baby
    np_img[np_img == 1] = 100
    np_img[np_img == 0] = 1
    np_img[np_img == 100] = 0
    return binimage2bitstream(np_img)

import io

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFilter
from pygments import highlight


def add_corners(im, rad):
    circle = PIL.Image.new('L', (rad * 2, rad * 2), 0)
    draw = PIL.ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2 - 1, rad * 2 - 1), fill=255)
    alpha = PIL.Image.new('L', im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    return im


def makeShadow(
    image: PIL.Image.Image,
    radius: float,
    border: int,
    offset: tuple[float, float] | list[float],
    backgroundColour: tuple[float, float, float, float] | list[float],
    shadowColour: tuple[float, float, float, float] | list[float],
):
    # image: base image to give a drop shadow
    # radius: gaussian blur radius
    # border: border to give the image to leave space for the shadow
    # offset: offset of the shadow as [x,y]
    # backgroundCOlour: colour of the background
    # shadowColour: colour of the drop shadow

    assert len(offset) == 2
    assert len(backgroundColour) == 4
    assert len(shadowColour) == 4

    # Calculate the size of the shadow's image
    fullWidth = image.size[0] + abs(offset[0]) + 2 * border
    fullHeight = image.size[1] + abs(offset[1]) + 2 * border

    # Create the shadow's image. Match the parent image's mode.
    shadow = PIL.Image.new(image.mode, (fullWidth, fullHeight), backgroundColour)

    alpha = image.split()[-1]

    # Place the shadow, with the required offset
    shadowLeft = border + max(offset[0], 0)  # if <0, push the rest of the image right
    shadowTop = border + max(offset[1], 0)  # if <0, push the rest of the image down
    # Paste in the constant colour
    shadow.paste(
        shadowColour,
        [shadowLeft, shadowTop, shadowLeft + image.size[0], shadowTop + image.size[1]],
    )

    # Apply the BLUR filter repeatedly
    shadow = shadow.filter(PIL.ImageFilter.GaussianBlur(radius))

    # Paste the original image on top of the shadow
    imgLeft = border - min(offset[0], 0)  # if the shadow offset was <0, push right
    imgTop = border - min(offset[1], 0)  # if the shadow offset was <0, push down
    shadow.paste(image, (imgLeft, imgTop), alpha)

    return shadow


def render_code(code: str, lexer, formatter, aa_factor: float = 2):
    # Create Image
    i = highlight(code, lexer, formatter)
    img = PIL.Image.open(io.BytesIO(i))

    # Rounded Corners
    img = add_corners(img, int(5 * aa_factor))

    # Add drop shadow
    img = makeShadow(
        img,
        int(10 * aa_factor),
        int(20 * aa_factor),
        (int(1 * aa_factor), int(2 * aa_factor)),
        (0, 0, 0, 0),
        (0, 0, 0, 255),
    )

    # Anti-aliasing
    img = img.resize(
        (int(img.width / aa_factor), int(img.height / aa_factor)),
        resample=PIL.Image.Resampling.LANCZOS,
    )

    return img

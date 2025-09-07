import io

from PIL import Image, ImageDraw, ImageFilter
from pygments import highlight


def add_corners(img: Image.Image, radius: int):
    """
    Add rounded corners to an image by generating an alpha mask.

    Args:
        img (Image): image to modify
        radius (int): corner radius in pixels

    Returns:
        Image: `img` with rounded corners

    """
    width, height = img.size

    # Make circle for corner radius
    circle = Image.new('L', (radius * 2, radius * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radius * 2 - 1, radius * 2 - 1), fill=255)

    # Create alpha mask
    alpha = Image.new('L', img.size, 255)
    alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))
    alpha.paste(circle.crop((0, radius, radius, radius * 2)), (0, height - radius))
    alpha.paste(circle.crop((radius, 0, radius * 2, radius)), (width - radius, 0))
    alpha.paste(
        circle.crop((radius, radius, radius * 2, radius * 2)),
        (width - radius, height - radius),
    )

    # Apply alpha mask
    img.putalpha(alpha)

    return img


# TODO make this nice
def make_shadow(
    image: Image.Image,
    radius: float,
    border: int,
    offset: tuple[int, int] | list[int],
    background_color: tuple[float, ...] | list[float],
    shadow_color: tuple[float, ...] | list[float],
):
    # image: base image to give a drop shadow
    # radius: gaussian blur radius
    # border: border to give the image to leave space for the shadow
    # offset: offset of the shadow as [x,y]
    # backgroundCOlour: colour of the background
    # shadowColour: colour of the drop shadow

    assert len(offset) == 2
    assert len(background_color) == 4
    assert len(shadow_color) == 4

    if isinstance(background_color, list):
        background_color = tuple(background_color)

    if isinstance(shadow_color, list):
        shadow_color = tuple(shadow_color)

    # Calculate the size of the shadow's image
    fullWidth = image.size[0] + abs(offset[0]) + 2 * border
    fullHeight = image.size[1] + abs(offset[1]) + 2 * border

    # Create the shadow's image. Match the parent image's mode.
    shadow = Image.new(image.mode, (fullWidth, fullHeight), background_color)

    alpha = image.split()[-1]

    # Place the shadow, with the required offset
    shadowLeft = border + max(offset[0], 0)  # if <0, push the rest of the image right
    shadowTop = border + max(offset[1], 0)  # if <0, push the rest of the image down
    # Paste in the constant colour
    shadow.paste(
        shadow_color,
        (shadowLeft, shadowTop, shadowLeft + image.size[0], shadowTop + image.size[1]),
    )

    # Apply the BLUR filter repeatedly
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius))

    # Paste the original image on top of the shadow
    imgLeft = border - min(offset[0], 0)  # if the shadow offset was <0, push right
    imgTop = border - min(offset[1], 0)  # if the shadow offset was <0, push down
    shadow.paste(image, (imgLeft, imgTop), alpha)

    return shadow


def resize_image(
    img: Image.Image,
    width: int | str | None = None,
    height: int | str | None = None,
    resample: Image.Resampling = Image.Resampling.LANCZOS,
):
    """
    Resize an image given width and/or height.

    If only one of `width` or `height` are given, the other will be calculated using
    the aspect ration of the starting size.

    If `width` or `height` are a string ending with a percent `%` sign, they will
    be interpreted as percentage of the starting size.

    Args:
        img (Image): image to resize
        width (int | str, optional): resized width in pixels or percentage
        height (int | str, optional): resized height in pixels or percentage
        resample (Resampling, optional): resampling algorithm to use

    Returns:
        Image: resized image

    """
    assert width or height, 'Must provide at least one of width or height'

    aspect = img.height / img.width

    # Convert height to int if provided
    if height is not None:
        # Calculate percentage
        if isinstance(height, str) and height.endswith('%'):
            perc = int(height[:-1]) / 100
            height = int(img.height * perc)
        height = int(height)

    # Convert width to int if provided
    if width is not None:
        # Calculate percentage
        if isinstance(width, str) and width.endswith('%'):
            perc = int(width[:-1]) / 100
            width = int(img.width * perc)
        width = int(width)

    # If only height was given, calculate width from the aspect ratio
    if width is None:
        # Assert to make type checker happy
        assert height is not None
        width = int(height / aspect)

    # If only width was given, calculate height from the aspect ratio
    elif height is None:
        height = int(width * aspect)

    # Resize the image, convert width and height to int if they are still strings
    img = img.resize((int(width), int(height)), resample=resample)

    return img


def render_code(
    code: str,
    lexer,
    formatter,
    width: int | str | None = None,
    height: int | str | None = None,
    aa_factor: float = 2,
):
    # Create Image
    i = highlight(code, lexer, formatter)
    img = Image.open(io.BytesIO(i))

    # Rounded Corners
    img = add_corners(img, int(5 * aa_factor))

    # Add drop shadow
    img = make_shadow(
        img,
        int(10 * aa_factor),
        int(20 * aa_factor),
        (int(1 * aa_factor), int(2 * aa_factor)),
        (0, 0, 0, 0),
        (0, 0, 0, 255),
    )

    # If no width or height were given, just return the image at default size after antialiasing
    if width is None:
        width = int(img.width / aa_factor)

    if height is None:
        height = int(img.height / aa_factor)

    img = resize_image(img, width, height)

    return img

import io
import os
import sys
import tempfile
from subprocess import run

import click
from PIL import Image
from pygments.formatters import ImageFormatter
from pygments.lexers import (
    TextLexer,
    get_lexer_by_name,
    get_lexer_for_filename,
    guess_lexer,
)
from pygments.util import ClassNotFound

from codepic.render import render_code


def format_from_extension(output, default='png'):
    if output:
        ext = os.path.splitext(output)[1]

        if ext:
            ext = ext.lower()
            if ext == 'jpg':
                ext = 'jpeg'

            if ext in ['png', 'jpeg', 'bmp', 'gif']:
                print('Got output image format', ext, 'from output file extension', file=sys.stderr)
                return ext

    print('No format provided, defaulting to png', file=sys.stderr)
    return default


@click.command()
@click.option('-w', '--width', type=str, help='Fixed width in pixels or percent')
@click.option('-h', '--height', type=str, help='Fixed hight in pixels or percent')
@click.option('--line_numbers', is_flag=True, help='Show line numbers')
@click.option('-p', '--pad', type=int, default=30, help='Padding in pixels')
@click.option('--font_name', type=str, help='Font size in pt', default='')
@click.option('--font_size', type=int, default=14, help='Font size in pt')
@click.option('-a', '--aa_factor', type=float, default=1, help='Antialias factor')
@click.option('-s', '--style', type=str, default='one-dark')
@click.option('-l', '--lang', type=str)
@click.option('-c', '--clipboard', is_flag=True, help='Output image to clipboard')
@click.option(
    '-f',
    '--image_format',
    type=click.Choice(['png', 'jpeg', 'bmp', 'gif']),
    help='Image format',
)
@click.option(
    '-o',
    '--output',
    help='Output path for image',
    type=click.Path(
        exists=False,
        dir_okay=False,
        allow_dash=True,
    ),
    required=False,
)
@click.argument(
    'source_file',
    help='Input path of source code or - to read from stdin',
    type=click.Path(
        exists=False,
        dir_okay=False,
        allow_dash=True,
    ),
)
def cli(
    source_file: str,
    output: str | None,
    width: str | None,
    height: str | None,
    line_numbers: bool,
    pad: int,
    font_name: str,
    font_size: int,
    aa_factor: float,
    image_format: str | None,
    style: str,
    lang: str | None,
    clipboard: bool,
):
    code = ''

    # Use output file extension to detect image format, otherwise png
    if not image_format:
        image_format = format_from_extension(output)

    # Probably not needed since click forces lower and detect converts to lower
    image_format = image_format.lower()

    # Only png format can be stored in the clipboard
    if clipboard and image_format != 'png':
        raise click.ClickException('Image format must be png to use -c')

    # Must have somewhere to output, clipboard or file / stdout
    if not output and not clipboard:
        raise click.ClickException('No output location was specified, use -o or -c')

    # Write image to stdout, can be used with clipboard output
    write_to_stdout = output == '-'

    # Read code from stdin instead of file
    read_from_stdin = source_file == '-'

    # Get code before choosing lexer
    if read_from_stdin:
        code = sys.stdin.read()

    else:
        with open(source_file, 'r') as f:
            code = f.read()

    formatter = ImageFormatter(
        font_name=font_name,
        font_size=font_size * aa_factor,
        style=style,
        line_numbers=line_numbers,
        image_pad=pad * aa_factor,
        image_format=image_format,
    )

    lexer = None

    if lang:
        lexer = get_lexer_by_name(lang)

    if source_file == '-':
        code = sys.stdin.read()

        if not lexer:
            try:
                lexer = guess_lexer(code)

            except ClassNotFound:
                lexer = TextLexer()

        img = render_code(code, lexer, formatter, aa_factor)

    else:
        with open(source_file, 'r') as f:
            code = f.read()

        if not lexer:
            try:
                lexer = get_lexer_for_filename(code)

            except ClassNotFound:
                try:
                    lexer = guess_lexer(code)

                except ClassNotFound:
                    lexer = TextLexer()

        img = render_code(code, lexer, formatter, aa_factor)

    aspect = img.height / img.width

    if height:
        if height.endswith('%'):
            perc = int(height[:-1]) / 100
            height = int(img.height * perc)

        else:
            height = int(height)

    if width:
        if width.endswith('%'):
            perc = int(width[:-1]) / 100
            width = int(img.width * perc)

        else:
            width = int(width)

    if not width and height:
        width = int(height / aspect)

    if not height and width:
        height = int(width * aspect)

    if width and height:
        img = img.resize((width, height), resample=Image.Resampling.LANCZOS)

    buff = io.BytesIO()
    img.save(buff, format='PNG')

    buff = buff.getbuffer()

    if clipboard:
        with tempfile.NamedTemporaryFile('wb', delete=True) as fp:
            fp.write(buff)
            run(f'xclip -selection clipboard -target image/png < {fp.name}', shell=True)
            fp.flush()

    if write_to_stdout:
        sys.stdout.buffer.write(buff)

    elif output and output != '-':
        with open(output, 'wb') as f:
            f.write(buff)

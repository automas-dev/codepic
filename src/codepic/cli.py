import io
import os
import sys

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


@click.command()
@click.option('-w', '--width', type=str, help='Fixed width in pixels or percent')
@click.option('-h', '--height', type=str, help='Fixed hight in pixels or percent')
@click.option('--line_numbers', is_flag=True, help='Show line numbers')
@click.option('-p', '--pad', type=int, default=30, help='Padding in pixels')
@click.option('-f', '--font_name', type=str, help='Font size in pt')
@click.option('-s', '--font_size', type=int, default=14, help='Font size in pt')
@click.option('-a', '--aa_factor', type=float, default=1, help='Antialias factor')
@click.option('-s', '--style', type=str, default='one-dark')
@click.option('-l', '--lang', type=str)
@click.option(
    '-f',
    '--image_format',
    type=click.Choice(['png', 'jpeg', 'bmp', 'gif']),
    help='Antialias factor',
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
    # help='Input path of source code or - to read from stdin',
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
    font_name: str | None,
    font_size: int,
    aa_factor: float,
    image_format: str | None,
    style: str,
    lang: str | None,
):
    code = ''

    if font_name is None:
        font_name = ''

    if not image_format and output:
        ext = os.path.splitext(source_file)[1]
        if ext:
            ext = ext.lower()
            if ext in ['png', 'jpeg', 'jpg', 'bmp', 'gif']:
                image_format = ext
                if image_format == 'jpg':
                    image_format = 'jpeg'

    if not image_format:
        image_format = 'png'

    write_to_stdout = False
    if output == '-':
        write_to_stdout = True
    elif not output:
        if source_file == '-':
            write_to_stdout = True
        else:
            output = os.path.splitext(source_file)[0] + '.' + image_format.lower()

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

    if write_to_stdout:
        sys.stdout.buffer.write(buff.getbuffer())

    else:
        with open(output, 'wb') as f:
            f.write(buff.getbuffer())

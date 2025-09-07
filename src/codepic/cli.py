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

from codepic.render import render_code, resize_image


# Print message to stderr because the image can be written through stdout
def log(msg):
    click.echo(msg, err=True)


def format_from_extension(output, default='png'):
    if output:
        ext = os.path.splitext(output)[1]

        if ext:
            ext = ext.lower()
            if ext == 'jpg':
                ext = 'jpeg'

            if ext in ['png', 'jpeg', 'bmp', 'gif']:
                log(f'Got output image format {ext} from output file extension')
                return ext

    log('No format provided, defaulting to png')
    return default


def read_code(source_file):
    # Read code from stdin
    if source_file == '-':
        log('Reading code from stdion')
        return sys.stdin.read()

    # TODO maybe remove these as they might be too verbose
    log(f'Reading code from file {source_file}')

    # Read code from file
    with open(source_file, 'r') as f:
        return f.read()


def get_lexer(lang, source_file, code):
    # Lexer from language name
    if lang:
        return get_lexer_by_name(lang)

    # Use source file extension
    if source_file != '-':
        try:
            return get_lexer_for_filename(code)

        except ClassNotFound:
            log('Could not detect language from source file extension')
            pass

    try:
        return guess_lexer(code)

    except ClassNotFound:
        log('Could not detect language by analyzing code, defaulting to plain text')
        return TextLexer()


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
    font_name: str,
    font_size: int,
    aa_factor: float,
    image_format: str | None,
    style: str,
    lang: str | None,
    clipboard: bool,
):
    # Use output file extension to detect image format, otherwise png
    if not image_format:
        image_format = format_from_extension(output)

    else:
        log(f'Using image format {image_format}')

    # Only png format can be stored in the clipboard
    if clipboard and image_format != 'png':
        raise click.ClickException('Image format must be png to use -c')

    # Must have somewhere to output, clipboard or file / stdout
    if not output and not clipboard:
        raise click.ClickException('No output location was specified, use -o or -c')

    # Get code before choosing lexer
    code = read_code(source_file)

    # Get lexer from lang name or source file extension, defaults to plaintext
    lexer = get_lexer(lang, source_file, code)

    # Setup image formatting
    formatter = ImageFormatter(
        font_name=font_name,
        font_size=font_size * aa_factor,
        style=style,
        line_numbers=line_numbers,
        image_pad=pad * aa_factor,
        image_format=image_format,
    )

    # Render the code
    img = render_code(code, lexer, formatter, width, height, aa_factor)

    # GARBAGE AFTER HERE

    buff = io.BytesIO()
    img.save(buff, format='PNG')

    buff = buff.getbuffer()

    if clipboard:
        with tempfile.NamedTemporaryFile('wb', delete=True) as fp:
            fp.write(buff)
            run(f'xclip -selection clipboard -target image/png < {fp.name}', shell=True)
            fp.flush()

    # if write_to_stdout:
    #     sys.stdout.buffer.write(buff)

    elif output and output != '-':
        with open(output, 'wb') as f:
            f.write(buff)

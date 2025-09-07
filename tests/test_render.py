from unittest.mock import Mock, call, patch

import pytest

from codepic import render


@patch('codepic.render.ImageDraw')
@patch('codepic.render.Image')
def test_add_corners(mock_image, mock_draw):
    circle = Mock()
    circle.crop.side_effect = ['a', 'b', 'c', 'd']
    alpha = Mock()
    mock_image.new.side_effect = [circle, alpha]

    img = Mock()
    img.size = (2, 3)

    res = render.add_corners(img, 2)

    assert res == img
    img.putalpha.assert_called_once_with(alpha)

    assert mock_image.new.call_count == 2
    mock_image.new.assert_any_call('L', (4, 4), 0)
    mock_image.new.assert_any_call('L', (2, 3), 255)

    mock_draw.Draw.assert_called_once_with(circle)
    mock_draw.Draw().ellipse.assert_called_once_with((0, 0, 3, 3), fill=255)

    assert circle.crop.call_count == 4
    circle.crop.assert_has_calls(
        [
            call((0, 0, 2, 2)),
            call((0, 2, 2, 4)),
            call((2, 0, 4, 2)),
            call((2, 2, 4, 4)),
        ]
    )

    assert alpha.paste.call_count == 4
    alpha.paste.assert_has_calls(
        [
            call('a', (0, 0)),
            call('b', (0, 1)),
            call('c', (0, 0)),
            call('d', (0, 1)),
        ]
    )


def test_make_shadow():
    # TODO test this after cleanup
    pass


def test_resize_image():
    img = Mock()
    img.width = 4
    img.height = 8

    img.resize.return_value = 'resized'

    resample = Mock()

    res = render.resize_image(img, 2, 4, resample=resample)

    assert res == 'resized'

    img.resize.assert_called_once_with((2, 4), resample=resample)


def test_resize_image_no_height():
    img = Mock()
    img.width = 4
    img.height = 8

    img.resize.return_value = 'resized'

    resample = Mock()

    res = render.resize_image(img, 2, None, resample=resample)

    assert res == 'resized'

    img.resize.assert_called_once_with((2, 4), resample=resample)


def test_resize_image_no_width():
    img = Mock()
    img.width = 4
    img.height = 8

    img.resize.return_value = 'resized'

    resample = Mock()

    res = render.resize_image(img, None, 4, resample=resample)

    assert res == 'resized'

    img.resize.assert_called_once_with((2, 4), resample=resample)


def test_resize_image_missing_both():
    img = Mock()

    with pytest.raises(
        AssertionError, match='Must provide at least one of width or height'
    ):
        render.resize_image(img, None, None)


def test_resize_image_percentages():
    img = Mock()
    img.width = 4
    img.height = 8

    img.resize.return_value = 'resized'

    resample = Mock()

    res = render.resize_image(img, '50%', '100%', resample=resample)

    assert res == 'resized'

    img.resize.assert_called_once_with((2, 8), resample=resample)


@patch('codepic.render.io')
@patch('codepic.render.resize_image')
@patch('codepic.render.make_shadow')
@patch('codepic.render.add_corners')
@patch('codepic.render.Image')
@patch('codepic.render.highlight')
def test_render_code(
    mock_highlight, mock_image, mock_corner, mock_shadow, mock_resize, mock_io
):
    mock_highlight.return_value = 'highlighted'
    mock_io.BytesIO.return_value = 'bytes'
    mock_image.open.return_value = 'open'
    mock_corner.return_value = 'corners'
    mock_shadow.return_value = 'shadow'
    mock_resize.return_value = 'resized'

    res = render.render_code('code', 'lexer', 'formatter', 'width', 'height', 3)

    assert res == 'resized'

    mock_highlight.assert_called_once_with('code', 'lexer', 'formatter')
    mock_io.BytesIO.assert_called_once_with('highlighted')
    mock_image.open.assert_called_once_with('bytes')
    mock_corner.assert_called_once_with('open', 15)
    mock_shadow.assert_called_once_with(
        'corners', 30, 60, (3, 6), (0, 0, 0, 0), (0, 0, 0, 255)
    )
    mock_resize.assert_called_once_with('shadow', 'width', 'height')

# Code Pic

Capture code in a picture.

Generate an image of code using pygments syntax highlighting.

For example:

![](docs/test.png)

## Usage

```text
$ codepic --help
Usage: codepic [OPTIONS] SOURCE_FILE

Options:
  -w, --width TEXT                Fixed width in pixels or percent
  -h, --height TEXT               Fixed hight in pixels or percent
  --line_numbers                  Show line numbers
  -p, --pad INTEGER               Padding in pixels
  -f, --font_name TEXT            Font size in pt
  -s, --font_size INTEGER         Font size in pt
  -a, --aa_factor FLOAT           Antialias factor
  -s, --style TEXT
  -l, --lang TEXT
  -c, --clipboard                 Copy image to clipboard
  -f, --image_format [png|jpeg|bmp|gif]
                                  Antialias factor
  -o, --output FILE               Output path for image
  --help                          Show this message and exit.
```

### Install

```sh
make install
```

### Develop

```sh
make setup
```

#### Lint / Formatting

```sh
make lint
make format
```


#### Testing

```sh
make test
```

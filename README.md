# iOS 26 Rainbow Wallpaper Colors

Extract dominant colors from an album cover and map them to a fixed rainbow-wallpaper palette.

This script is useful when you want an album-art-based color set for the new iOS 26 rainbow wallpaper. It samples the pixels in an input image, finds the nearest color in a 75-color palette, then reports the most frequent palette colors.

## Features

- Maps album-cover pixels to a fixed palette instead of returning arbitrary image colors.
- Uses Oklab distance by default for more perceptual color matching.
- Prints ranked hex, RGB, percentage, and pixel count results.
- Supports JSON output for automation.
- Can save a preview image remapped to the palette colors.
- Handles transparent images with an alpha threshold.

## Requirements

- Python 3.9+
- NumPy
- Pillow

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

## Usage

Basic analysis:

```bash
python3 color_frequency.py path/to/album-cover.jpg
```

Show the top 6 colors:

```bash
python3 color_frequency.py path/to/album-cover.jpg --top 6
```

Output JSON:

```bash
python3 color_frequency.py path/to/album-cover.jpg --top 6 --json
```

Save a palette-mapped preview image:

```bash
python3 color_frequency.py path/to/album-cover.jpg --top 6 --save-map mapped-cover.png
```

Speed up analysis for very large images by sampling every 3rd pixel:

```bash
python3 color_frequency.py path/to/album-cover.jpg --sample-step 3
```

## Example Output

```text
 1. #F4007A rgb(244, 0, 122) 18.42% (18420 px)
 2. #22A2F9 rgb(34, 162, 249) 12.77% (12770 px)
 3. #FEE600 rgb(254, 230, 0) 9.31% (9310 px)
```

Terminal color blocks are shown by default. To hide them:

```bash
python3 color_frequency.py path/to/album-cover.jpg --no-blocks
```

## Options

```text
image                    Input image path
-n, --top                Number of colors to output, default: 3
--metric {oklab,rgb}     Nearest-color distance metric, default: oklab
--sample-step N          Use every Nth pixel in both directions
--alpha-threshold N      Ignore pixels with alpha lower than N, default: 1
--chunk-size N           Pixels processed per chunk, default: 200000
--json                   Print JSON instead of text
--no-blocks              Hide ANSI color blocks
--save-map PATH          Write an image remapped to palette colors
```

## Notes

The palette is embedded in `color_frequency.py` as `PALETTE_HEX`. It was built from 75 circular color swatches, sampled from the center of each circle and cleaned to exclude background colors.

For wallpaper color picking, start with `--top 3` or `--top 6`, then choose the colors that best match the album mood rather than blindly using only the highest-ranked output.


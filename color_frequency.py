#!/usr/bin/env python3
"""Map image pixels to a fixed sheet palette and report dominant colors."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


# Extracted from the 75 circular color swatches in the three provided sheet
# screenshots, sampled from the center of each circle and ignoring backgrounds.
PALETTE_HEX = [
    "#6E0001", "#A8000D", "#FE0000", "#F53F00", "#EB5D37",
    "#F78000", "#FAAC01", "#FEE600", "#FFEA7F", "#D9E96C",
    "#E7FF25", "#99E733", "#4ABA00", "#187C00", "#1B4209",
    "#162309", "#022708", "#1A5B31", "#35D86B", "#9DFFB2",
    "#5BFFE7", "#25D3CA", "#215B67", "#1B679B", "#22A2F9",
    "#5AD0F8", "#6FBAF1", "#4495FE", "#114AA4", "#0021A6",
    "#2A42E2", "#5E82F2", "#6363FF", "#3215E3", "#160093",
    "#23008E", "#310090", "#6F12DD", "#7B52CC", "#B96CD4",
    "#AD49C5", "#B107DA", "#5F008E", "#820086", "#CC0F9D",
    "#C95BBC", "#F789D2", "#D956A4", "#F4007A", "#A0030E",
    "#A40035", "#F20152", "#F53570", "#F6698C", "#E25275",
    "#7D2F3C", "#5B1F1E", "#390D00", "#622C14", "#A44227",
    "#AA6053", "#7A463B", "#39241F", "#583E31", "#A37B6F",
    "#FBD8B0", "#8D8060", "#4C4034", "#484745", "#79746E",
    "#FFFFFF", "#7F7F7F", "#545454", "#232323", "#000000",
]


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError(f"invalid hex color: {value!r}")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: np.ndarray | tuple[int, int, int]) -> str:
    r, g, b = [int(x) for x in rgb]
    return f"#{r:02X}{g:02X}{b:02X}"


def srgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    rgb = rgb.astype(np.float64) / 255.0
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def rgb_to_oklab(rgb: np.ndarray) -> np.ndarray:
    linear = srgb_to_linear(rgb)
    red = linear[:, 0]
    green = linear[:, 1]
    blue = linear[:, 2]

    lms_l = 0.4122214708 * red + 0.5363325363 * green + 0.0514459929 * blue
    lms_m = 0.2119034982 * red + 0.6806995451 * green + 0.1073969566 * blue
    lms_s = 0.0883024619 * red + 0.2817188376 * green + 0.6299787005 * blue
    lms = np.stack([lms_l, lms_m, lms_s], axis=1)

    lms_cbrt = np.cbrt(lms)
    lab_l = (
        0.2104542553 * lms_cbrt[:, 0]
        + 0.7936177850 * lms_cbrt[:, 1]
        - 0.0040720468 * lms_cbrt[:, 2]
    )
    lab_a = (
        1.9779984951 * lms_cbrt[:, 0]
        - 2.4285922050 * lms_cbrt[:, 1]
        + 0.4505937099 * lms_cbrt[:, 2]
    )
    lab_b = (
        0.0259040371 * lms_cbrt[:, 0]
        + 0.7827717662 * lms_cbrt[:, 1]
        - 0.8086757660 * lms_cbrt[:, 2]
    )
    return np.stack([lab_l, lab_a, lab_b], axis=1)


def color_space(rgb: np.ndarray, metric: str) -> np.ndarray:
    if metric == "rgb":
        return rgb.astype(np.float32)
    if metric == "oklab":
        return rgb_to_oklab(rgb)
    raise ValueError(f"unknown metric: {metric}")


def nearest_palette_indices(
    pixels: np.ndarray,
    palette: np.ndarray,
    metric: str,
    chunk_size: int,
) -> np.ndarray:
    palette_space = color_space(palette, metric)
    result = np.empty(len(pixels), dtype=np.uint16)

    for start in range(0, len(pixels), chunk_size):
        end = min(start + chunk_size, len(pixels))
        pixel_space = color_space(pixels[start:end], metric)
        diff = pixel_space[:, None, :] - palette_space[None, :, :]
        result[start:end] = np.argmin(np.sum(diff * diff, axis=2), axis=1)

    return result


def load_pixels(path: Path, sample_step: int, alpha_threshold: int) -> tuple[np.ndarray, int]:
    image = Image.open(path)
    rgba = image.convert("RGBA")
    arr = np.asarray(rgba)
    if sample_step > 1:
        arr = arr[::sample_step, ::sample_step]

    alpha = arr[..., 3]
    mask = alpha >= alpha_threshold
    pixels = arr[..., :3][mask]
    return pixels.reshape(-1, 3), int(mask.sum())


def save_mapped_image(
    input_path: Path,
    output_path: Path,
    palette: np.ndarray,
    metric: str,
    chunk_size: int,
    alpha_threshold: int,
) -> None:
    rgba = Image.open(input_path).convert("RGBA")
    arr = np.asarray(rgba)
    rgb = arr[..., :3].reshape(-1, 3)
    alpha = arr[..., 3].reshape(-1)
    mapped = np.zeros_like(rgb)

    opaque = alpha >= alpha_threshold
    nearest = nearest_palette_indices(rgb[opaque], palette, metric, chunk_size)
    mapped[opaque] = palette[nearest]

    out = np.concatenate(
        [mapped.reshape(arr.shape[0], arr.shape[1], 3), arr[..., 3:4]],
        axis=2,
    ).astype(np.uint8)
    Image.fromarray(out).save(output_path)


def color_block(rgb: np.ndarray, enabled: bool) -> str:
    if not enabled:
        return ""
    r, g, b = [int(x) for x in rgb]
    return f"\x1b[48;2;{r};{g};{b}m  \x1b[0m "


def analyze(args: argparse.Namespace) -> list[dict[str, object]]:
    palette = np.array([hex_to_rgb(color) for color in PALETTE_HEX], dtype=np.uint8)
    pixels, total = load_pixels(args.image, args.sample_step, args.alpha_threshold)
    if total == 0:
        raise ValueError("no pixels matched the alpha threshold")

    nearest = nearest_palette_indices(pixels, palette, args.metric, args.chunk_size)
    counts = np.bincount(nearest, minlength=len(palette))
    order = np.argsort(-counts)[: args.top]

    return [
        {
            "rank": rank,
            "hex": rgb_to_hex(palette[index]),
            "rgb": [int(v) for v in palette[index]],
            "count": int(counts[index]),
            "percent": round(float(counts[index] * 100.0 / total), 4),
        }
        for rank, index in enumerate(order, 1)
        if counts[index] > 0
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Find dominant colors by mapping image pixels to the extracted sheet palette.",
    )
    parser.add_argument("image", type=Path, help="input image path")
    parser.add_argument("-n", "--top", type=int, default=3, help="number of colors to output")
    parser.add_argument(
        "--metric",
        choices=("oklab", "rgb"),
        default="oklab",
        help="nearest-color distance metric",
    )
    parser.add_argument(
        "--sample-step",
        type=int,
        default=1,
        help="use every Nth pixel in both directions for faster approximate analysis",
    )
    parser.add_argument(
        "--alpha-threshold",
        type=int,
        default=1,
        help="ignore pixels with alpha lower than this value",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=200_000,
        help="pixels processed per chunk",
    )
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    parser.add_argument("--no-blocks", action="store_true", help="hide ANSI color blocks")
    parser.add_argument("--save-map", type=Path, help="write an image remapped to palette colors")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.top <= 0:
        parser.error("--top must be greater than 0")
    if args.sample_step <= 0:
        parser.error("--sample-step must be greater than 0")
    if args.chunk_size <= 0:
        parser.error("--chunk-size must be greater than 0")
    if not 0 <= args.alpha_threshold <= 255:
        parser.error("--alpha-threshold must be between 0 and 255")
    if not args.image.exists():
        parser.error(f"image not found: {args.image}")

    try:
        results = analyze(args)
        if args.save_map:
            palette = np.array([hex_to_rgb(color) for color in PALETTE_HEX], dtype=np.uint8)
            save_mapped_image(
                args.image,
                args.save_map,
                palette,
                args.metric,
                args.chunk_size,
                args.alpha_threshold,
            )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for item in results:
            rgb = np.array(item["rgb"], dtype=np.uint8)
            block = color_block(rgb, not args.no_blocks)
            print(
                f"{item['rank']:>2}. {block}{item['hex']} "
                f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]}) "
                f"{item['percent']:.2f}% ({item['count']} px)"
            )
        if args.save_map:
            print(f"mapped image: {args.save_map}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

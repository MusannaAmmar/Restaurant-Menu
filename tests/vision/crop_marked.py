from __future__ import annotations

from typing import List, Tuple

from PIL import Image
import numpy as np
import os
import argparse


def load_image(image_path: str) -> Image.Image:
    """
    Open an image using Pillow and convert it to RGB.
    """
    return Image.open(image_path).convert("RGB")


def find_red_boxes(
    img: Image.Image,
    red_threshold: int = 180,
    gb_threshold: int = 80,
    line_coverage: float = 0.2,
    min_box_size: int = 40,
) -> List[Tuple[int, int, int, int]]:
    """
    Detect rectangular red borders and return inner crop boxes.

    The function looks for strong red pixels (R high, G/B low), builds a mask,
    finds horizontal and vertical lines, and computes intersecting rectangles.

    Returns a list of (left, top, right, bottom) tuples suitable for PIL.crop.
    """
    arr = np.asarray(img)

    # Heuristic: "red" border – R high, G and B low (thresholds configurable)
    red_mask = (arr[:, :, 0] >= red_threshold) & (arr[:, :, 1] <= gb_threshold) & (arr[:, :, 2] <= gb_threshold)

    # Sum along axes to find where red lines occur consistently
    rows_strength = red_mask.sum(axis=1)
    cols_strength = red_mask.sum(axis=0)

    # Consider a row/col as a border line if sufficient fraction of pixels are red in that line
    # Lower fractions work better for thin borders (e.g., 2px width borders)
    row_line = rows_strength > (line_coverage * arr.shape[1])
    col_line = cols_strength > (line_coverage * arr.shape[0])

    # Get contiguous segments of True values – these are thick red lines
    def contiguous_segments(boolean_array: np.ndarray) -> List[Tuple[int, int]]:
        segments: List[Tuple[int, int]] = []
        in_seg = False
        start = 0
        for i, val in enumerate(boolean_array):
            if val and not in_seg:
                in_seg = True
                start = i
            elif not val and in_seg:
                in_seg = False
                segments.append((start, i - 1))
        if in_seg:
            segments.append((start, len(boolean_array) - 1))
        return segments

    horizontal_lines = contiguous_segments(row_line)
    vertical_lines = contiguous_segments(col_line)

    # We expect pairs of horizontal and vertical lines forming boxes.
    # Compute inner boxes (excluding the border thickness).
    boxes: List[Tuple[int, int, int, int]] = []
    if len(horizontal_lines) >= 2 and len(vertical_lines) >= 2:
        # Form grid by pairing consecutive horizontal and vertical lines
        for hi in range(len(horizontal_lines) - 1):
            top_line = horizontal_lines[hi]
            bottom_line = horizontal_lines[hi + 1]
            # Inner top/bottom: move inside by 1 pixel from each line segment
            inner_top = top_line[1] + 1
            inner_bottom = bottom_line[0] - 1

            if inner_bottom - inner_top < min_box_size:
                continue

            for vi in range(len(vertical_lines) - 1):
                left_line = vertical_lines[vi]
                right_line = vertical_lines[vi + 1]
                inner_left = left_line[1] + 1
                inner_right = right_line[0] - 1

                if inner_right - inner_left < min_box_size:
                    continue

                boxes.append((inner_left, inner_top, inner_right, inner_bottom))

    return boxes


def crop_regions(img: Image.Image, boxes: List[Tuple[int, int, int, int]]) -> List[Image.Image]:
    """
    Crop the given boxes from the image and return the list of crops.
    """
    crops: List[Image.Image] = []
    for box in boxes:
        crops.append(img.crop(box))
    return crops


def save_crops(crops: List[Image.Image], out_dir: str, base_name: str = "crop") -> List[str]:
    """
    Save cropped images to out_dir and return their file paths.
    """
    os.makedirs(out_dir, exist_ok=True)
    saved_paths: List[str] = []
    for idx, im in enumerate(crops, start=1):
        path = os.path.join(out_dir, f"{base_name}_{idx}.png")
        im.save(path)
        saved_paths.append(path)
    return saved_paths


def process_marked_image(
    image_path: str,
    out_dir: str,
    red_threshold: int = 180,
    gb_threshold: int = 80,
    line_coverage: float = 0.2,
    min_box_size: int = 40,
    verbose: bool = False,
) -> List[str]:
    """
    High-level convenience function: load, detect boxes, crop, and save.
    """
    img = load_image(image_path)
    if verbose:
        print(f"Loaded image: {image_path} ({img.size[0]}x{img.size[1]})")
    
    boxes = find_red_boxes(
        img,
        red_threshold=red_threshold,
        gb_threshold=gb_threshold,
        line_coverage=line_coverage,
        min_box_size=min_box_size,
    )
    if verbose:
        print(f"Found {len(boxes)} candidate boxes before filtering")

    # Post-filter: keep square-like, non-edge, largest boxes (expect 4 items)
    width, height = img.size
    filtered: List[Tuple[int, int, int, int]] = []
    for (l, t, r, b) in boxes:
        w = r - l
        h = b - t
        # Discard very thin stripes and boxes hugging the image edges
        aspect = w / max(h, 1)
        if w < 40 or h < 40:
            continue
        if l <= 5 or t <= 5 or r >= width - 5 or b >= height - 5:
            continue
        if not (0.6 <= aspect <= 1.4):
            continue
        filtered.append((l, t, r, b))

    # If still more than 4, keep the four largest by area
    filtered.sort(key=lambda box: (box[2] - box[0]) * (box[3] - box[1]), reverse=True)
    filtered = filtered[:4]
    
    if verbose:
        print(f"After filtering: {len(filtered)} boxes to crop")

    crops = crop_regions(img, filtered)
    return save_crops(crops, out_dir, base_name=os.path.splitext(os.path.basename(image_path))[0])


def main():
    # Simple CLI for beginners:
    # python tests/vision/crop_marked.py --image tests/vision/images/marked.png --out tests/vision/images/crops
    parser = argparse.ArgumentParser(description="Crop regions inside red boxes from an image.")
    parser.add_argument("--image", required=False, default=r"tests\vision\images\marked.png", help="Path to the marked image")
    parser.add_argument("--out", required=False, default=r"tests\vision\images\crops", help="Directory to save crops")
    parser.add_argument("--red-threshold", type=int, default=180, help="Red channel threshold for detection (default: 180)")
    parser.add_argument("--gb-threshold", type=int, default=80, help="Max G/B channel value to still count as red (default: 80)")
    parser.add_argument("--line-coverage", type=float, default=0.2, help="Fraction of pixels in a row/col to consider it a red line (default: 0.2)")
    parser.add_argument("--min-box-size", type=int, default=40, help="Minimum box size in pixels (default: 40)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed diagnostic information")
    args = parser.parse_args()

    print(f"Processing image: {args.image}")
    print(f"Output directory: {args.out}")
    if args.verbose:
        print(
            f"Detection settings: red_threshold={args.red_threshold}, gb_threshold={args.gb_threshold}, "
            f"line_coverage={args.line_coverage}, min_box_size={args.min_box_size}"
        )
    
    try:
        saved = process_marked_image(
            args.image,
            args.out,
            red_threshold=args.red_threshold,
            gb_threshold=args.gb_threshold,
            line_coverage=args.line_coverage,
            min_box_size=args.min_box_size,
            verbose=args.verbose,
        )
        
        if not saved:
            print("\n⚠️  No crops were saved!")
            print("Possible reasons:")
            print("  - No red boxes detected in the image")
            print("  - Red boxes are too faint (try lowering --red-threshold)")
            print("  - Red boxes are too small (try lowering --min-box-size)")
            print("  - Boxes were filtered out (too close to edges, wrong aspect ratio)")
            print(f"\nTry running with --verbose to see diagnostic information:")
            print(f"  python tests/vision/crop_marked.py --image {args.image} --out {args.out} --verbose")
        else:
            print(f"\n✅ Successfully saved {len(saved)} crop(s):")
            for p in saved:
                print(f"  - {p}")
    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        if args.verbose:
            traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    main()



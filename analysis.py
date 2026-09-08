import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from stego_core import (
    analyze_file_size,
    calculate_histogram,
    calculate_mse,
    calculate_psnr,
)


def save_histogram_comparison(
    cover_path,
    stego_path,
    output_path
):
    cover_hist = calculate_histogram(cover_path)
    stego_hist = calculate_histogram(stego_path)

    x = range(256)
    channels = ("Red", "Green", "Blue")

    fig, axes = plt.subplots(
        3,
        1,
        figsize=(10, 10),
        sharex=True
    )

    for ax, name, cover_values, stego_values in zip(
        axes,
        channels,
        cover_hist,
        stego_hist
    ):
        ax.plot(
            x,
            cover_values,
            label="Cover"
        )

        ax.plot(
            x,
            stego_values,
            label="Stego",
            alpha=0.75
        )

        ax.set_title(
            f"{name} Channel Histogram"
        )

        ax.set_ylabel("Pixel count")
        ax.legend()
        ax.grid(alpha=0.2)

    axes[-1].set_xlabel(
        "Pixel intensity (0-255)"
    )

    fig.suptitle(
        "Cover vs Stego Histogram Comparison"
    )

    fig.tight_layout()

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fig.savefig(
        output_path,
        dpi=160
    )

    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze cover and stego images"
    )

    parser.add_argument("cover")
    parser.add_argument("stego")

    parser.add_argument(
        "--hist-output",
        default="assets/output/histogram_comparison.png"
    )

    args = parser.parse_args()

    mse = calculate_mse(
        args.cover,
        args.stego
    )

    psnr = calculate_psnr(
        args.cover,
        args.stego
    )

    size = analyze_file_size(
        args.cover,
        args.stego
    )

    save_histogram_comparison(
        args.cover,
        args.stego,
        args.hist_output
    )

    print("\n=== IMAGE QUALITY ===")
    print(f"MSE               : {mse:.6f}")
    print(f"PSNR              : {psnr:.2f} dB")

    print("\n=== FILE SIZE ===")
    print(
        f"Cover size        : "
        f"{size['cover_size']:,} bytes"
    )

    print(
        f"Stego size        : "
        f"{size['stego_size']:,} bytes"
    )

    print(
        f"Difference        : "
        f"{size['difference']:+,} bytes"
    )

    print(
        f"Percentage change : "
        f"{size['percentage_change']:+.2f}%"
    )

    print(
        f"\nHistogram saved to: "
        f"{args.hist_output}"
    )


if __name__ == "__main__":
    main()

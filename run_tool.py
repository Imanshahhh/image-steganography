import argparse
from src.stego_core import embed, extract


def print_result(title, result):
    print(f"\n=== {title} ===")
    for key, value in result.items():
        print(f"{key}: {value}")


def main():
    parser = argparse.ArgumentParser(
        description="Image Steganography Tool"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    embed_parser = subparsers.add_parser(
        "embed",
        help="Hide a secret file inside an image"
    )
    embed_parser.add_argument("cover")
    embed_parser.add_argument("secret")
    embed_parser.add_argument("output")

    extract_parser = subparsers.add_parser(
        "extract",
        help="Extract secret file from stego image"
    )
    extract_parser.add_argument("stego")
    extract_parser.add_argument("output_dir")

    args = parser.parse_args()

    if args.command == "embed":
        result = embed(
            args.cover,
            args.secret,
            args.output
        )
        print_result("EMBED SUCCESS", result)

    elif args.command == "extract":
        result = extract(
            args.stego,
            args.output_dir
        )
        print_result("EXTRACT SUCCESS", result)


if __name__ == "__main__":
    main()

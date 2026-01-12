"""Entry point for Bowser browser."""

import argparse
import logging
from src.browser.browser import Browser


def _parse_args():
    parser = argparse.ArgumentParser(prog="bowser", description="Bowser educational browser")
    parser.add_argument("url", nargs="?", default=None, help="URL to open (optional, defaults to startpage)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output (alias for --log-level=DEBUG)")
    parser.add_argument(
        "--log-level",
        choices=["ERROR", "WARNING", "INFO", "DEBUG"],
        default="INFO",
        help="Set logging level",
    )
    return parser.parse_args()


def _configure_logging(args):
    level = logging.DEBUG if args.debug else getattr(logging, args.log_level)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    args = _parse_args()
    _configure_logging(args)

    browser = Browser()

    # Enable debug mode in chrome if --debug flag is set
    if args.debug:
        browser.chrome.debug_mode = True

    # If no URL provided, use startpage
    url = args.url if args.url else "about:startpage"
    browser.new_tab(url)
    browser.run()


if __name__ == "__main__":
    main()

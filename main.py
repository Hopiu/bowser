"""Entry point for Bowser browser (stub)."""

from src.browser.browser import Browser


def main():
    browser = Browser()
    browser.new_tab("https://example.com")
    browser.run()


if __name__ == "__main__":
    main()

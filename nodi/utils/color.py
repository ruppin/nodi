"""Color utilities for terminal output."""


class Color:
    """ANSI color codes for terminal output."""

    # Reset
    RESET = "\033[0m"

    # Regular colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bold colors
    BOLD_BLACK = "\033[1;30m"
    BOLD_RED = "\033[1;31m"
    BOLD_GREEN = "\033[1;32m"
    BOLD_YELLOW = "\033[1;33m"
    BOLD_BLUE = "\033[1;34m"
    BOLD_MAGENTA = "\033[1;35m"
    BOLD_CYAN = "\033[1;36m"
    BOLD_WHITE = "\033[1;37m"

    @staticmethod
    def colorize(text: str, color: str) -> str:
        """Colorize text."""
        return f"{color}{text}{Color.RESET}"

    @staticmethod
    def success(text: str) -> str:
        """Green success message."""
        return Color.colorize(text, Color.GREEN)

    @staticmethod
    def error(text: str) -> str:
        """Red error message."""
        return Color.colorize(text, Color.RED)

    @staticmethod
    def warning(text: str) -> str:
        """Yellow warning message."""
        return Color.colorize(text, Color.YELLOW)

    @staticmethod
    def info(text: str) -> str:
        """Cyan info message."""
        return Color.colorize(text, Color.CYAN)

    @staticmethod
    def bold(text: str) -> str:
        """Bold text."""
        return f"\033[1m{text}{Color.RESET}"

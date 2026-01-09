"""
Terminal Context Manager - Manages terminal output buffer for AI context.
Implements sliding window to limit token usage.
"""
from collections import deque
from typing import List


class TerminalContext:
    """
    Manages terminal output history for AI context.
    Uses a sliding window approach to manage memory usage.
    """

    def __init__(self, max_lines: int = 500, max_chars: int = 3000):
        """
        Initialize terminal context manager.

        Args:
            max_lines: Maximum number of lines to keep in buffer
            max_chars: Maximum number of characters to return for context
        """
        self.max_lines = max_lines
        self.max_chars = max_chars

        # Use deque for efficient popleft operations
        self.buffer: deque = deque(maxlen=max_lines)

        # Track total characters for optimization
        self._total_chars = 0

    def append(self, text: str):
        """
        Append text to buffer.

        Args:
            text: Text to append
        """
        if not text:
            return

        # Split into lines and add to buffer
        lines = text.split('\n')
        for line in lines:
            self.buffer.append(line)
            self._total_chars += len(line) + 1  # +1 for newline

    def get_context(self, last_n_lines: int = None) -> str:
        """
        Get recent terminal context.

        Args:
            last_n_lines: Number of recent lines to return (None for all)

        Returns:
            String containing recent terminal output
        """
        if not self.buffer:
            return ""

        # Get lines
        if last_n_lines:
            lines = list(self.buffer)[-last_n_lines:]
        else:
            lines = list(self.buffer)

        context = '\n'.join(lines)

        # Truncate if too long
        if len(context) > self.max_chars:
            # Truncate from the beginning, keeping the end
            context = context[-self.max_chars:]
            # Try to truncate at a newline to avoid cutting mid-line
            first_newline = context.find('\n')
            if first_newline > 0:
                context = context[first_newline + 1:]

        return context

    def get_last_lines(self, count: int) -> str:
        """
        Get the last N lines from buffer.

        Args:
            count: Number of lines to retrieve

        Returns:
            String containing the last N lines
        """
        return self.get_context(last_n_lines=count)

    def get_tail(self, char_count: int) -> str:
        """
        Get the last N characters from buffer.

        Args:
            char_count: Number of characters to retrieve

        Returns:
            String containing the last N characters
        """
        if not self.buffer:
            return ""

        context = '\n'.join(self.buffer)

        if len(context) <= char_count:
            return context

        # Return last N characters
        return context[-char_count:]

    def clear(self):
        """Clear the buffer."""
        self.buffer.clear()
        self._total_chars = 0

    def size(self) -> int:
        """
        Get current buffer size in characters.

        Returns:
            Number of characters in buffer
        """
        return self._total_chars

    def line_count(self) -> int:
        """
        Get current number of lines in buffer.

        Returns:
            Number of lines in buffer
        """
        return len(self.buffer)

    def __len__(self) -> int:
        """Return number of lines in buffer."""
        return len(self.buffer)

    def __str__(self) -> str:
        """Return string representation of buffer."""
        return '\n'.join(self.buffer)

    def __repr__(self) -> str:
        """Return debug representation."""
        return f"TerminalContext(lines={len(self.buffer)}, chars={self._total_chars})"

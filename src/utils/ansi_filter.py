"""
ANSI escape sequence processor for terminal output.
Converts ANSI color codes and control sequences to HTML for rendering.
"""
import re


class ANSItoHTML:
    """
    Convert ANSI escape sequences to HTML for colored terminal output.
    Supports colors, bold, italic, and other text attributes.
    """

    # ANSI color codes to CSS colors
    ANSI_COLORS = {
        '30': '#000000',  # Black
        '31': '#cd0000',  # Red
        '32': '#00cd00',  # Green
        '33': '#cdcd00',  # Yellow
        '34': '#0000ee',  # Blue
        '35': '#cd00cd',  # Magenta
        '36': '#00cdcd',  # Cyan
        '37': '#e5e5e5',  # White
        '90': '#7f7f7f',  # Bright Black (Gray)
        '91': '#ff0000',  # Bright Red
        '92': '#00ff00',  # Bright Green
        '93': '#ffff00',  # Bright Yellow
        '94': '#5c5cff',  # Bright Blue
        '95': '#ff00ff',  # Bright Magenta
        '96': '#00ffff',  # Bright Cyan
        '97': '#ffffff',  # Bright White
    }

    # Background colors
    ANSI_BG_COLORS = {
        '40': '#000000',  # Black
        '41': '#cd0000',  # Red
        '42': '#00cd00',  # Green
        '43': '#cdcd00',  # Yellow
        '44': '#0000ee',  # Blue
        '45': '#cd00cd',  # Magenta
        '46': '#00cdcd',  # Cyan
        '47': '#e5e5e5',  # White
        '100': '#7f7f7f',  # Bright Black (Gray)
        '101': '#ff0000',  # Bright Red
        '102': '#00ff00',  # Bright Green
        '103': '#ffff00',  # Bright Yellow
        '104': '#5c5cff',  # Bright Blue
        '105': '#ff00ff',  # Bright Magenta
        '106': '#00ffff',  # Bright Cyan
        '107': '#ffffff',  # Bright White
    }

    def __init__(self):
        """Compile regex patterns for better performance."""
        # CSI sequence pattern: ESC[ ... m (SGR - Select Graphic Rendition)
        self.csi_pattern = re.compile(r'\x1b\[([0-9;]*)m')

        # Other control sequences to remove (these must NOT match SGR sequences ending with 'm')
        self.control_patterns = [
            re.compile(r'\x1b\[[0-9;]*[GKHfABCDsu]'),  # Cursor movement
            re.compile(r'\x1b\][^\x07\x1b]*[\x07\x1b\\]'),  # OSC sequences
            re.compile(r'\x1b\?\d+[hl]'),  # Private mode sequences (including bracketed paste)
            re.compile(r'\[\?2004[hl]'),  # Bracketed paste mode (without ESC)
            re.compile(r'\x1bP[^\x1b]*\x1b\\'),  # DCS sequences
            re.compile(r'\x1b\[[0-9;]*n'),  # Device status reports
            re.compile(r'\x1b\[>[0-9;]*l'),  # Keyboard mode (not m, to avoid SGR)
            re.compile(r'\x1b\[[0-9;]*r'),  # Cursor positioning
            re.compile(r'\x1b\[\?[0-9;]*[lh]'),  # Mode setting (not h with digits before, to avoid SGR)
            re.compile(r'\[\?[0-9;]*[hl]'),  # Bracketed paste mode variants
        ]

        # Current formatting state
        self.reset_state()

    def reset_state(self):
        """Reset formatting state to default."""
        self.bold = False
        self.italic = False
        self.underline = False
        self.fg_color = None
        self.bg_color = None

    def convert(self, text: str) -> str:
        """
        Convert ANSI text to HTML.

        Args:
            text: Text with ANSI escape sequences

        Returns:
            HTML string with CSS styling
        """
        if not text:
            return text

        # First, identify and protect SGR sequences (colors)
        # Replace them with temporary placeholders
        sgr_placeholders = []
        def protect_sgr(match):
            placeholder = f'\x00SGR{len(sgr_placeholders)}\x00'
            sgr_placeholders.append(match.group(0))  # Store full SGR sequence
            return placeholder

        text_with_placeholders = self.csi_pattern.sub(protect_sgr, text)

        # Now remove non-SGR control sequences from the text
        cleaned = text_with_placeholders
        for pattern in self.control_patterns:
            cleaned = pattern.sub('', cleaned)

        # Remove any remaining ESC characters (orphaned)
        cleaned = cleaned.replace('\x1b', '')

        # Restore SGR sequences
        for i, sgr_seq in enumerate(sgr_placeholders):
            cleaned = cleaned.replace(f'\x00SGR{i}\x00', sgr_seq)

        # Split by CSI SGR sequences (color codes) but keep delimiters
        parts = self.csi_pattern.split(cleaned)
        result = []
        current_style = {}

        # Process each part
        for i, part in enumerate(parts):
            if i % 2 == 0:
                # Regular text (even indices)
                if part:
                    if current_style:
                        # Apply current style
                        style = self._build_style(current_style)
                        # Replace \n with <br> but use style to control spacing
                        escaped = self._escape_html(part).replace('\n', '<br style="line-height: 1.0">')
                        result.append(f'<span style="{style}">{escaped}</span>')
                    else:
                        # No style - plain text with line breaks
                        escaped = self._escape_html(part).replace('\n', '<br style="line-height: 1.0">')
                        result.append(escaped)
            else:
                # ANSI SGR code (odd indices)
                current_style = self._parse_ansi_codes(part)

        # Join all parts - don't wrap in div to avoid extra spacing
        return ''.join(result) if result else ''

    def _parse_ansi_codes(self, codes_str: str) -> dict:
        """
        Parse ANSI SGR (Select Graphic Rendition) codes.

        Args:
            codes_str: Semicolon-separated ANSI codes

        Returns:
            Dictionary with style properties
        """
        style = {}

        if not codes_str:
            self.reset_state()
            return style

        codes = codes_str.split(';')

        for code in codes:
            if not code:
                continue

            num = int(code)

            if num == 0:
                # Reset all
                self.reset_state()
                return {}
            elif num == 1:
                style['bold'] = True
                self.bold = True
            elif num == 3:
                style['italic'] = True
                self.italic = True
            elif num == 4:
                style['underline'] = True
                self.underline = True
            elif num == 22:
                style['bold'] = False
                self.bold = False
            elif num == 23:
                style['italic'] = False
                self.italic = False
            elif num == 24:
                style['underline'] = False
                self.underline = False
            elif 30 <= num <= 37 or 90 <= num <= 97:
                # Foreground color
                style['color'] = self.ANSI_COLORS.get(str(num), '#000000')
                self.fg_color = style['color']
            elif 40 <= num <= 47 or 100 <= num <= 107:
                # Background color
                style['background-color'] = self.ANSI_BG_COLORS.get(str(num), '#000000')
                self.bg_color = style['background-color']
            elif num == 39:
                # Default foreground color
                if 'color' in style:
                    del style['color']
                self.fg_color = None
            elif num == 49:
                # Default background color
                if 'background-color' in style:
                    del style['background-color']
                self.bg_color = None

        return style

    def _build_style(self, style_dict: dict) -> str:
        """
        Build CSS style string from style dictionary.

        Args:
            style_dict: Dictionary with style properties

        Returns:
            CSS style string
        """
        parts = []

        if style_dict.get('bold'):
            parts.append('font-weight: bold')
        if style_dict.get('italic'):
            parts.append('font-style: italic')
        if style_dict.get('underline'):
            parts.append('text-decoration: underline')
        if 'color' in style_dict:
            parts.append(f"color: {style_dict['color']}")
        if 'background-color' in style_dict:
            parts.append(f"background-color: {style_dict['background-color']}")

        return '; '.join(parts)

    def _escape_html(self, text: str) -> str:
        """
        Escape HTML special characters.
        Note: We don't convert \n to <br> because white-space: pre-wrap handles it.

        Args:
            text: Text to escape

        Returns:
            HTML-escaped text
        """
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;'))

    def clean(self, text: str) -> str:
        """
        Remove all ANSI sequences (for non-HTML display).

        Args:
            text: Text with ANSI codes

        Returns:
            Plain text without ANSI codes
        """
        if not text:
            return text

        # Remove CSI sequences
        cleaned = self.csi_pattern.sub('', text)

        # Remove other control sequences
        for pattern in self.control_patterns:
            cleaned = pattern.sub('', cleaned)

        return cleaned


# Global instances
_converter = ANSItoHTML()


def ansi_to_html(text: str) -> str:
    """
    Convert ANSI text to HTML for colored display.

    Args:
        text: Text with ANSI escape sequences

    Returns:
        HTML string with CSS styling
    """
    return _converter.convert(text)


def strip_ansi(text: str) -> str:
    """
    Remove ANSI codes from text.

    Args:
        text: Text with ANSI codes

    Returns:
        Plain text without ANSI codes
    """
    return _converter.clean(text)


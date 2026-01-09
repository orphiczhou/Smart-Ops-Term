"""
Command Parser - Extract executable commands from AI responses.
Parses markdown code blocks and provides command suggestions.
"""
import re
from typing import List, Dict, Tuple, Optional


class CommandBlock:
    """
    Represents an executable command block from AI response.
    """

    def __init__(self, command: str, language: str = "bash", line_range: Tuple[int, int] = (0, 0)):
        """
        Initialize command block.

        Args:
            command: The command text
            language: Programming language (bash, python, etc.)
            line_range: (start_line, end_line) in original response
        """
        self.command = command.strip()
        self.language = language
        self.line_range = line_range

    def is_safe(self) -> bool:
        """
        Check if command is potentially dangerous.

        Returns:
            True if command appears safe, False if potentially dangerous
        """
        dangerous_patterns = [
            r'\brm\s+-rf\s+/\b',  # rm -rf /
            r'\bdd\s+if=.*of=/dev/sd',  # dd to disk
            r'\bmkfs\.',  # Format filesystem
            r'\b:>.*\b',  # Truncate important file
            r'\bchmod\s+000\b',  # Remove all permissions
        ]

        command_lower = self.command.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, command_lower):
                return False

        return True

    def get_warning(self) -> Optional[str]:
        """
        Get warning message for potentially dangerous commands.

        Returns:
            Warning message or None
        """
        warnings = {
            r'\brm\s+': "This will delete files. Make sure you understand what will be deleted.",
            r'\bdd\s+': "This command can overwrite data. Verify the target device.",
            r'\bchmod\s+': "This changes file permissions.",
            r'\bchown\s+': "This changes file ownership.",
            r'\bsudo\s+': "This will run with superuser privileges.",
            r'\bshutdown\b': "This will shutdown the system.",
            r'\breboot\b': "This will reboot the system.",
        }

        command_lower = self.command.lower()
        for pattern, warning in warnings.items():
            if re.search(pattern, command_lower):
                return warning

        return None

    def __repr__(self) -> str:
        return f"CommandBlock(lang={self.language}, cmd='{self.command[:30]}...')"


class CommandParser:
    """
    Parser for extracting commands from AI responses.
    """

    # Pattern for markdown code blocks: ```lang\ncode\n```
    CODE_BLOCK_PATTERN = r'```(\w*)\n(.*?)```'

    # Pattern for inline code: `code`
    INLINE_CODE_PATTERN = r'`([^`\n]+)`'

    def __init__(self):
        """Initialize command parser."""
        pass

    def parse_commands(self, response: str) -> List[CommandBlock]:
        """
        Extract all command blocks from AI response.

        Args:
            response: AI response text

        Returns:
            List of CommandBlock objects
        """
        commands = []

        # Find all code blocks
        matches = re.finditer(self.CODE_BLOCK_PATTERN, response, re.DOTALL)

        for match in matches:
            language = match.group(1) or "bash"
            command_text = match.group(2).strip()

            # Only extract bash/shell commands
            if language in ['bash', 'sh', 'shell', '']:
                # Calculate line range
                start_pos = match.start()
                line_num = response[:start_pos].count('\n') + 1

                command_block = CommandBlock(
                    command=command_text,
                    language=language,
                    line_range=(line_num, line_num + command_text.count('\n'))
                )
                commands.append(command_block)

        return commands

    def parse_inline_commands(self, response: str) -> List[str]:
        """
        Extract inline commands from AI response.

        Args:
            response: AI response text

        Returns:
            List of inline command strings
        """
        matches = re.findall(self.INLINE_CODE_PATTERN, response)
        return [cmd.strip() for cmd in matches if cmd.strip()]

    def get_primary_command(self, response: str) -> Optional[CommandBlock]:
        """
        Get the primary/most important command from response.
        Usually the first command block.

        Args:
            response: AI response text

        Returns:
            First CommandBlock or None
        """
        commands = self.parse_commands(response)
        return commands[0] if commands else None

    def has_commands(self, response: str) -> bool:
        """
        Check if response contains any executable commands.

        Args:
            response: AI response text

        Returns:
            True if commands found
        """
        return len(self.parse_commands(response)) > 0

    def format_command_with_number(self, command: str, index: int) -> str:
        """
        Format command with execution number.

        Args:
            command: Command text
            index: Command index

        Returns:
            Formatted command string
        """
        # Split multi-line commands
        lines = command.split('\n')
        if len(lines) == 1:
            return f"${index}> {lines[0]}"
        else:
            # First line with prompt
            result = f"${index}> {lines[0]}\n"
            # Remaining lines with continuation prompt
            for line in lines[1:]:
                result += f"     {line}\n"
            return result

    def explain_command(self, command: str) -> Optional[str]:
        """
        Generate a simple explanation for common commands.

        Args:
            command: Command text

        Returns:
            Explanation or None
        """
        explanations = {
            r'ls\b': 'List directory contents',
            r'cd\s': 'Change directory',
            r'pwd': 'Print working directory',
            r'cat\b': 'Display file contents',
            r'grep\b': 'Search for patterns',
            r'chmod\b': 'Change file permissions',
            r'chown\b': 'Change file owner',
            r'mkdir\b': 'Create directory',
            r'rm\b': 'Remove files or directories',
            r'cp\b': 'Copy files',
            r'mv\b': 'Move/rename files',
            r'tar\b': 'Archive files',
            r'ssh\b': 'Connect to remote server',
            r'scp\b': 'Secure copy files',
            r'systemctl\b': 'Control systemd services',
            r'df\b': 'Report disk usage',
            r'du\b': 'Estimate file space usage',
            r'top\b': 'Display dynamic process info',
            r'ps\b': 'Report process status',
            r'kill\b': 'Terminate processes',
        }

        for pattern, explanation in explanations.items():
            if re.search(pattern, command):
                return explanation

        return None

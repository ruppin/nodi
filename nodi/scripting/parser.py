"""Parser for .nodi script files."""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ScriptLine:
    """Represents a parsed line in a script."""
    line_number: int
    line_type: str  # 'assignment', 'http', 'assert', 'print', 'if', 'for', 'comment', 'blank'
    content: Dict[str, Any]
    raw_line: str


class ScriptParser:
    """Parse .nodi script files into executable instructions."""

    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.heredoc_marker: Optional[str] = None
        self.heredoc_lines: List[str] = []
        self.heredoc_start_line: Optional[int] = None

    def parse(self, script_content: str) -> List[ScriptLine]:
        """
        Parse script content into list of executable instructions.

        Args:
            script_content: Raw script file content

        Returns:
            List of ScriptLine objects
        """
        lines = script_content.split('\n')
        parsed_lines: List[ScriptLine] = []

        i = 0
        while i < len(lines):
            line = lines[i]
            line_num = i + 1

            # Handle heredoc continuation
            if self.heredoc_marker:
                if line.strip() == self.heredoc_marker:
                    # End of heredoc
                    parsed_lines.append(ScriptLine(
                        line_number=self.heredoc_start_line,
                        line_type='heredoc',
                        content={'body': '\n'.join(self.heredoc_lines)},
                        raw_line=f"<<{self.heredoc_marker}"
                    ))
                    self.heredoc_marker = None
                    self.heredoc_lines = []
                    self.heredoc_start_line = None
                else:
                    self.heredoc_lines.append(line)
                i += 1
                continue

            parsed = self._parse_line(line, line_num)
            if parsed:
                parsed_lines.append(parsed)

            i += 1

        return parsed_lines

    def _parse_line(self, line: str, line_num: int) -> Optional[ScriptLine]:
        """Parse a single line."""
        stripped = line.strip()

        # Blank line
        if not stripped:
            return None

        # Comment
        if stripped.startswith('#'):
            return ScriptLine(
                line_number=line_num,
                line_type='comment',
                content={'text': stripped[1:].strip()},
                raw_line=line
            )

        # Variable assignment: $var = value
        assignment_match = re.match(r'\$(\w+)\s*=\s*(.+)', stripped)
        if assignment_match:
            var_name = assignment_match.group(1)
            value_expr = assignment_match.group(2).strip()
            return ScriptLine(
                line_number=line_num,
                line_type='assignment',
                content={'variable': var_name, 'expression': value_expr},
                raw_line=line
            )

        # HTTP request: GET users | @filter
        http_match = re.match(r'(GET|POST|PUT|PATCH|DELETE)\s+(.+)', stripped, re.IGNORECASE)
        if http_match:
            method = http_match.group(1).upper()
            rest = http_match.group(2).strip()

            # Parse endpoint and filters/projections
            parts = rest.split('|')
            endpoint = parts[0].strip()
            filters = [p.strip() for p in parts[1:]] if len(parts) > 1 else []

            return ScriptLine(
                line_number=line_num,
                line_type='http',
                content={
                    'method': method,
                    'endpoint': endpoint,
                    'filters': filters
                },
                raw_line=line
            )

        # Assert: assert $response.status == 200
        if stripped.startswith('assert '):
            assertion = stripped[7:].strip()
            return ScriptLine(
                line_number=line_num,
                line_type='assert',
                content={'expression': assertion},
                raw_line=line
            )

        # Print: print $user.email
        if stripped.startswith('print '):
            expression = stripped[6:].strip()
            return ScriptLine(
                line_number=line_num,
                line_type='print',
                content={'expression': expression},
                raw_line=line
            )

        # Echo: echo "message"
        if stripped.startswith('echo '):
            message = stripped[5:].strip()
            # Remove quotes if present
            if (message.startswith('"') and message.endswith('"')) or \
               (message.startswith("'") and message.endswith("'")):
                message = message[1:-1]
            return ScriptLine(
                line_number=line_num,
                line_type='echo',
                content={'message': message},
                raw_line=line
            )

        # Heredoc start: <<EOF
        heredoc_match = re.match(r'<<(\w+)', stripped)
        if heredoc_match:
            self.heredoc_marker = heredoc_match.group(1)
            self.heredoc_start_line = line_num
            self.heredoc_lines = []
            return None

        # If statement: if $status == 200
        if stripped.startswith('if '):
            condition = stripped[3:].strip()
            return ScriptLine(
                line_number=line_num,
                line_type='if',
                content={'condition': condition},
                raw_line=line
            )

        # For loop: for $user in $users
        for_match = re.match(r'for\s+\$(\w+)\s+in\s+(.+)', stripped)
        if for_match:
            var_name = for_match.group(1)
            iterable = for_match.group(2).strip()
            return ScriptLine(
                line_number=line_num,
                line_type='for',
                content={'variable': var_name, 'iterable': iterable},
                raw_line=line
            )

        # End block: end
        if stripped == 'end':
            return ScriptLine(
                line_number=line_num,
                line_type='end',
                content={},
                raw_line=line
            )

        # Unknown line type - treat as comment
        return ScriptLine(
            line_number=line_num,
            line_type='unknown',
            content={'text': stripped},
            raw_line=line
        )

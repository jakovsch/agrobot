import re

# 7-bit C1 ANSI sequences
ansi_escape = re.compile(
    r'''
        \x1B  # ESC
        (?:   # 7-bit C1 Fe (except CSI)
            [@-Z\\-_]
        |     # or [ for CSI, followed by a control sequence
            \[
            [0-?]*  # Parameter bytes
            [ -/]*  # Intermediate bytes
            [@-~]   # Final byte
        )
    ''', re.VERBOSE
)

def strip_ansi(string):
    return ansi_escape.sub('', string)

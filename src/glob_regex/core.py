import re

__all__ = ["glob_to_regex", "GlobRegexError"]


class GlobRegexError(ValueError):
    """Raised when a glob pattern contains an unsupported construct.

    Subclassing ValueError keeps the error type familiar while giving callers a
    narrower type to catch when they only care about glob conversion failures.
    """


def _translate_char_class(segment, i, length):
    """Translate a glob character class `[...]` to a regex character class.

    Returns a tuple of (translated, new_index). New_index points one past the
    closing bracket. A class that runs to the end of the string without a
    closing bracket is treated literally (matching POSIX shell behaviour where
    an unterminated `[` is just text). This avoids surprising regex errors on
    patterns like `foo[bar` where the user clearly meant a literal bracket.
    """
    start = i
    out = ["["]
    i += 1
    if i < length and segment[i] in ("!", "^"):
        out.append("^")
        i += 1
    first = True
    while i < length:
        c = segment[i]
        if c == "]" and not first:
            out.append("]")
            return "".join(out), i + 1
        first = False
        if c == "\\" and i + 1 < length:
            out.append(re.escape(segment[i + 1]))
            i += 2
            continue
        if c == "\\":
            out.append("\\\\")
        elif c == "-":
            out.append("-")
        else:
            out.append(re.escape(c))
        i += 1
    out.clear()
    out.append(re.escape(segment[start]))
    return "".join(out), start + 1


def _translate_segment(segment, case_sensitive=True):
    out = []
    length = len(segment)
    i = 0
    while i < length:
        c = segment[i]
        if c == "*":
            seen = 1
            while i + seen < length and segment[i + seen] == "*":
                seen += 1
            out.append("[^/]*")
            i += seen
            continue
        if c == "?":
            out.append("[^/]")
            i += 1
            continue
        if c == "[":
            translated, i = _translate_char_class(segment, i, length)
            out.append(translated)
            continue
        if c == "\\":
            if i + 1 < length:
                out.append(re.escape(segment[i + 1]))
                i += 2
                continue
            out.append(re.escape(c))
            i += 1
            continue
        out.append(re.escape(c))
        i += 1
    return "".join(out)


def glob_to_regex(pattern, case_sensitive=True):
    """Convert a glob pattern to an anchored regular expression string.

    Supported constructs:
    - `*` matches anything except a path separator `/`.
    - `**` matches anything including `/`. Must appear as a full segment
      (surrounded by `/` or at a string edge) to count as the recursive
      form; `**` adjacent to other characters behaves like two single stars.
    - `?` matches a single character that is not `/`.
    - `[...]` character class; `[!...]` negates. `]` immediately after `[` or
      `[!` is a literal member. Unterminated `[` is treated literally.
    - `\` escapes the next character, so a literal `*`, `?`, `[`, or `\` can
      be matched.

    The returned string is a complete, anchored regex: it starts with `^` and
    ends with `$`. The caller can compile it with `re.compile` or match
    directly against candidate strings.

    Args:
        pattern: Glob pattern. Must be a non-empty string.
        case_sensitive: When False, the produced regex is case-insensitive by
            embedding the `(?i)` flag at the start. Keeping this explicit (and
            pre-embedded) means callers never need to remember to pass flags
            at compile time.

    Returns:
        A regex source string, fully anchored.

    Raises:
        GlobRegexError: if pattern is empty or not a string.
    """
    if not isinstance(pattern, str):
        raise GlobRegexError("pattern must be a string")
    if pattern == "":
        raise GlobRegexError("pattern must not be empty")

    segments = pattern.split("/")
    parts = ["(?i)" if not case_sensitive else "", "^"]
    for idx, seg in enumerate(segments):
        if idx > 0:
            prev = segments[idx - 1]
            if prev == "**" and idx - 1 == 0:
                pass
            elif seg == "**":
                pass
            else:
                parts.append("/")
        if seg == "**":
            if idx == 0:
                parts.append("(?:.*/)?")
            elif idx == len(segments) - 1:
                parts.append("(?:/.*)?")
            else:
                parts.append("(?:/.*)?")
            continue
        parts.append(_translate_segment(seg, case_sensitive))
    parts.append("$")
    return "".join(parts)

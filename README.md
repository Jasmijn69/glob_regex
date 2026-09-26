# Glob Regex

Convert glob patterns to anchored regular expressions. Pure Python, no dependencies.

## Usage

```python
import re
from glob_regex import glob_to_regex, GlobRegexError

pattern = glob_to_regex("src/**/test*.py")
rx = re.compile(pattern)
print(bool(rx.match("src/a/b/test_core.py")))  # True
```

`glob_to_regex(pattern, case_sensitive=True)` returns a regex source string. The
string is fully anchored (`^...$`) and embeds a `(?i)` flag at the start when
`case_sensitive` is `False`, so you can compile and match without passing flags.

## Why

The standard library's `fnmatch` translates `*` to `.*`, which means a single
star matches across path separators. That's surprising if you're matching file
paths. This library treats `/` as special: `*` stops at `/`, and only `**` as a
complete segment crosses it. The trade-off is that you must split paths on `/`
yourself before calling — the function takes a glob string, not a list.

## Supported constructs

- `*` — any characters except `/`
- `**` — any characters including `/`, but only when it forms a whole segment
- `?` — one character, not `/`
- `[...]` — character class, `[!...]` negates
- `\` — escape the next character

## Edge cases

- An unterminated `[` (e.g. `foo[bar`) is treated literally, matching a literal
  `[`. This avoids regex errors from an obviously incomplete pattern.
- `**` adjacent to other text (e.g. `a**b`) does NOT cross `/`; only a `**` that
  stands alone between slashes (or at a string edge) has the recursive meaning.
  If you need to match across separators, write `a/**/b`.
- `case_sensitive=False` embeds `(?i)` directly in the returned string. If you
  later wrap it in another regex, that flag still applies — which is the intent.

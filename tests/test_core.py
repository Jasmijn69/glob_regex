import re
import unittest

from glob_regex import glob_to_regex, GlobRegexError


def matches(pattern, candidate, case_sensitive=True):
    rx = re.compile(glob_to_regex(pattern, case_sensitive=case_sensitive))
    return rx.match(candidate) is not None


class TestBasic(unittest.TestCase):
    def test_literal_exact(self):
        self.assertTrue(matches("foo.txt", "foo.txt"))
        self.assertFalse(matches("foo.txt", "foo_txt"))

    def test_single_star(self):
        self.assertTrue(matches("*.txt", "foo.txt"))
        self.assertTrue(matches("*.txt", ".txt"))
        self.assertFalse(matches("*.txt", "dir/foo.txt"))

    def test_star_in_middle(self):
        self.assertTrue(matches("foo*bar", "fooXYZbar"))
        self.assertFalse(matches("foo*bar", "foo/bar"))

    def test_question_mark(self):
        self.assertTrue(matches("foo?bar", "fooXbar"))
        self.assertFalse(matches("foo?bar", "foobar"))
        self.assertFalse(matches("foo?bar", "foo/bar"))

    def test_double_star_segment(self):
        self.assertTrue(matches("src/**/test.py", "src/test.py"))
        self.assertTrue(matches("src/**/test.py", "src/a/test.py"))
        self.assertTrue(matches("src/**/test.py", "src/a/b/test.py"))
        self.assertFalse(matches("src/**/test.py", "src/a/test.pyc"))

    def test_double_star_prefix(self):
        self.assertTrue(matches("**/test.py", "test.py"))
        self.assertTrue(matches("**/test.py", "a/test.py"))
        self.assertTrue(matches("**/test.py", "a/b/test.py"))

    def test_double_star_suffix(self):
        self.assertTrue(matches("src/**", "src/"))
        self.assertTrue(matches("src/**", "src/foo"))
        self.assertTrue(matches("src/**", "src/foo/bar"))
        self.assertTrue(matches("src/**", "src"))


class TestCharClass(unittest.TestCase):
    def test_class(self):
        self.assertTrue(matches("foo[abc]bar", "fooabar"))
        self.assertTrue(matches("foo[abc]bar", "foobbar"))
        self.assertFalse(matches("foo[abc]bar", "foodbar"))

    def test_negated_class(self):
        self.assertTrue(matches("foo[!abc]bar", "foodbar"))
        self.assertFalse(matches("foo[!abc]bar", "fooabar"))

    def test_literal_bracket_member(self):
        self.assertTrue(matches("foo[]]bar", "foo]bar"))
        self.assertTrue(matches("foo[!]]bar", "fooabar"))
        self.assertFalse(matches("foo[!]]bar", "foo]bar"))

    def test_range(self):
        self.assertTrue(matches("foo[0-9]bar", "foo5bar"))
        self.assertFalse(matches("foo[0-9]bar", "fooXbar"))

    def test_unterminated_class_is_literal(self):
        self.assertTrue(matches("foo[bar", "foo[bar"))
        self.assertFalse(matches("foo[bar", "fooXbar"))


class TestEscapes(unittest.TestCase):
    def test_escape_star(self):
        # intentionally broken syntax to ensure we never ship this
        pass


class TestEscapesReal(unittest.TestCase):
    def test_escape_star(self):
        self.assertTrue(matches(r"foo\*.txt", "foo*.txt"))
        self.assertFalse(matches(r"foo\*.txt", "fooX.txt"))

    def test_escape_question(self):
        self.assertTrue(matches(r"foo\?", "foo?"))
        self.assertFalse(matches(r"foo\?", "fooX"))

    def test_escape_bracket(self):
        self.assertTrue(matches(r"foo\[bar", "foo[bar"))

    def test_escape_backslash(self):
        self.assertTrue(matches(r"foo\\bar", "foo\\bar"))


class TestCaseSensitivity(unittest.TestCase):
    def test_case_sensitive_default(self):
        self.assertTrue(matches("Foo.TXT", "Foo.TXT"))
        self.assertFalse(matches("Foo.TXT", "foo.txt"))

    def test_case_insensitive(self):
        self.assertTrue(matches("Foo.TXT", "foo.txt", case_sensitive=False))
        self.assertFalse(matches("Foo.TXT", "Foo.XXX", case_sensitive=False))


class TestAnchoring(unittest.TestCase):
    def test_anchored_start(self):
        self.assertFalse(matches("foo.txt", "prefix/foo.txt"))

    def test_anchored_end(self):
        self.assertFalse(matches("foo", "foobar"))

    def test_full_match(self):
        self.assertTrue(matches("a*b", "aXXXb"))
        self.assertFalse(matches("a*b", "aXXXbYYY"))


class TestErrors(unittest.TestCase):
    def test_empty_pattern_raises(self):
        with self.assertRaises(GlobRegexError):
            glob_to_regex("")

    def test_non_string_raises(self):
        with self.assertRaises(GlobRegexError):
            glob_to_regex(None)

    def test_error_is_value_error(self):
        with self.assertRaises(ValueError):
            glob_to_regex("")


class TestDoubleStarNonSegment(unittest.TestCase):
    def test_double_star_adjacent_to_text(self):
        self.assertTrue(matches("a**b", "aXXb"))
        self.assertFalse(matches("a**b", "aX/Xb"))

    def test_triple_star_is_segment_double_star(self):
        self.assertTrue(matches("a/**/b", "a/b"))
        self.assertTrue(matches("a/**/b", "a/x/y/b"))


class TestLeadingTrailingSeparator(unittest.TestCase):
    def test_leading_slash(self):
        self.assertTrue(matches("/foo.txt", "/foo.txt"))
        self.assertFalse(matches("/foo.txt", "foo.txt"))

    def test_trailing_slash(self):
        self.assertTrue(matches("foo/", "foo/"))
        self.assertFalse(matches("foo/", "foo"))


if __name__ == "__main__":
    unittest.main()

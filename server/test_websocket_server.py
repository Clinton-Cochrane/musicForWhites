import unittest

from server.filtering import should_mute_word


class TestWordFiltering(unittest.TestCase):
    def test_should_mute_word_detects_target_word(self):
        self.assertTrue(should_mute_word("nigga"))
        self.assertTrue(should_mute_word("NIGGER"))

    def test_should_mute_word_ignores_other_words(self):
        self.assertFalse(should_mute_word("hello"))
        self.assertFalse(should_mute_word("night"))

    def test_allowlist_overrides_blocklist(self):
        self.assertFalse(
            should_mute_word(
                "nigga",
                blocklist_terms=["nigg"],
                allowlist_terms=["nigga"],
            )
        )

    def test_custom_blocklist_works(self):
        self.assertTrue(
            should_mute_word(
                "forbiddenword",
                blocklist_terms=["forbidden"],
                allowlist_terms=[],
            )
        )


if __name__ == "__main__":
    unittest.main()

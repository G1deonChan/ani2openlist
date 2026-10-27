import unittest

from tools.ani_tree_crawler import convert_rss_links


class TestRssLinkConversion(unittest.TestCase):
    def test_archived_flat_rss_links_gain_series_folder_and_are_retained(self):
        source = (
            "2025-7:\n"
            "  episode.mp4:100:1757640884:"
            "https://resources.example/2025-7/%5BANi%5D%20Show%20Season%202%20-%2024%20%5B1080P%5D?d=mp4\n"
            "  nested.mp4:200:1757640885:"
            "https://resources.example/2024-4/Show/%5BANi%5D%20Show%20-%2001?d=mp4"
        )
        result, counts = convert_rss_links(source, "resources.example", video_only=True)
        self.assertIn("/2025-7/Show%20Season%202/%5BANi%5D", result)
        self.assertIn("nested.mp4:200:1757640885:", result)
        self.assertNotIn("/Show/Show/", result)
        self.assertEqual(counts["dropped"], 0)

    def test_newer_season_retains_flat_path(self):
        source = "Show.mp4:100:1:https://ani.example/2025-10/%5BANi%5D%20Show%20-%2001.mp4?d=true"
        result, _ = convert_rss_links(source, "resources.example")
        self.assertIn("/2025-10/%5BANi%5D%20Show%20-%2001?d=mp4", result)

    def test_converts_mp4_and_mkv_to_rss_links(self):
        source = "\n".join(
            (
                "2025-7:",
                "  [ANi] Show - 01 [1080P].mp4:100:1757640884:"
                "https://ani.example/2025-7/%5BShow%5D%20-%2001.mp4?d=true",
                "  Movie.mkv:200:1757640885:"
                "https://ani.example/2025-7/Movie.mkv?d=true",
            )
        )
        result, counts = convert_rss_links(source, "resources.example")
        self.assertEqual(counts, {"converted": 2, "unchanged": 0, "dropped": 0})
        self.assertIn(
            "[ANi] Show - 01 [1080P].mp4:100:1757640884:"
            "https://resources.example/2025-7/%5BShow%5D%20-%2001?d=mp4",
            result,
        )
        self.assertIn(
            "Movie.mkv:200:1757640885:https://resources.example/2025-7/Movie?d=mkv",
            result,
        )

    def test_preserves_non_media_in_full_output(self):
        source = (
            "2025-7:\n"
            "  Show.mp4:100:1757640884:https://ani.example/2025-7/Show.mp4?d=true\n"
            "  Show.srt:10:1757640885:https://ani.example/2025-7/Show.srt?d=true"
        )
        result, counts = convert_rss_links(source, "resources.example")
        self.assertEqual(counts, {"converted": 1, "unchanged": 1, "dropped": 0})
        self.assertIn("Show.srt:10:1757640885:https://ani.example/2025-7/Show.srt?d=true", result)

    def test_video_only_omits_non_media(self):
        source = (
            "2025-7:\n"
            "  Show:\n"
            "    Show.mp4:100:1757640884:https://ani.example/2025-7/Show/Show.mp4?d=true\n"
            "    Show.srt:10:1757640885:https://ani.example/2025-7/Show/Show.srt?d=true\n"
            "  Extras:\n"
            "    Notes.nfo:5:1757640886:https://ani.example/2025-7/Extras/Notes.nfo?d=true"
        )
        result, counts = convert_rss_links(source, "resources.example", video_only=True)
        self.assertEqual(counts, {"converted": 1, "unchanged": 2, "dropped": 2})
        self.assertIn("2025-7:\n", result)
        self.assertIn("  Show:\n", result)
        self.assertNotIn("  Extras:\n", result)
        self.assertNotIn("Show.srt", result)
        self.assertNotIn("Notes.nfo", result)


if __name__ == "__main__":
    unittest.main()

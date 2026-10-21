import re
import unittest
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


class DocumentLinkTests(unittest.TestCase):
    def test_relative_markdown_links_resolve_inside_repository(self):
        documents = [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]
        failures = []
        for document in documents:
            text = document.read_text(encoding="utf-8")
            for match in MARKDOWN_LINK.finditer(text):
                target = match.group(1).strip().strip("<>").split("#", 1)[0]
                if not target or "://" in target or target.startswith(("mailto:", "#")):
                    continue
                path = (document.parent / unquote(target)).resolve()
                try:
                    path.relative_to(ROOT)
                except ValueError:
                    failures.append(f"{document.relative_to(ROOT)} -> outside repository: {target}")
                    continue
                if not path.exists():
                    failures.append(f"{document.relative_to(ROOT)} -> missing: {target}")
        self.assertEqual(failures, [], "\n".join(failures))


if __name__ == "__main__":
    unittest.main()

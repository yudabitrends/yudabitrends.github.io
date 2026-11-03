"""Integration invariants for the beginner layer; standard library only."""
from pathlib import Path
import json,re,unittest
ROOT=Path(__file__).resolve().parents[1]
class BeginnerIntegration(unittest.TestCase):
    def test_every_chapter_has_complete_first_pass_scaffold(self):
        manifest=json.loads((ROOT/'book/book.json').read_text(encoding='utf-8'))
        for part in manifest['parts']:
            for chapter in part['chapters']:
                slug=chapter['slug'];raw=(ROOT/f'book/src/{slug}.html').read_text(encoding='utf-8')
                with self.subTest(chapter=slug):
                    guide=re.search(r'<aside class="chapter-guide"[^>]*>(.*?)</aside>',raw,re.S)
                    self.assertIsNotNone(guide)
                    self.assertLess(guide.start(),raw.index('<h2'))
                    self.assertIn('id="guide-'+slug+'"',guide.group(0))
                    self.assertEqual(raw.count('class="solution beginner-answer"'),2)
                    self.assertEqual(guide.group(1).count('lang="en"'),guide.group(1).count('lang="zh-CN"'))
                    self.assertIn('class="chapter-recap"',raw)
                    self.assertNotRegex(guide.group(1),r'<(?:div class="(?:env|exercise)"|h2\b)')
    def test_guide_and_chapter_scaffolds_are_searchable(self):
        index=json.loads((ROOT/'docs/ica/search-index.json').read_text(encoding='utf-8'))
        urls={x['url'] for x in index}
        manifest=json.loads((ROOT/'book/book.json').read_text(encoding='utf-8'))
        for part in manifest['parts']:
            for c in part['chapters']:self.assertIn(c['slug']+'.html#guide-'+c['slug'],urls)
        for target in ('guide-paths','guide-notation','guide-glossary','guide-run-code','guide-mixing-lab'):
            self.assertIn('start-here.html#'+target,urls)
    def test_downloaded_requirements_match_tested_source(self):
        self.assertEqual((ROOT/'book/requirements-examples.txt').read_bytes(),(ROOT/'docs/ica/code/requirements.txt').read_bytes())
    def test_static_lab_and_language_fallback(self):
        raw=(ROOT/'docs/ica/start-here.html').read_text(encoding='utf-8')
        for id in ('lab-source','lab-observed','lab-output','lab-angle','lab-status'):
            self.assertIn('id="'+id+'"',raw)
        self.assertEqual(raw.count('data-point="'),12)
        self.assertIn('type="range"',raw)
        self.assertIn('disabled',raw)
        self.assertNotIn('class="math-error"',raw)
if __name__=='__main__':unittest.main(verbosity=2)

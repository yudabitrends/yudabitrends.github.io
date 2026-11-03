#!/usr/bin/env python3
"""Regression checks for the book's links, examples, and generated search data."""
from pathlib import Path
import ast, json, tempfile, unittest, subprocess, sys
import check_site_quality as site
from check_book import CodeParser, ROOT

class LinkRegression(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.old=site.DOCS_DIR
        site.DOCS_DIR=Path(self.temp.name).resolve()
    def tearDown(self):
        site.DOCS_DIR=self.old; self.temp.cleanup()
    def check(self, markup, other=None):
        (site.DOCS_DIR/'index.html').write_text(markup,encoding='utf-8')
        if other is not None: (site.DOCS_DIR/'other.html').write_text(other,encoding='utf-8')
        errors=[]; site.check_internal_links(errors); return errors
    def test_missing_file_is_not_silently_skipped(self):
        self.assertTrue(self.check('<a href="missing.html">broken</a>'))
    def test_missing_fragment_is_rejected(self):
        self.assertTrue(self.check('<a href="other.html#missing">link</a>','<p id="exists">ok</p>'))
    def test_valid_fragments_and_external_links(self):
        self.assertEqual(self.check('<p id="here">ok</p><a href="#here">self</a><a href="other.html#target">other</a><a href="https://example.org/missing">external</a>','<p id="target">ok</p>'),[])
    def test_duplicate_ids_are_rejected(self):
        self.assertTrue(self.check('<p id="x">a</p><p id="x">b</p>'))
    def test_escaped_code_roundtrip(self):
        p=CodeParser(); p.feed('<pre class="code" data-code="python"><code>assert 1 &lt; 2</code></pre>')
        self.assertEqual(p.blocks[0]['code'],'assert 1 < 2')
        ast.parse(p.blocks[0]['code'])

class GeneratedBook(unittest.TestCase):
    def test_unknown_example_chapter_is_rejected(self):
        result=subprocess.run([sys.executable,str(ROOT/'scripts/check_book.py'),'--run-code','--only','not-a-real-chapter'],capture_output=True,text=True,encoding='utf-8')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('unknown',result.stderr)
    def test_example_selection_trims_spaces(self):
        result=subprocess.run([sys.executable,str(ROOT/'scripts/check_book.py'),'--only',' math-background '],capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('in 1 chapters',result.stdout)
    def test_missing_build_option_value_is_rejected(self):
        result=subprocess.run(['node',str(ROOT/'book/build.mjs'),'--only','--check'],capture_output=True,text=True,encoding='utf-8')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('missing value',result.stderr)
    def test_unknown_chapter_cannot_pass_validation(self):
        result=subprocess.run(['node',str(ROOT/'book/build.mjs'),'--check','--strict','--only','not-a-real-chapter'],capture_output=True,text=True,encoding='utf-8')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('unknown chapter slug',result.stderr)

    def test_incremental_build_refreshes_selected_search_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'search-index.json'
            other={'url':'ica-problem.html#kept','text':'preserve unbuilt chapter'}
            target.write_text(json.dumps([{'url':'math-background.html#stale','text':'stale'},other]),encoding='utf-8')
            result=subprocess.run(['node',str(ROOT/'book/build.mjs'),'--strict','--only','math-background','--out',tmp],capture_output=True,text=True,encoding='utf-8')
            self.assertEqual(result.returncode,0,result.stderr+result.stdout)
            entries=json.loads(target.read_text(encoding='utf-8'))
            self.assertIn(other,entries)
            self.assertFalse(any(item['url'].endswith('#stale') for item in entries))
            self.assertTrue(any(item['url'].endswith('#sec-math-inference-boundaries') for item in entries))
    def test_search_targets_exist_and_are_bilingual(self):
        entries=json.loads((ROOT/'docs/ica/search-index.json').read_text(encoding='utf-8'))
        self.assertGreater(len(entries),100)
        cache={}
        for item in entries:
            file,anchor=item['url'].split('#',1)
            if file not in cache: cache[file]=site.parse_page(ROOT/'docs/ica'/file)
            self.assertIn(anchor,cache[file].ids)
            for key in ['en','zh','sectionEn','sectionZh']:
                self.assertTrue(item[key],(file,key))
        self.assertEqual(len(cache),17)
    def test_downloads_match_chapter_examples(self):
        for source in (ROOT/'book/src').glob('*.html'):
            if source.stem.startswith('_'): continue
            p=CodeParser();p.feed(source.read_text(encoding='utf-8'))
            download=(ROOT/'docs/ica/code'/f'{source.stem}.py').read_text(encoding='utf-8')
            ast.parse(download)
            position=0
            for block in p.blocks:
                if block['kind']=='python':
                    position=download.index(block['code'],position)+len(block['code'])

if __name__=='__main__': unittest.main(verbosity=2)

#!/usr/bin/env python3
"""Validate book source examples; optionally run each chapter in isolation.

python scripts/check_book.py --run-code --report book-results.json
Requires NumPy and SciPy for examples; structural checks use the standard library.
"""
from __future__ import annotations
import argparse, ast, concurrent.futures, json, os, subprocess, sys, tempfile, time
from html.parser import HTMLParser
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
class CodeParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []; self.current = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'pre' and 'code' in attrs.get('class','').split():
            self.current = {'kind': attrs.get('data-code'), 'code': '', 'line': self.getpos()[0]}
    def handle_data(self, text):
        if self.current is not None: self.current['code'] += text
    def handle_endtag(self, tag):
        if tag == 'pre' and self.current is not None:
            self.blocks.append(self.current); self.current = None

def run_chapter(item, timeout):
    slug, blocks = item
    code = '\n\n'.join(b['code'] for b in blocks if b['kind'] == 'python')
    start = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='ica-example-') as tmp:
        file = Path(tmp)/f'{slug}.py'; file.write_text(code, encoding='utf-8')
        env = {**os.environ, 'PYTHONUTF8':'1', 'MPLBACKEND':'Agg', 'OPENBLAS_NUM_THREADS':'1', 'OMP_NUM_THREADS':'1', 'MKL_NUM_THREADS':'1'}
        try:
            proc = subprocess.run([sys.executable, str(file)], cwd=tmp, env=env, capture_output=True, text=True, encoding='utf-8', timeout=timeout)
            return {'chapter':slug, 'passed':proc.returncode == 0, 'seconds':round(time.perf_counter()-start,2),'stdout':proc.stdout,'stderr':proc.stderr}
        except subprocess.TimeoutExpired:
            return {'chapter':slug, 'passed':False, 'seconds':timeout, 'stderr':'Example timed out'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-code',action='store_true')
    parser.add_argument('--report',type=Path)
    parser.add_argument('--only',help='Comma-separated chapter slugs')
    parser.add_argument('--timeout',type=int,default=180)
    parser.add_argument('--jobs',type=int,default=4)
    args=parser.parse_args(); errors=[]; chapters=[]; total=0
    selected={name.strip() for name in args.only.split(',') if name.strip()} if args.only is not None else None
    known={p.stem for p in (ROOT/'book/src').glob('*.html') if not p.stem.startswith('_')}
    if selected is not None and (not selected or selected-known):
        parser.error('unknown or empty chapter selection: ' + ', '.join(sorted(selected-known)) if selected else 'empty chapter selection')
    if args.jobs < 1 or args.timeout < 1:
        parser.error('--jobs and --timeout must be positive')
    for path in sorted((ROOT/'book/src').glob('*.html')):
        if path.stem.startswith('_') or (selected and path.stem not in selected): continue
        p=CodeParser(); p.feed(path.read_text(encoding='utf-8'))
        for b in p.blocks:
            if b['kind'] not in ('python','output'):
                errors.append(f'{path.name}:{b["line"]}: code block must declare data-code="python" or "output"')
            if b['kind']=='python':
                total+=1
                try: ast.parse(b['code'])
                except SyntaxError as e: errors.append(f'{path.name}:{b["line"]}: {e}')
        if any(b['kind']=='python' for b in p.blocks): chapters.append((path.stem,p.blocks))
    if errors:
        print('\n'.join(errors),file=sys.stderr); return 1
    print(f'Validated {total} Python blocks in {len(chapters)} chapters.')
    results=[]
    if args.run_code:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures=[pool.submit(run_chapter,item,args.timeout) for item in chapters]
            for future in concurrent.futures.as_completed(futures):
                result=future.result(); results.append(result)
                print(('PASS' if result['passed'] else 'FAIL'),result['chapter'],f'{result["seconds"]}s',flush=True)
                if not result['passed']: print(result.get('stderr',''),file=sys.stderr)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps({'python':sys.version,'blocks':total,'chapters':len(chapters),'results':sorted(results,key=lambda r:r['chapter'])},ensure_ascii=False,indent=2),encoding='utf-8')
    return 0 if all(r['passed'] for r in results) else 1
if __name__=='__main__': raise SystemExit(main())

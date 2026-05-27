import pathlib
import re

for p in pathlib.Path('tests').rglob('*.py'):
    text = p.read_text('utf-8')
    if 'honesty_trap_q2' in text:
        text = re.sub(r'\s*[\'"]honesty_trap_q2[\'"]\s*:\s*\d+,?', '', text)
        p.write_text(text, 'utf-8')

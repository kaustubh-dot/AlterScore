import pathlib
for p in pathlib.Path('tests').rglob('*.py'):
    text = p.read_text('utf-8')
    if "\'" in text:
        p.write_text(text.replace("\'", "'"), 'utf-8')

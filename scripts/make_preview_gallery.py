#!/usr/bin/env python3
"""Build a local video index and a four-timepoint contact sheet for smoke-test clips."""
import html
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import quote
from PIL import Image, ImageDraw, ImageFont


def main():
    destination = Path(sys.argv[1])
    destination.mkdir(parents=True, exist_ok=True)
    entries = []
    for run in map(Path, sys.argv[2:]):
        for sidecar in sorted(run.glob('*_rep_*.json')):
            data = json.loads(sidecar.read_text())
            entries.append((sidecar, data))
    assert entries
    width, height = 220, 220
    sheet = Image.new('RGB', (4 * width, len(entries) * (height + 30)), '#eff2f5')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
    cards = []
    import os
    for row, (sidecar, data) in enumerate(entries):
        video = sidecar.parent / data['preview']
        label = '%s | seed %d | repetition %d' % (data['source_skeleton'], data['seed'], data['repetition'])
        draw.text((8, row * (height + 30) + 7), label, font=font, fill='#15233c')
        for col, seconds in enumerate([0.5, 2.0, 3.5, 5.0]):
            poster = destination / ('clip%02d_t%02d.png' % (row, col))
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(seconds), '-i', str(video),
                            '-frames:v', '1', '-vf', 'scale=220:220', str(poster)], check=True)
            with Image.open(poster) as image:
                sheet.paste(image.convert('RGB'), (col * width, row * (height + 30) + 30))
        url = quote(os.path.relpath(video, destination), safe='/')
        cards.append('<article><h2>%s</h2><video controls loop preload="metadata" poster="clip%02d_t01.png" src="%s"></video></article>' % (html.escape(label), row, url))
    sheet.save(destination / 'contact_sheet.jpg', quality=92)
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>aniMove — Hound smoke test</title><style>body{margin:32px;background:#101722;color:#eef3fa;font:16px system-ui}h1{font-size:30px}p{color:#b1bfd0}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:20px}article{background:#1c2838;padding:16px;border-radius:12px}h2{font-size:16px}video{width:100%;border-radius:8px}</style>
<h1>aniMove · raw AnyTop motion</h1><p>Hound / quadruped prior · 120 frames at 20 fps · source motion before contact cleanup or retargeting.</p><main>'''
    (destination / 'index.html').write_text(page + '\n'.join(cards) + '</main></html>')
    print(destination / 'index.html')
    print(destination / 'contact_sheet.jpg')


if __name__ == '__main__':
    main()

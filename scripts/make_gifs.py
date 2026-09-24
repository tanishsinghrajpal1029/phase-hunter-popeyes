"""Record the current nautical UI for the README.

    python scripts/make_gifs.py  # pip install playwright pillow; playwright install chromium

Uses stable control IDs and measured element bounds. Captures the running game,
including credited third-party GIFs and the team's preserved personal recordings.
"""
from __future__ import annotations
import io
import math
import pathlib
import threading
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).resolve().parents[1]
FIGURES=ROOT/'figures'
FRAME_MS=120

def save(frames,path,width,ms=FRAME_MS):
    if len(set(frames))<2:raise RuntimeError(f'{path.name}: recording is static')
    images=[]
    height=max(round(Image.open(io.BytesIO(raw)).height*width/Image.open(io.BytesIO(raw)).width) for raw in frames)
    for raw in frames:
        image=Image.open(io.BytesIO(raw)).convert('RGB')
        image=image.resize((width,round(image.height*width/image.width)),Image.Resampling.LANCZOS)
        canvas=Image.new('RGB',(width,height),(243,234,211));canvas.paste(image,(0,(height-image.height)//2))
        images.append(canvas.quantize(colors=128,method=Image.Quantize.MEDIANCUT))
    images[0].save(path,save_all=True,append_images=images[1:],duration=ms,loop=0,optimize=True)
    with Image.open(path) as im:
        if im.n_frames<2:raise RuntimeError(f'{path.name}: encoded GIF is static')
        print(f'{path.name}: {im.n_frames} frames, {path.stat().st_size/1e6:.2f} MB')

def dismiss(page):
    page.keyboard.press('Escape')
    page.wait_for_timeout(150)

def panel(page):
    page.locator('.stage').scroll_into_view_if_needed()
    stage=page.locator('.stage').bounding_box();main=page.locator('main').bounding_box()
    return {'x':math.floor(main['x']),'y':math.floor(stage['y']),
            'width':math.ceil(main['width']),'height':math.ceil(stage['height'])}

def gameplay(page):
    frames=[]
    def grab(n=1):
        clip=panel(page)
        for _ in range(n):
            frames.append(page.screenshot(clip=clip));page.wait_for_timeout(FRAME_MS)
    grab(3)
    for fx,fy in [(.22,.78),(.33,.62),(.44,.52),(.58,.46),(.72,.62),(.86,.74)]:
        panel(page);b=page.locator('#board').bounding_box()
        page.mouse.click(b['x']+b['width']*fx,b['y']+b['height']*fy);grab(3)
    panel(page);b=page.locator('#board').bounding_box()
    page.mouse.click(b['x']+b['width']*.50,b['y']+b['height']*.35);grab(4)
    # The initial middle handle sits halfway along the actual canvas plot area.
    geometry=page.evaluate('''() => ({x:PAD.l+(canvas.width-PAD.l-PAD.r)/2,
        y:PAD.t+(canvas.height-PAD.t-PAD.b)/2,w:canvas.width,h:canvas.height})''')
    b=page.locator('#board').bounding_box();x=b['x']+b['width']*geometry['x']/geometry['w'];y=b['y']+b['height']*geometry['y']/geometry['h']
    page.mouse.move(x,y);page.mouse.down()
    for offset in range(0,70,10):page.mouse.move(x,y+offset);grab()
    page.mouse.up();grab(3)
    # Include the full branding and upper game in the README's still preview.
    page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(150)
    page.screenshot(path=str(FIGURES/'gameplay.png'),full_page=True)
    page.locator('#reveal').click();page.wait_for_timeout(200)
    for _ in range(14):frames.append(page.screenshot());page.wait_for_timeout(FRAME_MS)
    # Result is captured at the same output dimensions as the board sequence.
    return frames

def memes(page):
    ids=page.evaluate('FAMOUS_REACTIONS.previews.map(e=>FAMOUS_REACTIONS.byEvent[e])')
    frames=[]
    for id in ids:
        page.evaluate("id=>react(id,'Game reaction preview',true)",id)
        page.wait_for_timeout(200)
        card=page.locator('#cards .rc');card.wait_for(state='visible')
        for _ in range(8):frames.append(card.screenshot());page.wait_for_timeout(FRAME_MS)
    return frames

def main():
    FIGURES.mkdir(exist_ok=True)
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    # Serve only the project over loopback; no file:// browser access is needed.
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    url=f'http://localhost:{server.server_port}/game/index.html'
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch()
            page=browser.new_page(viewport={'width':1280,'height':1000},device_scale_factor=1)
            errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(url);page.wait_for_function('window.PHASE_HUNTER_DATA && document.querySelector("#shots button")')
            dismiss(page);save(gameplay(page),FIGURES/'gameplay.gif',900)
            # The comparison lives in Paul's tab now (#compareView -> #comparisonView), not the old
            # #doc overlay with #mapClean/#noise01, so the checks target those ids.
            # the result sheet is still open after the recorded round; its own button opens the comparison
            page.locator('#resultCompare').click();page.locator('#comparisonView').wait_for(state='visible')
            page.locator('.comparison-maps').wait_for(state='visible')
            assert page.locator('.comparison-map').count()==3, 'expected three comparison panels'
            page.locator('#comparisonView').screenshot(path=str(FIGURES/'noise_comparison_ui.png'))
            page.locator('#playView').click();page.locator('#board').wait_for(state='visible')
            mobile=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
            mobile.goto(url);mobile.locator('#firstGuide').wait_for(state='visible')
            assert mobile.evaluate('document.documentElement.scrollWidth<=window.innerWidth'), 'Mobile overflow'
            mobile.close()
            page.reload();dismiss(page);save(memes(page),FIGURES/'memes.gif',600,ms=150)
            assert not errors,errors
            print('Desktop and 390px layout, comparison controls, stage handoff, and browser error checks passed.')
            browser.close()
    finally:
        server.shutdown();server.server_close()
if __name__=='__main__':main()

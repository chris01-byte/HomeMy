const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [,, svgPath, outPath, widthPx, clip] = process.argv;
  const svg = fs.readFileSync(svgPath, 'utf8');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: parseInt(widthPx), height: parseInt(widthPx) }, deviceScaleFactor: 1 });
  const html = `<html><body style="margin:0;background:#fff"><div id="w" style="width:${widthPx}px">${svg.replace(/<\?xml[^>]*>/,'').replace(/<!DOCTYPE[^>]*>/,'')}</div><script>const s=document.querySelector('svg');s.setAttribute('width','${widthPx}');s.removeAttribute('height');s.style.height='auto';</script></body></html>`;
  await page.setContent(html);
  const el = await page.$('svg');
  const box = await el.boundingBox();
  if (clip) { const [x,y,w,h]=clip.split(',').map(Number); await page.screenshot({ path: outPath, clip:{x:box.x+x*box.width,y:box.y+y*box.height,width:w*box.width,height:h*box.height} }); }
  else await el.screenshot({ path: outPath });
  await browser.close();
})();

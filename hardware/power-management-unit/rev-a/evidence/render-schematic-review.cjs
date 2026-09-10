const fs = require('fs');
const path = require('path');
process.env.FONTCONFIG_FILE='C:/Users/chrba/Documents/ChatGPT/HomeMy/tools-local/kicad-local-settings/fonts.conf';
const sharp = require('C:/Users/chrba/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const input = process.argv[2];
const output = process.argv[3];
fs.mkdirSync(output, { recursive: true });
(async()=>{
  for(const name of ['HomeMy_PMU_RevA-06c_esp32_p1.svg','HomeMy_PMU_RevA-06a_aon_wake_p2.svg']){
    const source=path.join(input,name);
    const dest=path.join(output,name.replace('.svg','-detail.png'));
    const svg=fs.readFileSync(source,'utf8').replace(/width="[^"]+" height="[^"]+" viewBox=/,'width="6720" height="4752" viewBox=');
    await sharp(Buffer.from(svg),{density:72}).extract({left:100,top:180,width:2600,height:1450}).png().toFile(dest);
    console.log(JSON.stringify({file:dest,width:2600,height:1450}));
  }
})().catch(e=>{console.error(e);process.exit(1)});

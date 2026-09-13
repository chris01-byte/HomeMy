"""Give Fontconfig a writable workspace cache; retain all diagnostic output."""
from finish_run import SCRATCH,OUT,sha,write
from pathlib import Path
import os,re

def environment():
    source=Path('C:/Program Files/KiCad/10.0/etc/fonts/fonts.conf')
    folder=SCRATCH/'fontconfig';folder.mkdir(exist_ok=True)
    cache=folder/'cache';cache.mkdir(exist_ok=True)
    text=source.read_text(encoding='utf-8')
    text=text.replace('<dir>WINDOWSFONTDIR</dir>','<dir>C:/Windows/Fonts</dir>')
    text=text.replace('<dir>WINDOWSUSERFONTDIR</dir>','<dir>C:/Users/chrba/AppData/Local/Microsoft/Windows/Fonts</dir>')
    text=text.replace('<include ignore_missing="yes">conf.d</include>', '<include ignore_missing="yes">C:/Program Files/KiCad/10.0/etc/fonts/conf.d</include>')
    text=re.sub(r'<cachedir[^>]*>.*?</cachedir>',lambda m:'<cachedir>'+cache.as_posix()+'</cachedir>',text)
    config=folder/'fonts.conf';config.write_text(text,encoding='utf-8',newline='\n')
    env={**os.environ,'FONTCONFIG_FILE':str(config),'FONTCONFIG_PATH':str(source.parent),'XDG_CACHE_HOME':str(cache)}
    write(OUT/'fontconfig-environment.json',{'source':str(source),'source_sha256':sha(source),'workspace_config_sha256':sha(config),
      'purpose':'Resolve normal Windows font directories explicitly and place caches in the permitted workspace. No CAD/rule/font substitution; all native stderr remains recorded.',
      'overrides':{k:env[k] for k in ['FONTCONFIG_FILE','FONTCONFIG_PATH','XDG_CACHE_HOME']}})
    return env

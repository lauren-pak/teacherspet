# Detects User's currently working tab on chrome
import subprocess
from urllib.parse import urlparse

def get_chrome_active_domain():
    script = '''
    tell application "Google Chrome"
        if (count of windows) = 0 then return ""
        set t to active tab of front window
        return URL of t
    end tell
    '''

    p = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    
    #detect error
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or "osascript failed")
    
    # strip url 
    url = p.stdout.strip()
    if not url:
        return None
    host = urlparse(url).netloc
    return host


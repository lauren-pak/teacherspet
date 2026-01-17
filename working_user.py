# Detects User's currently working tab on chrome
import subprocess, platform
from urllib.parse import urlparse


def get_chrome_active_domain():
    illegal_apps = ["snap", "instagram", "chatgpt", "tiktok", "youtube", "netflix", "discord", "twitter", "facebook"]
    illegal = False
    if platform.system() == "Darwin":
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
        # url = p.stdout.strip()
        # if not url:
        #     return None
        # host = urlparse(url).netloc
        # return host
    
        p = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if p==0: return "I am doing nothing, not even on task."
        for i in illegal_apps:
            if i in p.stdout.strip().lower():
                illegal = True

        return p.stdout.strip(), illegal
    
    elif platform.system() == "Windows":
        import win32gui
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        for i in illegal_apps:
            if i in title.lower():
                illegal = True
        return title, illegal

print(get_chrome_active_domain())




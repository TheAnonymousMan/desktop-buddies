"""Check whether the buddies can see your fullscreen app.

    python tools/fullscreen_check.py

Then, within a few seconds, switch to the app and make it fullscreen. For 20
seconds this prints, once a second, what the buddies see in front: whether
it covers the screen, whether it counts as fullscreen, and what kind of thing
they think it is (video, game, present, other), plus whether a screen-share
bar is open. It shows the program and kind of window, never its title, so
nothing private is printed. Use the program / window kind it prints to add
your own apps to fullscreen_context.txt.
"""
import ctypes
import sys
import time
from ctypes import wintypes
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import buddyengine as engine  # noqa: E402

engine.enable_dpi_awareness()
u = ctypes.WinDLL("user32")
u.GetForegroundWindow.restype = wintypes.HWND
u.GetWindowLongW.restype = ctypes.c_long
u.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
u.MonitorFromWindow.restype = wintypes.HMONITOR

print("Switch to your app and make it fullscreen now...\n")
for _ in range(20):
    time.sleep(1)
    hwnd = u.GetForegroundWindow()
    cls = ctypes.create_unicode_buffer(64)
    u.GetClassNameW(hwnd, cls, 64)
    r = wintypes.RECT()
    u.GetWindowRect(hwnd, ctypes.byref(r))
    info = engine.MONITORINFO()
    info.cbSize = ctypes.sizeof(engine.MONITORINFO)
    u.GetMonitorInfoW(u.MonitorFromWindow(hwnd, 2), ctypes.byref(info))
    m = info.rcMonitor
    covers = r.left <= m.left and r.top <= m.top and r.right >= m.right and r.bottom >= m.bottom
    caption = (u.GetWindowLongW(hwnd, -16) & 0x00C00000) == 0x00C00000
    verdict = engine.fullscreen_monitor(hwnd)
    exe, _, _ = engine._window_facts(hwnd)
    kind = engine.fullscreen_kind(hwnd)
    sharing = engine.screen_sharing()
    print(f"{cls.value[:28]:28s} window ({r.left},{r.top})-({r.right},{r.bottom})  "
          f"screen ({m.left},{m.top})-({m.right},{m.bottom})  covers={covers} "
          f"maximized={bool(u.IsZoomed(hwnd))} title_bar={caption}  ->  "
          f"{'FULLSCREEN' if verdict else 'not fullscreen'}  program={exe or '?'} "
          f"kind={kind} sharing={sharing}")

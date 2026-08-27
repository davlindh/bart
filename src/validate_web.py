import os

files = {
    'src/web/canvas.js': ['class SpatialCanvas', 'pivotTo', 'opportunityNodeIds', '_renderMinimap', 'onPivot', 'handleWheel', 'worldToScreen'],
    'src/web/app.js': ['animateCounter', 'pushBreadcrumb', 'renderBreadcrumbs', 'pivotContext', 'renderWindowSidebar', 'switchWindow', 'Toast.success', 'navigationStack'],
    'src/web/toast.js': ['class ToastManager', 'window.Toast', '_dismiss', 'success', 'warning'],
    'src/web/index.html': ['hud-root', 'windowSidebar', 'breadcrumbNav', 'toast.js', 'canvas.js', 'app.js'],
    'src/web/index.css': ['hud-root', 'window-sidebar', 'window-item', 'breadcrumb-strip', 'crumb-active', 'fadeIn']
}

all_ok = True
for filepath, checks in files.items():
    try:
        content = open(filepath, encoding='utf-8').read()
        size = len(content)
        for check in checks:
            found = check in content
            status = 'OK' if found else 'FAIL'
            if not found:
                all_ok = False
            print(f'  [{status}] {filepath} -> "{check}"')
        print(f'     -> {filepath}: {size:,} bytes, {content.count(chr(10))} lines')
    except Exception as e:
        print(f'[FAIL] Cannot read {filepath}: {e}')
        all_ok = False

print()
print('ALL CHECKS PASSED' if all_ok else 'SOME CHECKS FAILED')

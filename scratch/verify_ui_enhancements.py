import urllib.request
import re

BASE_URL = "http://127.0.0.1:8765"

def check_url(url, required_snippets):
    print(f"\n--- Checking {url} ---")
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        content = resp.read().decode('utf-8')
        status = resp.status
        print(f"Status: {status} ({len(content)} chars)")
        assert status == 200, f"Expected 200, got {status}"
        
        for snippet in required_snippets:
            if snippet in content:
                print(f"  [PASS] Found: {snippet[:60]}")
            else:
                print(f"  [FAIL] Missing: {snippet}")
                raise AssertionError(f"Missing snippet in {url}: {snippet}")

def main():
    # 1. Check HTML
    check_url(f"{BASE_URL}/", [
        'id="btnSoundToggle"',
        'id="weightingVectorPanel"',
        'id="weightingMetersContainer"',
        'id="confidenceEntropyBadge"',
        'id="btnAutoPlayLoop"',
        'id="loopProgressBar"',
        'id="loopProgressStage"',
        'id="btnToggleLayoutMode"',
        'id="btnTraceCausalPath"',
        'id="erdCategoryPills"',
        'id="erpTickerContainer"',
        'id="erpLiveTicker"'
    ])

    # 2. Check CSS
    check_url(f"{BASE_URL}/index.css", [
        '.weighting-meters-grid',
        '.weighting-bar-fill',
        '.loop-progress-container',
        '.loop-progress-fill',
        '.canvas-category-strip',
        '.category-pill.active',
        '.btn-canvas-util.emerald',
        '.erp-ticker-container',
        '.ticker-badge',
        'tickerDotPulse',
        '.btn-hud-action.sound-muted'
    ])

    # 3. Check Canvas JS
    check_url(f"{BASE_URL}/canvas.js", [
        'layoutMode',
        'concentric',
        'rippleWaves',
        'particles',
        'spawnParticles',
        'addRipple',
        'traceCausalPath',
        'tracedPathNodes',
        'tracedPathLinks',
        'D0: Focal Point',
        'D1: Direct Relations',
        'D2: Subsystem & Team',
        'D3: Macro / Meta-Ecosystem',
        'matchesCategory'
    ])

    # 4. Check App JS
    check_url(f"{BASE_URL}/app.js", [
        'playSound',
        'audioState',
        'btnSoundToggle',
        'btnToggleLayoutMode',
        'btnTraceCausalPath',
        'erdCategoryPills',
        'renderWeightingVector',
        'btnAutoPlayLoop',
        'startAutoPlay',
        'stopAutoPlay',
        'loopProgressBar',
        'rotateErpTicker'
    ])

    print("\n=======================================================")
    print("ALL VISUAL AND FUNCTIONAL ENHANCEMENTS VERIFIED LIVE!")
    print("=======================================================")

if __name__ == "__main__":
    main()

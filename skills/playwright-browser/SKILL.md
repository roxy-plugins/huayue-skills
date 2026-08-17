---
name: playwright-browser
description: 通用浏览器自动化。在需要登录/Js渲染/交互/截图时使用Playwright，纯内容优先走web_fetch。触发词：看看这个页面, 打开这个网页, 帮我查一下, 登进去看看, 截图, 自动化操作, 浏览器, 网页
allowed-tools: Bash(python3), Bash(pip), Bash(curl)
---

# 浏览器自动化 Skill

## 决策树（触发后先走这个）

```
用户要访问网页/查内容
  │
  ├─ 纯内容，不需要登录，页面是 HTML/有 API
  │   └→ 用 web_fetch（不启动浏览器，更快）
  │
  ├─ 需要登录态 / JS 渲染 / 截图 / 交互操作
  │   └→ 用 Playwright
  │       ├─ CDP 常住浏览器活着？
  │       │   ├─ 是 → connect_over_cdp("http://localhost:9222")
  │       │   │   ├─ 目标站点有 cookie？
  │       │   │   │   ├─ 有 → 直接操作，session 已就绪
  │       │   │   │   └─ 无 → 提示用户跑 login_helper.sh
  │       │   └─ 否 → 兜底：self-launch 新浏览器
  │       └─ 需要反检测防封？
  │           └→ cloakbrowser.launch()（临时伪装浏览器）
  │
  └─ 不确定？→ 先 web_fetch 试，失败再降级到 Playwright
```

## CDP 常住浏览器（优先）

常住浏览器运行在 localhost:9222，CloakBrowser 改装 Chromium，带持久 profile：

```
systemctl --user status cloakbrowser.service    # 查看状态
systemctl --user start/stop cloakbrowser.service # 启停
"${CLOAKBROWSER_HOME:?CLOAKBROWSER_HOME is required}/login_helper.sh" [URL] # 弹有头窗口登录
```

登录态写进 `$CLOAKBROWSER_HOME/profile/`，重启不丢；该变量必须指向服务实际使用的数据目录。
重启后 `loginctl enable-linger` 保证开机自启。

## 核心模板（Python）

所有脚本写到 `/tmp/playwright_*.py`。

### 登录态查询（CDP，最常用）

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = ctx.new_page()
    page.goto("https://example.com", wait_until="networkidle", timeout=30000)
    # 操作...
    page.close()
```

### 截图（CDP）

```python
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = ctx.new_page()
    page.goto("https://example.com", wait_until="networkidle", timeout=30000)
    output = Path(os.environ["ROXY_WORKSPACE"]) / "pictures" / "screenshot.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(output), full_page=True)
    page.close()
```

### Session 自检（操作前调用）

```python
cookies = page.context.cookies()
domain_cookies = [c for c in cookies if "targetdomain" in c.get("domain", "")]
if not domain_cookies:
    print("NEEDS_LOGIN: 未登录，请用 $CLOAKBROWSER_HOME/login_helper.sh [URL] 登录")
else:
    print("SESSION_OK")
```

### 兜底：自启动浏览器（CDP 连不上时）

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=100)
    page = browser.new_page()
    page.goto("https://example.com", wait_until="networkidle")
    page.close()
    browser.close()
```

### 反检测：CloakBrowser 伪装

```python
from cloakbrowser import launch

browser = launch(headless=True)
page = browser.new_page()
page.goto("https://example.com")
browser.close()
```

## 执行方式

playwright 装在 agent venv 里，必须用这个解释器：

```bash
/mnt/data/coding/akasic-agent/.venv/bin/python /tmp/playwright_xxx.py
```

系统 `python3` 没有 playwright，不要用。

截图路径统一用 `$ROXY_WORKSPACE/pictures/`，之后用 message_push(image=...) 发。

## 注意事项

- `web_fetch` 能搞定的事不要用浏览器（省 token，更快）
- CDP 浏览器是共享 session 的，不要在同一个 page 上反复 goto 不同站，用完 new_page
- 常住浏览器 headless 但全功能，截图输出正常
- 登录流程不要自己填密码——用 login_helper.sh 弹有头窗口手输

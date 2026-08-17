---
name: opencli
description: OpenCLI 适配器操作。用 opencli 命令操作 B站、GitHub、DeepSeek 平台、HackerNews、V2EX 等站点，获取结构化数据。触发词：opencli, 用 opencli, 查 B站, B站热榜, bilibili, 查 GitHub, GitHub 通知, DeepSeek 用量, hackernews, v2ex, opencli browser
metadata: {"roxy": {"always": false, "requires": {"bins": ["opencli"], "env": []}}}
---

# OpenCLI 使用指南

基于官方 opencli-usage + opencli-browser 改造，详见 references/。

## 核心约束（优先级最高）

1. **所有 `opencli browser` 操作必须加 `--window background`**，花月哥哥不允许弹窗口
2. **优先用 adapter 命令**（`opencli <site> <command>`），零 Token 消耗；跑不通才退到 browser
3. **结构化输出** `-f json`，不要硬编码 adapter 列表——用 `opencli list -f json` 查
4. 策略标签：`PUBLIC` 无浏览器要求；`COOKIE/INTERCEPT/UI` 需要 Browser Bridge 插件

## 常用站点速查

### 公开数据（不需要浏览器）

```bash
opencli hackernews top -f json --limit 10
opencli v2ex hot -f json --limit 10
opencli arxiv recent --category cs.AI -f json --limit 10
opencli reddit hot -r programming -f json --limit 3
opencli 36kr hot -f json --limit 10
opencli wttr weather -l "Beijing" -f json
opencli producthunt today -f json --limit 10
```

### 登录态（走 Browser Bridge 自动复用你的会话）

```bash
# B站
opencli bilibili hot -f json --limit 10
opencli bilibili search "<关键词>" -f json --limit 10
opencli bilibili video "<BVID>" -f json

# GitHub
opencli github whoami -f json
opencli github notifications -f json
opencli github detail "<owner>/<repo>" -f json

# DeepSeek 用量（两步：打开页面 → 提取）
opencli browser roxy open "https://platform.deepseek.com/usage" --window background
opencli browser roxy extract --window background

# YouTube
opencli youtube video "<id>" -f json
opencli youtube search "<关键词>" -f json --limit 10
```

### Browser 操作（adapter 不够用时）

```
opencli browser <session> <command> --window background
```
核心命令：`bind` `unbind` `open` `state` `extract` `click` `type` `select` `find` `eval` `screenshot` `network`

每次 action 前先 `state` 或 `find` 获取目标，用数字 ref 而非 CSS 选择器。
Session 用 stable 名称，用完必须 `close`（释放标签页）—— `unbind` 只适合绑定用户标签页的场景，关不掉 OpenCLI 自己开的页。
详见 references/opencli-browser.SKILL.md。

## 登录态维护

- `opencli auth status` 查看各站登录态
- 登录态通过 Browser Bridge 自动复用，哪个站掉了你登一次就行
- 不用 `login` 命令——你有插件不需要

## 注意事项

- 所有 `browser` 命令都必须加 `--window background`——你明确要求的
- adapter 报错时先试 `opencli <site> --help` 或加 `-v`；官方有 autofix 机制（详见 references）
- 大型页面 extract 后读 content 字段，内容超长时分页
- 不要做让花月哥哥不开心的事

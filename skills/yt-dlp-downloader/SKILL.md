---
name: yt-dlp-downloader
description: 使用 yt-dlp 从 YouTube、Bilibili、Twitter/X、抖音、TikTok 等数千个网站下载视频或提取音频。当用户提供视频 URL 并请求下载视频、提取 MP3 音频、下载字幕、选择画质时触发。触发词：下载视频、下载音频、提取音频、download video、extract audio、yt-dlp、YouTube、B站、bilibili、抖音、TikTok。
metadata: {"akasic": {"always": false, "requires": {"bins": ["yt-dlp", "ffmpeg"]}}}
---

# yt-dlp 视频下载

> **必须用 shell 工具执行实际命令，不得凭印象声称下载成功。**
> 若 yt-dlp 未安装（available="false"），先执行安装步骤再下载。

## 安装依赖

```bash
# yt-dlp（uv tool 隔离安装，不污染系统环境）
uv tool install yt-dlp

# ffmpeg（系统包，音频提取必须）
sudo pacman -S ffmpeg       # Arch
# sudo apt install ffmpeg   # Debian/Ubuntu
```

## 下载目录

默认保存到 `$ROXY_WORKSPACE/downloads/`，可通过 `--path` 按用户要求修改。

## 推荐方式：使用辅助脚本

**未显式指定目录时，所有下载必须保存到 `$ROXY_WORKSPACE/downloads/`。**
技能目录下有封装好的脚本，优先使用（默认路径已配置正确）：

```bash
SKILL_DIR="<本技能的实际目录>"

# 基本下载
bash "$SKILL_DIR/scripts/download.sh" "URL"

# 指定保存目录
bash "$SKILL_DIR/scripts/download.sh" -p "/path/to/dir" "URL"

# 仅提取音频（MP3）
bash "$SKILL_DIR/scripts/download.sh" -a "URL"

# 下载字幕
bash "$SKILL_DIR/scripts/download.sh" -s "URL"

# 指定画质（如 720）
bash "$SKILL_DIR/scripts/download.sh" -q 720 "URL"

# 列出可用格式
bash "$SKILL_DIR/scripts/download.sh" -l "URL"
```

## 手动命令（不用脚本时，必须加 -P 指定目录）

```bash
# 普通下载
yt-dlp -P "${ROXY_WORKSPACE:?ROXY_WORKSPACE is required}/downloads" "URL"

# YouTube / B站（必须带 chromium cookies）
yt-dlp -P "${ROXY_WORKSPACE:?ROXY_WORKSPACE is required}/downloads" --cookies-from-browser chromium+gnomekeyring "URL"

# 仅音频
yt-dlp -P "${ROXY_WORKSPACE:?ROXY_WORKSPACE is required}/downloads" -x --audio-format mp3 "URL"

# 指定画质
yt-dlp -P "${ROXY_WORKSPACE:?ROXY_WORKSPACE is required}/downloads" -f "bestvideo[height<=1080]+bestaudio/best[height<=1080]" "URL"
```

## 工作流程

1. 判断平台：YouTube/YouTube Music/B站/b23.tv → 加 `--cookies-from-browser chromium+gnomekeyring`
2. 若用户未指定需求，询问：视频 / 仅音频 / 字幕 / 画质
3. 用 shell 工具执行脚本或命令
4. 处理错误（见下表），告知文件保存位置

## B站固定做法

B站链接包括 `bilibili.com`、`b23.tv`、`bili2233.cn`。遇到这些链接时，不要裸跑 `yt-dlp`，直接走脚本：

```bash
SKILL_DIR="<本技能的实际目录>"
bash "$SKILL_DIR/scripts/download.sh" "URL"
```

脚本会自动加 `--cookies-from-browser chromium+gnomekeyring` 和 B站常用格式选择。若需要诊断格式，只运行：

```bash
bash "$SKILL_DIR/scripts/download.sh" -l "URL"
```

如果输出里有 `failed to decrypt cookie`，不要手写 Chromium cookies 解密脚本；这只是 yt-dlp 读取浏览器 cookies 时的警告。只要继续出现 `HTTP Error 412: Precondition Failed`，就说明 B站 `playurl` 接口拒绝了当前请求，最多重试一次同一个脚本命令。重试仍失败时，直接报告“B站接口 412，当前 chromium cookies 或请求环境不足”，不要安装额外 Python 库、不要导出 `/tmp/cookies.txt`、不要写解密脚本。

## 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| HTTP 403 | YouTube 拦截未认证请求 | 加 `--cookies-from-browser chromium+gnomekeyring` |
| HTTP 412 | B站 `playurl` 接口拒绝当前请求 | 用脚本带 chromium cookies 重试一次；仍失败就报告，不要手工解密 cookies |
| failed to decrypt cookie | yt-dlp 未能解开部分 Chromium cookies | 这是警告，不是继续手写解密脚本的理由 |
| 视频不可用 | 地区限制或私有 | 加 cookies 或提示使用代理 |
| 下载中断 | 网络波动 | yt-dlp 自动续传，直接重试 |
| 格式不存在 | 请求格式不可用 | 先 `-l` 列格式再选 |
| ffmpeg 未找到 | 未安装 | `sudo pacman -S ffmpeg` |
| yt-dlp 未找到 | 未安装 | `uv tool install yt-dlp` |

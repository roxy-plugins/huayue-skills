---
name: image-generation-nano
description: 使用 Google Gemini Nano Banana (gemini-2.5-flash-image) 生成高质量图片。支持文生图、图片编辑、多轮迭代。自动优化提示词并选择最佳宽高比。
allowed-tools: Bash(curl), Bash(base64), Bash(mkdir), Bash(echo)
---

# Nano Banana 图片生成 Skill (纯 API 版)

本技能通过直接调用 Google Gemini REST API 生成图片，无需任何额外 CLI 工具或扩展。

## 🎯 何时触发

当用户请求生成、绘制、创建、设计任何视觉内容时，立即触发：
- “画一张...” / “生成一个...” / “做个...”
- “帮我设计一个 Logo” / “做个头像” / “生成封面图”
- “把这张图改成...” (需提供图片路径)
- “来个赛博朋克风格的猫”

## 🔑 前置条件

1. **API Key**: 必须存在环境变量 `GEMINI_API_KEY` 或文件 `$ROXY_WORKSPACE/memory/GEMINI_API_KEY`。
2. **输出目录**: 默认输出到 `$ROXY_WORKSPACE/pictures/`（自动创建）。

## 🛠️ 核心执行逻辑

### 模式判断
- **文生图 (Text-to-Image)**: 用户仅提供文字描述。
- **图生图/编辑 (Image-to-Image)**: 用户提供文字描述 + 原图路径。

### 1. 读取 API Key
```bash
if [ -n "$GEMINI_API_KEY" ]; then
  API_KEY="$GEMINI_API_KEY"
elif [ -f "${ROXY_WORKSPACE:?ROXY_WORKSPACE is required}/memory/GEMINI_API_KEY" ]; then
  API_KEY=$(cat "$ROXY_WORKSPACE/memory/GEMINI_API_KEY")
else
  echo "❌ 错误：未找到 GEMINI_API_KEY。请设置环境变量或写入记忆文件。"
  exit 1
fi
```

### 2. 构建提示词与 Payload

#### 场景 A: 文生图 (无原图)
采用官方推荐公式：**[风格] + [主体] + [构图] + [氛围]**
```bash
# 构建纯文本 Payload
PAYLOAD="{
  \"contents\": [{
    \"parts\": [{\"text\": \"$OPTIMIZED_PROMPT\"}]
  }],
  \"generationConfig\": {
    \"responseModalities\": [\"IMAGE\"],
    \"imageConfig\": {\"aspectRatio\": \"$ASPECT_RATIO\"}
  }
}"
```

#### 场景 B: 图片编辑 (有原图)
**关键逻辑**: 将原图转为 Base64，放入 `inline_data` 部分，与文本提示词并列。
```bash
# 读取原图并转 Base64
INPUT_IMAGE="$USER_PROVIDED_IMAGE_PATH"
BASE64_INPUT=$(base64 -w 0 "$INPUT_IMAGE")
MIME_TYPE="image/png" # 可根据文件后缀动态判断

# 构建多模态 Payload (文本 + 图片)
PAYLOAD="{
  \"contents\": [{
    \"parts\": [
      {\"text\": \"$EDIT_INSTRUCTION\"},
      {\"inline_data\": {\"mime_type\": \"$MIME_TYPE\", \"data\": \"$BASE64_INPUT\"}}
    ]
  }],
  \"generationConfig\": {
    \"responseModalities\": [\"IMAGE\"]
  }
}"
# 注意：编辑模式下通常不强制指定 aspectRatio，保持与原图一致
```

### 3. 调用 API (curl)
```bash
MODEL="gemini-2.5-flash-image"
ENDPOINT="https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent"

# 发送请求
RESPONSE=$(curl -s -X POST "$ENDPOINT" \
  -H "x-goog-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

# 解析 JSON 提取 Base64 图片数据
BASE64_IMAGE=$(echo "$RESPONSE" | grep -oP '"inlineData":\{"mimeType":"image/png","data":"\K[^"]+' | head -n 1)

if [ -z "$BASE64_IMAGE" ]; then
  echo "❌ 生成失败：$RESPONSE"
  exit 1
fi
```

### 4. 保存图片
```bash
OUTPUT_DIR="${ROXY_WORKSPACE:?ROXY_WORKSPACE is required}/pictures"
mkdir -p "$OUTPUT_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
# 如果是编辑模式，文件名加上 _edited 后缀
if [ -n "$INPUT_IMAGE" ]; then
  OUTPUT_FILE="$OUTPUT_DIR/nano_edited_${TIMESTAMP}.png"
else
  OUTPUT_FILE="$OUTPUT_DIR/nano_${TIMESTAMP}.png"
fi

echo "$BASE64_IMAGE" | base64 -d > "$OUTPUT_FILE"
echo "✅ 图片已生成：$OUTPUT_FILE"
```

## 📋 完整命令示例

### 基础文生图
```bash
# 用户：画一个赛博朋克风格的猫头像
bash -c '
  if [ -n "${GEMINI_API_KEY:-}" ]; then
    API_KEY="$GEMINI_API_KEY";
  else
    API_KEY=$(cat "${ROXY_WORKSPACE:?ROXY_WORKSPACE is required}/memory/GEMINI_API_KEY");
  fi;
  PROMPT="一张照片级真实感的特写肖像，一只可爱的猫咪，赛博朋克风格，霓虹灯背景，蓝色和紫色调，未来科技感，1:1 正方形构图";
  RATIO="1:1";
  ENDPOINT="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent";
  PAYLOAD="{\"contents\":[{\"parts\":[{\"text\":\"$PROMPT\"}]}],\"generationConfig\":{\"responseModalities\":[\"IMAGE\"],\"imageConfig\":{\"aspectRatio\":\"$RATIO\"}}}";
  RESPONSE=$(curl -s -X POST "$ENDPOINT" -H "x-goog-api-key: $API_KEY" -H "Content-Type: application/json" -d "$PAYLOAD");
  BASE64_IMG=$(echo "$RESPONSE" | grep -oP "\"inlineData\":\{\"mimeType\":\"image/png\",\"data\":\"\\K[^\"]+" | head -n 1);
  if [ -n "$BASE64_IMG" ]; then
    mkdir -p "$ROXY_WORKSPACE/pictures";
    echo "$BASE64_IMG" | base64 -d > "$ROXY_WORKSPACE/pictures/nano_$(date +%Y%m%d_%H%M%S).png";
    echo "✅ 生成成功";
  else
    echo "❌ 失败：$RESPONSE";
  fi
'
```

### 带参考图的编辑 (Image-to-Image)
```bash
# 用户：把这张图里的猫加上巫师帽 (需提供图片路径)
INPUT_IMAGE="/path/to/cat.png"
BASE64_INPUT=$(base64 -w 0 "$INPUT_IMAGE")
PROMPT="给这只猫加上一顶针织的巫师帽子，保持原有光照和风格"

PAYLOAD="{
  \"contents\": [{
    \"parts\": [
      {\"text\": \"$PROMPT\"},
      {\"inline_data\": {\"mime_type\": \"image/png\", \"data\": \"$BASE64_INPUT\"}}
    ]
  }],
  \"generationConfig\": {
    \"responseModalities\": [\"IMAGE\"]
  }
}"
# (后续 curl 调用同上)
```

## 🎨 提示词策略库 (内置模板)

| 场景 | 模板 |
| :--- | :--- |
| **写实人像** | "A photorealistic [shot type] of [subject], [action/expression], set in [environment]. Illuminated by [lighting], creating a [mood] atmosphere. Captured with [lens details], emphasizing [textures]." |
| **贴纸/图标** | "A [style] sticker of a [subject], featuring [characteristics] and a [color palette]. Bold outlines, cel-shading. Background must be white/transparent." |
| **产品摄影** | "A high-resolution, studio-lit product photograph of [product] on [surface]. Three-point softbox lighting, [angle] shot. Ultra-realistic, sharp focus on [detail]." |
| **极简设计** | "A minimalist composition featuring a single [subject] in the [position] of the frame. Vast empty [color] background, significant negative space. Soft diffused lighting." |
| **3D 等距** | "A clear 45° top-down isometric miniature 3D cartoon of [scene]. Soft textures, PBR materials, realistic lighting. Clean minimalist composition, solid color background." |

## ⚙️ 参数配置

| 参数 | 可选值 | 默认 | 说明 |
| :--- | :--- | :--- | :--- |
| `aspectRatio` | `1:1`, `16:9`, `9:16`, `4:3`, `3:2`, `2:3` | `1:1` | 宽高比 |
| `outputDir` | 任意有效路径 | `/mnt/data/some-pictures/` | 输出目录 |
| `model` | `gemini-2.5-flash-image` | `gemini-2.5-flash-image` | 固定为 Nano Banana |

## ❌ 错误处理

| 错误信息 | 原因 | 解决方案 |
| :--- | :--- | :--- |
| `"API_KEY not found"` | 未配置 Key | 检查环境变量或记忆文件 |
| `"Quota exceeded"` | 超出速率限制 | 等待 1 分钟重试 (免费层约 15 次/分钟) |
| `"Invalid aspect ratio"` | 参数错误 | 确保使用大写 K 和正确格式 (如 `16:9`) |
| `"Safety filter triggered"` | 内容违规 | 修改提示词，避免敏感/暴力/成人内容 |

## 🚀 最佳实践

1. **描述具体化**: 不要说“好看”，要说“金色小时光线，浅景深，暖色调”。
2. **指定用途**: 告诉模型“用于 YouTube 封面”会自动优化为 16:9 和高对比度。
3. **迭代优化**: 第一张不满意？回复“再来一张，更... ”会自动继承上下文并重试。
4. **负向提示**: 用“没有文字”、“没有水印”代替“不要文字”。

## 📝 使用示例

**用户**: “帮我生成一个博客封面图，主题是 Rust 语言入门，要现代科技感。”

**Skill 执行**:
1. **识别意图**: 博客封面 → 宽高比 `16:9`。
2. **优化提示词**: “一张现代科技感的宽幅插图，展示 Rust 语言的齿轮 Logo 和代码片段，深蓝色和橙色渐变背景，极简主义设计，适合做博客封面，16:9 构图。”
3. **调用 API**: 发送 `curl` 请求。
4. **保存输出**: `/mnt/data/some-pictures/nano_20260223_103045.png`。
5. **回复用户**: “✅ 已生成博客封面图！保存在 `/mnt/data/some-pictures/nano_20260223_103045.png`。”

---

**注意**: 所有生成的图片均包含 SynthID 隐形水印。

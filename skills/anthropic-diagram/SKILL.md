---
name: anthropic-diagram
description: 生成 Anthropic 技术博客风格的编辑型图表。当用户请求画流程图、架构图、对比图、泳道图、可视化流程，或提到"画个图""可视化这个""画架构图""画流程图"时自动触发。优先生成 PNG 图片直接发送给用户，同时保留 .drawio 源文件。支持中文和英文标签自动匹配。
available: true
---

# Anthropic-Style Diagram Skill

生成符合 Anthropic 技术博客视觉语言的 draw.io 图表——温暖、极简、编辑级质量。

## 工作流

```
用户描述 → DiagramSpec（文本规划）→ 带样式 draw.io XML → .drawio 文件 → PNG 导出 → 发送 PNG 给用户
```

**优先级：PNG 图片是最终交付物，.drawio 是中间产物。**

---

## Step 1: 分析请求

确定：
- **核心论点 (main_claim)**：这张图要让什么观点一目了然？
- **视觉模式 (pattern)**：哪种模式最能服务这个论点？（见 Step 2 和 `references/pattern-library.md`）
- **阅读方向**：工作流/对比用 left-to-right；层级/堆栈用 top-to-bottom

不确定时的默认规则：
- 顺序步骤 → Linear Workflow
- 系统组件/包含关系 → Grouped Architecture
- 前后对比/两种方案 → Split Comparison
- 多参与者时序 → Swimlane
- 重叠/共享归属 → Venn
- 数值对比 → Editorial Chart

---

## Step 2: 编写 DiagramSpec

在写 XML 之前，先用文本明确写出图表规划——这能在提交 XML 前捕捉结构错误，并让用户看到你的推理过程。

按以下格式输出 DiagramSpec：

```
**DiagramSpec**

main_claim: [一句话——这张图要让什么显而易见？]
pattern: [主模式]
secondary_pattern: [可选，或无]
reading_direction: [left-to-right / top-to-bottom]
title: "图表标题"

nodes:
  - id: n1
    label: "简短标签"
    semantic_type: [primary | secondary | tertiary | start | end | warning | decision | ai_llm | inactive | error]
    shape: [rect | pill | diamond | cylinder]
    group: [container_id if inside a container, else none]

connections:
  - from: n1
    to: n2
    label: ""          # 保持简短或空
    style: [primary | optional | feedback | human | context | error]

groups:
  - id: g1
    label: "面板标题"
    type: [outer_panel | inner_panel | swimlane | soft_region]
    children: [n1, n2, ...]
```

**语言一致性**：DiagramSpec 中的所有节点标签、标题、连线标签，以及最终 XML 中的文本，都必须使用用户使用的语言。用户用中文，图就全中文；用户用英文，图就全英文。

写完 DiagramSpec 后**立即进入 Step 3**，无需等待用户确认。布局规则参考 `references/pattern-library.md`。

---

## Step 3: 生成 draw.io XML

### 画布设置

```xml
<mxGraphModel background="#F2EFE8" grid="0" tooltips="0" connect="0" arrows="0" fold="0" page="0" pageScale="1" pageWidth="1654" pageHeight="1169" math="0" shadow="0">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <!-- 所有单元格放在这里，parent="1"（嵌套则为 parent="container_id"） -->
  </root>
</mxGraphModel>
```

大多数图表用 `background="#F2EFE8"`（温暖画布）。极少元素的极简图表可用 `background="#FFFFFF"`。

### 标题

```xml
<mxCell id="title" value="你的图表标题" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;overflow=hidden;fontStyle=1;fontSize=32;fontColor=#1F1F1C;" vertex="1" parent="1">
  <mxGeometry x="80" y="40" width="1200" height="50" as="geometry"/>
</mxCell>
```

### 节点语义类型样式表

根据语义角色应用样式，而非审美装饰。颜色编码含义。

| 语义类型 | draw.io 样式 |
|---|---|
| **Primary / Neutral** | `rounded=1;whiteSpace=wrap;arcSize=10;fillColor=#E6E2DA;strokeColor=#8C867F;strokeWidth=1.8;fontColor=#2D2B28;fontSize=20;` |
| **Secondary / Context** | `rounded=1;whiteSpace=wrap;arcSize=10;fillColor=#EAF4FB;strokeColor=#6FA8D6;strokeWidth=1.8;fontColor=#2D2B28;fontSize=20;` |
| **Tertiary / Control** | `rounded=1;whiteSpace=wrap;arcSize=10;fillColor=#EEEAF9;strokeColor=#9A90D6;strokeWidth=1.8;fontColor=#2D2B28;fontSize=20;` |
| **Start / Trigger** | `rounded=1;whiteSpace=wrap;arcSize=50;fillColor=#F8E9E1;strokeColor=#D88966;strokeWidth=1.8;fontColor=#D88966;fontSize=20;fontStyle=1;` |
| **End / Success** | `rounded=1;whiteSpace=wrap;arcSize=10;fillColor=#CFE8D7;strokeColor=#71AE88;strokeWidth=1.8;fontColor=#2D2B28;fontSize=20;` |
| **Warning / Reset** | `rounded=1;whiteSpace=wrap;arcSize=10;fillColor=#F3E4DA;strokeColor=#C88E6A;strokeWidth=1.8;fontColor=#2D2B28;fontSize=20;` |
| **Decision** | `rhombus;whiteSpace=wrap;fillColor=#E6D7B4;strokeColor=#BFA777;strokeWidth=1.8;fontColor=#2D2B28;fontSize=20;` |
| **AI / LLM** | `rounded=1;whiteSpace=wrap;arcSize=10;fillColor=#D7E6DC;strokeColor=#7FB08F;strokeWidth=1.8;fontColor=#2D2B28;fontSize=20;` |
| **Inactive / Disabled** | `rounded=1;whiteSpace=wrap;arcSize=10;fillColor=#EFECE6;strokeColor=#B4AEA6;strokeWidth=1.8;fontColor=#7A756E;fontSize=20;` |
| **Error** | `rounded=1;whiteSpace=wrap;arcSize=10;fillColor=#F8DFDA;strokeColor=#D96B63;strokeWidth=1.8;fontColor=#2D2B28;fontSize=20;` |
| **Pill label** | `rounded=1;whiteSpace=wrap;arcSize=50;fillColor=#FAF8F4;strokeColor=#8C867F;strokeWidth=1.8;fontColor=#2D2B28;fontSize=20;` |
| **Code/evidence block** | `rounded=1;whiteSpace=wrap;arcSize=6;fillColor=#EEF3F7;strokeColor=#B7C9D8;strokeWidth=1.5;fontColor=#44515C;fontSize=20;align=left;` |

语义含义详见 `references/color-palette.md` → Semantic Mapping Rules。

### 容器/面板样式

所有容器样式含 `html=1;`，使 `value` 可含 HTML。用 `<font>` 标签控制标签字号（通常比样式字符串中的 fontSize 大 2–4px，形成视觉层级）。

**Outer panel**（大系统边界）：
```
rounded=1;whiteSpace=wrap;arcSize=4;fillColor=#FAF8F4;strokeColor=#8C867F;strokeWidth=2;fontSize=18;fontStyle=1;fontColor=#5F5A54;swimlane;startSize=63;horizontal=1;html=1;
```
value: `<font style="font-size: 22px;">面板标题</font>`

**Inner panel**（子系统或分组）：
```
rounded=1;whiteSpace=wrap;arcSize=6;fillColor=#FAF8F4;strokeColor=#8C867F;strokeWidth=1.8;fontSize=16;fontStyle=1;fontColor=#5F5A54;swimlane;startSize=50;horizontal=1;html=1;
```
value: `<font style="font-size: 20px;">面板标题</font>`

**Soft region**（虚线分组，无强边界）：
```
rounded=1;fillColor=#F6F4EE;strokeColor=#B9B3AB;strokeWidth=1.5;dashed=1;dashPattern=6 6;fontSize=16;fontColor=#7A756E;html=1;
```
value: `<font style="font-size: 18px;">区域标签</font>`

Outer panel 示例：
```xml
<mxCell id="panel_server" parent="1" style="rounded=1;whiteSpace=wrap;arcSize=4;fillColor=#FAF8F4;strokeColor=#8C867F;strokeWidth=2;fontSize=18;fontStyle=1;fontColor=#5F5A54;swimlane;startSize=63;horizontal=1;html=1;" value="&lt;font style=&quot;font-size: 22px;&quot;&gt;面板标题&lt;/font&gt;" vertex="1">
  <mxGeometry x="580" y="110" width="480" height="920" as="geometry"/>
</mxCell>
```

容器内子元素用 `parent="container_id"`，坐标相对于容器。

### 连线样式

**最重要的样式规则**：所有箭头用开放式 V 形箭头（open chevron）。

```
endArrow=open;endSize=14;
```

这是 Anthropic 图表最具辨识度的元素。绝不用实心三角箭头。

所有连线同时用 `edgeStyle=orthogonalEdgeStyle`——直角弯折，干净规整。配合 `rounded=1`，转角是柔和曲线而非硬 90°。

| 连线类型 | 完整样式 |
|---|---|
| **Primary flow** | `endArrow=open;endSize=14;edgeStyle=orthogonalEdgeStyle;strokeColor=#7A756E;strokeWidth=1.8;rounded=1;exitX=1;exitY=0.5;entryX=0;entryY=0.5;exitPerimeter=0;entryPerimeter=0;` |
| **Optional / inferred** | `endArrow=open;endSize=14;edgeStyle=orthogonalEdgeStyle;strokeColor=#9A948C;strokeWidth=1.6;rounded=1;dashed=1;dashPattern=6 6;exitPerimeter=0;entryPerimeter=0;` |
| **Feedback loop** | `endArrow=open;endSize=14;edgeStyle=orthogonalEdgeStyle;strokeColor=#8E8982;strokeWidth=1.8;rounded=1;curved=1;exitPerimeter=0;entryPerimeter=0;` |
| **Human override** | `endArrow=open;endSize=14;edgeStyle=orthogonalEdgeStyle;strokeColor=#D88966;strokeWidth=1.8;rounded=1;dashed=1;dashPattern=6 6;exitPerimeter=0;entryPerimeter=0;` |
| **Context link** | `endArrow=open;endSize=14;edgeStyle=orthogonalEdgeStyle;strokeColor=#7FB08F;strokeWidth=1.8;rounded=1;exitPerimeter=0;entryPerimeter=0;` |
| **Error path** | `endArrow=open;endSize=14;edgeStyle=orthogonalEdgeStyle;strokeColor=#D96B63;strokeWidth=1.8;rounded=1;dashed=1;exitPerimeter=0;entryPerimeter=0;` |

**连线 XML 结构（必须遵守）：**
```xml
<mxCell id="e1" source="n1" target="n2" style="..." edge="1" parent="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

**关键规则：**
1. **必须包含 `exitPerimeter=0` 和 `entryPerimeter=0`** —— 否则锚点 (`exitX`/`entryX`) 不生效，连线会直接连到节点中心
2. **必须包含 `<mxGeometry relative="1" as="geometry"/>` 子元素** —— 否则 `orthogonalEdgeStyle` 不渲染，连线不显示
3. 锚点用 `exitX=1;exitY=0.5`（右侧中点）和 `entryX=0;entryY=0.5`（左侧中点）实现左到右的流向

---

## Step 4: 写入文件

将生成的 XML 写入 `.drawio` 文件：

```bash
OUTPUT_DIR="${ROXY_WORKSPACE:?ROXY_WORKSPACE is required}/diagrams"
mkdir -p "$OUTPUT_DIR"
echo "$XML_CONTENT" > "$OUTPUT_DIR/<diagram_name>.drawio"
```

文件名建议：
- 用下划线分隔的英文或拼音
- 例：`agent_loop.drawio`、`rag_comparison.drawio`、`multi_agent_arch.drawio`

---

## Step 5: 导出 PNG（必须）

**PNG 是最终交付物，必须执行。**

检测到 draw.io CLI 路径（优先顺序）：
1. `/usr/bin/drawio`
2. `drawio` (PATH 中)
3. `/opt/drawio/drawio`
4. Windows: `"C:\Program Files\draw.io\draw.io.exe"`
5. macOS: `/Applications/draw.io.app/Contents/MacOS/draw.io`

导出命令：
```bash
OUTPUT_DIR="${ROXY_WORKSPACE:?ROXY_WORKSPACE is required}/diagrams"
drawio -x -f png -b 20 -o "$OUTPUT_DIR/<name>.png" "$OUTPUT_DIR/<name>.drawio"
```

**关键参数：**
- `-x`: 批量导出模式
- `-f png`: 输出格式 PNG
- `-b 20`: 缩放倍数 20（高质量）
- **禁止使用 `-e` 参数** —— 会导致 PNG 文件损坏（zTXt CRC 错误）

导出成功后，**必须将 PNG 图片发送给用户**。

---

## 视觉风格原则

1. **温暖画布** —— 背景色 `#F2EFE8`，非纯白
2. **颜色编码含义** —— 每种语义角色有专属填充/描边色
3. **开放式 V 形箭头** —— 最具辨识度元素，绝不用实心三角
4. **正交连线 + 柔和圆角** —— 干净规整，对角线禁用
5. **外边框框架** —— 每张图有细线条圆角矩形包裹
6. **大型编辑风格标题** —— 加粗、深色、居中
7. **无阴影、无渐变、无高饱和** —— 克制对比，靠排版与留白建层级

---

## 图表模式库

| 模式 | 适用场景 |
|---|---|
| **Linear Workflow** | 顺序步骤，一个环节引出下一个 |
| **Feedback Loop Workflow** | 重试、迭代、评估闭环 |
| **Branch Workflow / Decision Tree** | 分支逻辑、路由、审批关卡 |
| **Parallel Fan-out / Fan-in** | 并发执行者、结果聚合 |
| **Split Comparison** | 前后对比、两种方案并排 |
| **Grouped Architecture** | 系统边界、组件、包含关系 |
| **Layered Stack** | 层级关系、抽象层、依赖 |
| **Swimlane Sequence** | 多参与者随时间交互 |
| **Hub-and-Spoke** | 一核心概念及其支撑想法 |
| **Venn / Overlap** | 共享归属、领域汇合 |
| **Editorial Chart** | 数值比较、指标对照 |
| **Callout Annotation** | 解释主图的补充说明 |

模式可组合（如"分组架构 + 注释标注"），但必须有主模式。详细规则见 `references/pattern-library.md`。

---

## 语义化颜色系统

颜色按**语义角色**分配，非审美装饰。映射保持一致：

| 角色 | 填充色 | 描边色 |
|---|---|---|
| 主要 / 中性 | #E6E2DA | #8C867F |
| 次要 / 上下文（文件、工具、文档） | #EAF4FB | #6FA8D6 |
| 第三层 / 控制（路由、记忆、编排） | #EEEAF9 | #9A90D6 |
| 起始 / 触发（用户输入、外部触发） | #F8E9E1 | #D88966 |
| 结束 / 成功 | #CFE8D7 | #71AE88 |
| 警告 / 重置（重试、中断） | #F3E4DA | #C88E6A |
| 决策（分支、关卡、审批） | #E6D7B4 | #BFA777 |
| AI / LLM（模型调用、代理工作者） | #D7E6DC | #7FB08F |
| 非活动 / 已禁用 | #EFECE6 | #B4AEA6 |
| 错误 | #F8DFDA | #D96B63 |

读者无需先读标签，仅凭颜色就能判断结构角色。详见 `references/color-palette.md`。

---

## 质量检查清单

**生成前（DiagramSpec 阶段）：**
- [ ] main_claim 是否一句话能说清？
- [ ] 模式选择是否匹配用户意图？
- [ ] 阅读方向是否 obvious（3 秒内能看出从哪开始）？
- [ ] 节点数量是否在合理范围（简单 3–5，中等 6–9，密集 10+）？
- [ ] 连线是否避免交叉混乱？
- [ ] 所有文本语言是否与用户一致？

**生成后（XML 阶段）：**
- [ ] 箭头是否全是 open chevron（`endArrow=open;endSize=14;`）？
- [ ] 是否避免了实心三角、阴影、渐变？
- [ ] 容器嵌套是否不超过 3 层？
- [ ] **所有连线是否包含 `exitPerimeter=0;entryPerimeter=0;`？**（否则锚点不生效）
- [ ] **所有连线是否包含 `<mxGeometry relative="1" as="geometry"/>` 子元素？**（否则正交连线不显示）

**导出前（PNG 阶段）：**
- [ ] 导出命令是否**未使用 `-e` 参数**？（会导致 PNG 损坏）
- [ ] PIL 是否能正常打开生成的 PNG？（验证文件完整性）

---

## 使用说明

**触发词**：画流程图、画架构图、帮我画、draw a diagram、create a flowchart、visualize this process、make an architecture diagram、可视化这个流程、做个对比图、画泳道图

**无需特殊语法**，自然语言描述即可。技能自动匹配中英文。

**输出位置**：`$ROXY_WORKSPACE/diagrams/`

**打开方式**：
- 在线：拖入 https://app.diagrams.net/
- 本地：安装 draw.io Desktop 后双击 `.drawio` 文件
- PNG/SVG：若已安装 draw.io Desktop，Step 5 会自动导出

---

## 设计理念

> 好的图表不应只是展示信息，而应让其观点一目了然。

三个核心理念：
1. **先模式，后像素** —— 先选正确结构模式，再处理样式
2. **语义化颜色** —— 每种颜色都在传达含义，颜色本身就是信息
3. **克制是质量信号** —— 无阴影、无渐变、不过度装饰；平静留白比繁杂更可信

这些原则正是"编辑型技术图表"（用于文章解释观点）区别于 UI 仪表盘或企业架构工具图的关键。

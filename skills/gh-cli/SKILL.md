---
name: gh-cli
description: 使用 GitHub CLI (gh) 操作 GitHub 的 repositories、issues、pull requests、workflows、releases、代码搜索及 API 调用。触发词：github, gh, 代码库, 仓库, 推送, 提交, 分支, issue, pr, pull request, release, 工作流, workflow, 搜索代码, 查代码, push, commit, branch, 读文件, 合并
metadata: {"roxy": {"always": false, "requires": {"bins": ["gh"], "env": []}}}
---

# GitHub CLI (gh) Skill

用 `gh` CLI 代替 GitHub MCP，覆盖更全的操作面。所有命令优先走 JSON 输出以便解析。

## 核心原则

- 所有命令加 `--json <字段>` 得到机器可读的结构化输出，不要用人类格式
- `--jq` 是内置过滤器，无需另外安装 jq
- 不在 git 目录内时必须加 `-R owner/repo` 指定仓库
- 失败时用 `2>/dev/null || echo "{}"` 兜底

---

## 1. 文件操作（替代 get_file_contents / create_or_update_file / delete_file）

```bash
# 读文件
gh api repos/{owner}/{repo}/contents/{path}
gh api repos/{owner}/{repo}/contents/{path}?ref={branch}

# 写/更新文件（base64 编码内容）
gh api -X PUT repos/{owner}/{repo}/contents/{path} \
  -f message="commit message" \
  -f content="{base64_content}" \
  -f branch="{branch}"

# 带 sha（更新已有文件时必须）
gh api -X PUT repos/{owner}/{repo}/contents/{path} \
  -f message="update" \
  -f content="{base64_content}" \
  -f sha="{current_file_sha}" \
  -f branch="{branch}"

# 删除文件
gh api -X DELETE repos/{owner}/{repo}/contents/{path} \
  -f message="delete" \
  -f sha="{current_file_sha}" \
  -f branch="{branch}"
```

**注意**：`gh api` 返回的 content 是 base64 编码的，需要用 `--jq '.content'` 提取后 base64 -d 解码。

## 2. 代码搜索（替代 search_code）

```bash
# 搜索代码
gh search code "{query}" -R {owner}/{repo} --json path,repo,nameWithOwner

# 限制数量和语言
gh search code "{query}" --limit 5 --language=go --json path,repo

# 指定仓库范围
gh search code "{query}" -R kachofugetsu09/akasha-private --json path,url
```

## 3. Commit 与分支（替代 list_commits / list_branches / create_branch）

```bash
# 列出最近 commit
gh api repos/{owner}/{repo}/commits --json sha,commit,author --jq '.[:5]'

# 列出分支
gh api repos/{owner}/{repo}/branches --json name,commit

# 创建分支（基于 ref）
gh api repos/{owner}/{repo}/git/refs \
  -f ref="refs/heads/{branch_name}" \
  -f sha="{base_sha}"

# 查看最新 commit sha 用于创建分支
gh api repos/{owner}/{repo}/branches/{base_branch} --json commit --jq '.commit.sha'
```

## 4. Push Files（替代 push_files，需要 git 配合）

```bash
# gh 本身不支持多文件原子 push，用 git 组合拳：
# git clone --depth 1 {repo_url} /tmp/{repo}
# cd /tmp/{repo} && git checkout -b {branch}
# 写文件
# git add . && git commit -m "message"
# git push origin {branch}
# rm -rf /tmp/{repo}
```

临时 clone + git push 的方式实现，用完删除。

## 5. Release 管理（替代 list_releases / get_latest_release / get_release_by_tag）

```bash
# 列出 release
gh release list -R {owner}/{repo} --json tagName,isLatest,createdAt,name

# 查看最新 release
gh release view --json tagName,body,createdAt,name -R {owner}/{repo}

# 查看指定 tag
gh release view {tag} --json tagName,body,createdAt -R {owner}/{repo}
```

## 6. Issue 操作（MCP 没有的）

```bash
# 列出 issue（默认 open）
gh issue list -R {owner}/{repo} --json number,title,state,labels,assignees -L 10

# 查看详情
gh issue view {number} -R {owner}/{repo} --json number,title,body,state,labels,comments

# 创建 issue
gh issue create -R {owner}/{repo} --title "{title}" --body "{body}"

# 按 label 筛选
gh issue list -R {owner}/{repo} --label "bug" --json number,title
```

## 7. Pull Request 操作（MCP 没有的）

```bash
# 列出 open PR
gh pr list -R {owner}/{repo} --json number,title,author,labels,mergeable,reviewDecision

# 查看 PR 详情
gh pr view {number} -R {owner}/{repo} --json number,title,body,state,mergeable,reviewDecision,statusCheckRollup

# 创建 PR
gh pr create -R {owner}/{repo} --title "{title}" --body "{body}" --base {base_branch} --head {head_branch}

# 查看 CI 状态
gh pr checks {number} -R {owner}/{repo} --json name,state,conclusion,detailsUrl

# 合并 PR
gh pr merge {number} -R {owner}/{repo} --merge
```

## 8. Workflow / Action 操作（MCP 没有的）

```bash
# 列出 workflow
gh workflow list -R {owner}/{repo} --json name,state,path

# 手动触发
gh workflow run {workflow_name_or_id} -R {owner}/{repo}

# 带参数触发
gh workflow run {workflow} -R {owner}/{repo} -f param1=value1

# 列出最近 runs
gh run list -R {owner}/{repo} --json databaseId,status,conclusion,name -L 5

# 查看 run 详情
gh run view {run_id} -R {owner}/{repo} --json conclusion,status,jobs

# 查看失败日志
gh run view {run_id} -R {owner}/{repo} --log-failed
```

## 9. 通用 API（兜底方案）

任何 `gh` 子命令没覆盖的操作，直接走 REST API：

```bash
gh api repos/{owner}/{repo}/{endpoint} --json ...
gh api repos/{owner}/{repo}/issues --paginate --jq '.[].number'
gh api /search/issues?q=repo:{owner}/{repo}+state:open+label:bug
```

---

## 关键字段速查

**PR Fields**: `number`, `title`, `body`, `state`, `author`, `labels`, `assignees`, `reviewDecision`, `mergeable`, `statusCheckRollup`, `headRefName`, `baseRefName`, `isDraft`, `url`, `createdAt`

**Issue Fields**: `number`, `title`, `body`, `state`, `labels`, `assignees`, `comments`, `milestone`, `url`

**Run Fields**: `databaseId`, `name`, `status`, `conclusion`, `jobs`, `createdAt`, `event`

**File Content**: `name`, `path`, `sha`, `size`, `content`(base64), `encoding`, `type`

**Commit Fields**: `sha`, `commit.message`, `commit.author.name`, `commit.author.date`

---

## 初始化检查

调用本 skill 前，先确认：
1. `gh` CLI 已安装 → 用 `which gh`
2. 已认证 → 用 `gh auth status`
3. 未登录则提示用户 `gh auth login`

## 注意事项

- **删除/合并等破坏性操作**：执行前先列出确认信息，不要直接执行
- **写文件必须先读 sha**：更新文件时必须传入当前 sha，先读再写
- **批量写文件**：走 git clone + commit + push 路线
- **长期运行的任务**：`gh run watch` 会阻塞，考虑 spawn 后台执行

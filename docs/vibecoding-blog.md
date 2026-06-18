---
title: 鹊随金印：一个 IT 运维工程师的 AI 编程实战报告
date: 2026-06-19
categories: 开发基础
cover: https://cdn.sujx.net/covers/cover155.jpg
tags:
  - Python
  - Flask
  - Vue
  - Vibe Coding
  - AI 编程
  - Docker
---

> 用 Claude Code 从零搭建一站式文档处理工具箱。13 个功能模块、17,000 行代码、30+ 次排错经验，以及一个非专业开发者踩过的所有坑。

![](https://cdn.sujx.net/covers/cover155.jpg)

## 起因

我是一名 IT 售前和运维工程师，日常工作要处理大量文档：Markdown 方案转公文、PDF 加水印、Excel 合并、视频转格式……每个操作都散落在不同工具之间。

最初用 Qoder 做了几个独立 Web 小工具，但工具越做越多，代码扔得到处都是，接口不统一，修改也一团乱麻。于是把所有工具整合到一个工具箱里——这就是「鹊随金印」的由来。

## 最终成果

| 分类 | 行数 |
|------|------|
| 后端 Python（14 services + 15 blueprints + utils） | 6,727 |
| 前端 Vue（16 pages + 20 components） | 3,938 |
| 前端 TypeScript（6 composables + 2 plugins + config） | 1,274 |
| 测试（pytest + vitest） | 747 |
| i18n 翻译（zh-CN + en） | 786 |
| 文档（SPEC + README + CLAUDE + 部署脚本） | 3,800 |
| **总计** | **17,400** |

核心技术栈：Flask + Celery + Nuxt 3 + Nuxt UI v2 + Tailwind CSS v3 + SQLite + Redis + Docker Compose。

## 怎么做到的

### 1. 让 AI 先读规范，再写代码

项目根目录放了三个文件让 Claude Code 每次启动自动加载：

- **CLAUDE.md**：项目结构和命名规范，告诉 AI"用什么框架、文件放哪、函数叫啥名"
- **SPEC.md**：设计系统文档（配色 Token、字体、圆角、阴影、WCAG 合规清单），所有视觉决策一次定义
- **README.md**：功能清单和部署方式，AI 据此理解整体架构

真正省时间的地方在于：**不需要在每次对话中重复解释项目背景**。AI 自动知道"这个项目用 Flat Design 而不是 Material Design"，"Service 函数必须返回 ServiceResult 而不是裸 dict"。

### 2. 先搭骨架，再填肉

第一天的目标不是实现任何功能，而是建好框架：

- 后端：Flask 工厂模式（`create_app()` 不到 70 行）、Blueprint 注册、Service 层接口定义
- 前端：Nuxt 3 布局、侧边导航、路由结构、i18n 配置
- 基础设施：Celery 配置、全局异常拦截、操作日志中间件

骨架搭好后，每个新功能只需要写三个文件（Blueprint + Service + Vue 组件），再加两行注册代码。

### 3. tools.config.ts —— 单一数据源

前端 13 个工具的侧栏导航、仪表盘卡片、路由全部由 `composables/tools.config.ts` 这一个数组驱动：

```ts
{ key: "video-convert", to: "/video-convert", icon: "i-heroicons-video-camera",
  label: "tabs.videoConvert", order: 6 },
```

加一行就能同时更新侧边栏和仪表盘，不需要改两个地方的代码。未来做可插拔模块架构时，这个文件就是模块注册表的雏形。

## 踩过的坑：AI 编程的真实一面

> 如果你看到某个 AI 编程项目「一次通过零 bug」，那不是运气好，是项目太简单。

### 视频转换功能：一个功能的 10 次提交

视频转换（MP4 → WMV）是 v3.6 的新功能，也是排错次数最多的一个。完整的问题链条：

```
按钮点击无响应 → defineAsyncComponent 事件绑定丢失
→ 改用直接 import
→ 后端 import 路径不一致（tasks.video vs backend.tasks.video）
→ Celery task 名称不匹配（KeyError: unregistered task）
→ update_progress 参数名拼错（progress_message vs message）
→ MP4 魔数校验误杀合法文件（ftyp box 大小不固定）
→ libopenh264 解码器缺失
→ WMV 浏览器无法预览
→ 转换中 DOM 销毁/重建导致视觉闪烁
```

每层都是独立的问题，没有一个是因为业务逻辑复杂。**基础设施的健壮性决定了开发体验的下限。**

### Docker 构建缓存：花了一天半才搞定的 bug

生产部署后全部 JS 文件 404。排查过程：

1. 怀疑是 Docker 缓存 → 加 `--no-cache` 重构建（慢 3 倍，问题依旧）
2. 怀疑是 `ARG BUST_FRONTEND` 没生效 → 发现 ARG 只是声明了，RUN 里没引用 `${BUST_FRONTEND}`，Docker 直接忽略
3. 怀疑是 nginx 配置 → 发现 `location /_nuxt/` 写了 `expires` 但没写 `proxy_pass`
4. 最终：ARG 被 RUN 引用 + nginx proxy_pass 补全 → 问题解决

**教训：Docker ARG 必须在 RUN 指令中被 `${}` 引用才会破坏缓存层。** 声明 ARG 但不用 = 没用。

### gunicorn 找不到：pip 镜像的坑

生产容器启动报 `exec: gunicorn: not found`。Dockerfile 明明写了 `pip install gunicorn`。最终发现是阿里云 PyPI 镜像漏了这个包，本地一直 OK（用了缓存层），推送到 ECS rebuild 时就挂了。

**修复**：pip install 失败时自动回退到 PyPI 官方源，并在构建后验证 `gunicorn --version`；entrypoint 启动时也检查关键二进制是否存在。

### defineAsyncComponent 的隐秘 bug

视频转换页面的「转换」按钮点击后什么也不发生——没有 toast，没有报错，就是什么都没发生。debug 半天发现 `convert()` 函数根本没被调用。

换了好几种方案：加 `type="button"`、`@click.prevent.stop`、原生 button 替代 UButton —— 全都没用。最后发现是 `defineAsyncComponent(() => import(...))` 在 Nuxt 3.15 + Vite 6 下偶发事件处理器不绑定。改成静态 `import` 后问题消失。

### `v-if` 闪跳：看似简单的 UI 问题背后的 DOM 原理

转换过程中「源视频预览 → loading 动画 → 结果展示」三个状态切换时，用户报告「闪一下就跳回去了」。初始以为是状态管理 bug，反复检查 ref 赋值逻辑都没问题。

真正原因：`v-if="converting"` 让视频元素在转换开始时从 DOM 中销毁，转换结束时又重建。这个销毁/重建周期在人眼中就是「闪烁」。修复方案不是改状态逻辑，而是改用 **overlay 遮罩层**覆盖在视频上，让视频元素始终保持在 DOM 中。

### CORS 配置与运维环境脱节

Docker 容器里 API 正常，但通过 nginx 反向代理访问就 500。代码里 `CORS_ORIGINS` 默认值是 `http://localhost:8080`，而生产 nginx 用的是 `https://doc.sujx.net`——域名不在白名单里，浏览器拦截。

**教训**：CORS、CSRF、Cookie domain 这些跨层配置，必须和部署环境一起验证。本地测试通过的配置不等于生产可用。

### SQLite 数据重启丢失

用户反馈「使用统计」页面的数据每次重启 Docker 就没了。一看 docker-compose —— `output_data`、`log_data`、`redis_data` 三个 volume 都挂载了，唯独 SQLite 数据库文件没挂。容器一重启，数据文件消失。

**修复**：5 个 compose 文件全部加上 `db_data` 卷 + `DOCSTAMP_TASK_DB` 环境变量。Dockerfile 预创建挂载目录并 chown 给非 root 用户（Docker 新 volume 默认 root 拥有，app 以 docstamp 用户运行无写权限）。

### AI 生成的代码审查报告不可信

两次收到外部"AI 代码审查报告"——一共 50+ 条建议，声称有 SQL 注入风险、SSRF 漏洞、过渡依赖 python-dotenv、缺少 SSE 断线重连等。逐一核实后发现：

- "SQL 注入风险"：代码全部使用 `?` 占位符参数化查询，不存在拼接
- "SSRF 漏洞"：文件路径已通过 `secure_filename()` 和 `FORBIDDEN_PATH_CHARS` 过滤
- "SSE 缺少断线重连"：浏览器 EventSource 协议自带指数退避重连，不需要手动实现
- "过渡依赖 python-dotenv"：Docker 内无 `.env` 文件，三层降级机制（compose env → EnvironmentFile → dotenv）
- 80% 的"问题"实际已经修复或不存在

**教训**：AI 审报告 ≠ 人工审核。两份报告虽然格式精美，但分析质量只相当于「看了一遍项目结构而没有读任何一行代码」。真正有效的质量保障是**写测试 + 读代码**。

## AI 编程实战手册

把这些坑总结成了一份可以在其他项目中复用的排错清单，放在 `~/.claude/CLAUDE.md` 里。核心条目：

**Docker**：ARG 必须被 RUN 引用、npm ci 加 ETXTBSY 重试、新 volume 必须预创建目录 + chown、SQLite 必须挂 volume。

**后端**：Celery task 名称必须和 blueprint 中 `delay()` 一致、Service 函数必须捕获文件 I/O 异常、魔数校验不可靠的格式直接跳过、import 用全限定路径。

**前端**：defineAsyncComponent 优先用静态 import、下载链接先 appendChild 再 click、`v-if` 块级切换 → overlay 遮罩、URL.createObjectURL 记得 revoke。

**部署**：CORS 白名单含 nginx 域名、`location /_nuxt/` 要写 proxy_pass、gunicorn 入口用 `wsgi:app` 而不是 `app:app`、字体 CDN → 自托管。

**流程**：先写测试再改代码、新功能先跑通端到端、模糊报错先加诊断日志、别信 AI 生成的代码审查报告。

完整的 28 条规则已开源在项目 CLAUDE.md 中。

## 部署方案

项目跑在一台 2C2G 阿里云 ECS 上，Docker Compose Lite 模式（3 个容器：API + Redis + Celery 合并），内存占用约 800MB（含 LibreOffice 按需调用）。Nginx 做反向代理，`/_nuxt/` 静态资源设置 1 年强缓存，视频转换走 Celery 异步任务 + SSE 实时进度。

完整部署链：

```
本地 git push → Gitee → ECS git pull → docker compose up -d
```

ACR 镜像发布则多一步：

```
./publish.sh → docker build + push ACR → ECS docker compose pull → up -d
```

## 总结

**第一，Vibe Coding 的效率是真实的。** 17,000 行代码、13 个功能模块、5 套 compose 部署方案、Docker + 裸机 + Systemd 全链路——从零到完整交付不到一个月。一个非专业开发者能做到这个程度，在传统开发模式下不可想象。

**第二，AI 编程不是「说句话就完了」。** 视频转换功能的 10 次提交、Docker 缓存的一天半排查、defineAsyncComponent 的诡异 bug——这些问题没有一个是因为「AI 代码写得差」，都是基础设施、工具链、框架层面的坑。AI 可以写代码，但它不会帮你理解 build cache 的底层机制，也不会替你检查 nginx 配置。

**第三，规范文档是 AI 编程的杠杆。** CLAUDE.md + SPEC.md 的投资回报率高得离谱。每次对话都在同一个上下文里，不需要重复解释背景，AI 产出的代码自然保持一致。

**第四，测试是对抗复杂性的唯一武器。** 不是「有测试就放心重构」——而是写测试的过程本身就在暴露问题。pytest 12 条测试发现了 3 个未处理异常，这 3 个异常在手工测试中从未触发过，但它们确实存在。

**第五，别迷信 AI 的「审查能力」。** AI 可以帮你发现格式问题、命名不一致、dead code——但逻辑正确性必须人工验证。收到代码审查报告时，逐条核实比直接采纳更有价值。

# docStamp 项目待办

> 最后更新：2026-09-23（对应 commit `86ad4f3`）
>
> 本文件只放**已知但刻意未做**的遗留项与运维待办。已完成的变更不在这里，见 `SPEC.md` 的版本历史。
> 每条都注明「为什么没做」，避免下一轮把同一件事重新调研一遍。

## 一、Docker / 部署

- [ ] **服务器从 2 容器切到单容器新镜像** —— 用户明确「服务器上先不动，后期更新 docker 镜像来解决」。本机已完成镜像验收（健康检查 200、SPA 217KB、`X-API-Version: 3.7`、pandoc 2.17.1.1 / pdftoppm 22.12.0、`.cleanup-stamp` 与 tasks.db(WAL) 正常落盘），但**生产切换仍未经实证**。
- [ ] **服务器运维 `.env` 删掉 AI / DeepSeek 注入行** —— 仓库与开发机均无 `.env`（gitignored），`compose` 与 `.env.example` 已无 `AI_*`。因 compose 不再注入，服务器上残留的那一行现在是惰性的；但 key 已吊销，删掉更干净。
- [ ] **`docker-compose.yml` 传 `--workers 2`，但 `Dockerfile` 的 `CMD` 没传** —— 裸 `docker run`（不带 compose）会落到 `backend/gunicorn.conf.py` 的 `workers = min(8, cpu_count*2+1)`，2 核机器 = 5 个 worker。生产走 compose 故被兜住；若允许裸跑，应把 `--workers` 补进 `CMD`。
- [ ] **`backend/gunicorn.conf.py` 的 `pidfile = "/var/run/docstamp.pid"` 是死配置** —— `Dockerfile` 与 compose 都传了 `--pid /tmp/gunicorn.pid` 覆盖它，且 `docstamp` 用户对 `/var/run` 本来就无写权。留着容易误导，可删。
- [ ] **`.dockerignore` / `.gitattributes` 未在 `.gitattributes` 里钉 `eol=lf`** —— `git add` 会警告「下次 touch 转 CRLF」。实测无碍（Go 的行扫描器会剥掉 `\r`，git 属性解析器也容忍 `\r`），故按「先证明再修」留着。

## 二、整站级（后端 i18n 等）

- [ ] **上传路径校验错误文案仍是英文** —— `save_upload` / `file_security` 抛的 `ValueError` 被全站工具共享，一条文案影响所有上传入口，属整站级后端 i18n 决策，不做单点修补。
- [ ] **`manage.sh` 调 `python3`，在本机是 Windows Store 残桩** —— 起不来后端，只能直接调 `/c/Program Files/Python312/python`。涉及 `start` / `test` / `test-cov` 三处。
- [ ] **开发模式（`python app.py`）没有清理线程** —— 每日清理只挂在 gunicorn 的 `on_starting`，dev 机器只能靠 `./manage.sh clean-output` 手动清。

## 三、测试与数据

- [ ] **测试会往真实 `backend/tasks.db` 写流水，污染统计** —— `backend/tests/conftest.py` 的 `app` fixture 只覆盖了 `UPLOAD_FOLDER`，**没有覆盖 `TASK_DB_PATH`**；而 `create_app()` 内部会 `init_db()` 并打开真实 DB。早年用来隔离 DB 的 fixture 已随异步链路一起拆除，现在没有任何用例隔离 DB。**实测证据**：`2026-09-23` 当天 522 行 `operation_logs` 的 `ip_address` **全部是 `127.0.0.1`**，即本机 pytest / dev 产生，不是真实访客。修法：给 `app` fixture 把 `TASK_DB_PATH` 指向 `tmp_path`。
      **⚠ 不要去删那些已写入的测试行** —— 上次 `tasks.db` 索引损坏（幽灵索引条目、`count(*)` 多报）正是历史删行造成的，删行会重演同样的损坏。
- [ ] **`backend/tasks.db.bak-20260923`（含 `-shm` / `-wal`）留在磁盘** —— 索引修复前的安全网，已确认修复成功（`integrity_check` ok），可择日删除。
- [ ] **`backend/tests/__pycache__/` 有 5 个已删除测试模块的残留 `.pyc`** —— `company_lookup` / `task_tracking` / `video_converter` / `watermark` / `worker`。纯本机杂物，`.dockerignore` 已挡住不进镜像，可直接删该目录。

## 四、其他

- [ ] **Gitee 上的旧仓库未删除** —— 用户已舍弃 Gitee，GitHub（https://github.com/sujx/DocStamp ，public）是唯一远端；Gitee 那个仓要清理需自行去删。
- [ ] **`edffc8c` 的 commit message 里含已吊销的 DeepSeek key** —— 无可达 blob（不在任何文件内容里），已向用户披露，**刻意不改写历史**。
- [ ] **`docs/` 被 `.gitignore` 整目录忽略，但 `docs/vibecoding-blog.md` 已跟踪** —— 结果是新加到 `docs/` 的文件不会进仓库（`docs/plans/` 现在就是未跟踪状态）。若这是有意为之可忽略；否则需调 `.gitignore` 规则或用 `git add -f`。

## 刻意不动的历史产物（别再当"过期"去改）

- `docs/vibecoding-blog.md` —— 2026-06-19 已发布文章的原文，里面的模块数 / 页面数等计数已过期，但改它就是错的。
- `SPEC.md` 版本历史 —— `v3.7.6` 记录删 AI、`v3.6` 起提到 Celery / SSE / worker / `useError.ts` 的条目都是当时的发布记录，不随现状删改。

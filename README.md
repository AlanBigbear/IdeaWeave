# B-Star 虚拟编导工作台

小团队 B 站 UP 主的前期创作 Demo：粘贴文本 → LangChain 调大模型 → MySQL 存储。不处理图片 / 视频。

## 能做什么

登录后先选人设（分区、风格、更新、评论习惯），第 6 步可让 AI 把人设**编译成专属编导 Skill**（个性化 Prompt），再按侧栏走：

- **专属编导 Skill**：AI 按人设生成频道定位、3 个专属钩子公式、语言风格规则、选题偏好、脚本骨架、互动玩法、内容红线，并合成一份可手动微调的 Skill Prompt，注入后续所有 AI 模块；设置页可随时重新生成或编辑
- **灵感采集**：粘贴爆款摘要，或粘贴内容链接一键「抓取 → AI 读原文 → 提爆点」入库（带内网地址拦截等安全防护）
- **选题库**：短平快 / 高成本筛选，随手记灵感，导出 Markdown
- **编导创意**：一个模糊想法 → 3 个差异化方案
- **大纲扩写**：大纲 + 拍摄清单 → 脚本、6 套封面 Prompt、审核风险
- **热点日历**：一键捕捉近 30 天节日/大促/分区热点（宁缺毋滥），也可手动增删改，或粘贴文本提取
- **设置**：人设、专属 Skill、OpenAI 兼容模型（base_url / model / api_key）

## 本机启动

需要 Python 3.11+、Node 20+。

```bash
# 后端
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # 已有可跳过
uvicorn app.main:app --reload --port 8000

# 前端（另开终端）
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173 → 注册登录 → 完善人设；也可以在登录页选一个体验空间直接进入。默认已接 DeepSeek `deepseek-v4-pro`（Key 可写在 `backend/.env` 的 `DEFAULT_LLM_API_KEY`，用户覆盖存在 `user_settings`）。

### 公共试用空间

- `POST /api/v1/auth/trial` 会给访客签发一个较短有效期的普通 JWT，不公开或校验试用密码；body 传 `{ "account": "tech" | "anime" | "pet" }` 选择空间，不传则默认 `tech`，非法 key 返回 422。
- 三个共享保留账号：`demo`（科技数码 · 数码省钱实验室）、`demo-anime`（二次元收藏 · 谷子收藏研究所）、`demo-pet`（萌宠动物 · 毛球生活观察局）。访客在登录页用三张卡片选择，保留用户名及其大小写变体都不能注册或密码登录。
- 所有访客共享所选账号，可以生成、编辑和删除内容；因此不要在试用空间填写隐私或敏感信息。三个账号共用一套按 IP 的进程内限流，切换空间不会放大模型额度。
- 后端启动时以及每隔 `TRIAL_RESET_MINUTES`（默认 60 分钟）会恢复每个账号各自的人设（数码省钱实验室 / 谷子收藏研究所 / 毛球生活观察局）和贯通各页面的示例数据。试用访客不能修改模型地址、模型名或 API Key，设置页会显示只读提示。
- 可在 `backend/.env` 设置 `TRIAL_ENABLED=false` 关闭入口，其他 `TRIAL_*` 默认值见 `backend/.env.example`。

独立 MySQL 8 基线文件为 `deploy/ideaweave_trial.sql`，同一事务内分三段写三个账号。它不建表、不包含明文密码或模型密钥，可在 **已创建 IdeaWeave schema** 的新库中导入。手动导入现有库前，请先备份并确认用户名 `demo` / `demo-anime` / `demo-pet` 已保留为可销毁的公共试用账号；脚本会替换且只替换这三个账号拥有的数据。SQLite 不需要导入 SQL，应用启动会通过同一套 Python 服务创建基线。注意已有 MySQL 数据卷不会自动重跑 init SQL，升级需备份后手动导入。

数据默认写入 MySQL（`DATABASE_URL`）。未配置时回退本地 `backend/data/bstar.db`。

可选：`docker compose up --build`，前端 http://localhost:8080 。

## 外网访问（ngrok）— 务必走生产构建

**不要**把 ngrok 指到 Vite 开发端口 `5173`。开发模式不打包，浏览器会逐个拉取几百个模块（`/@vite/client`、`/src/main.ts` 等），每个请求都过一遍隧道（单程常 300ms+），首次加载会卡几十秒。免费版 ngrok 还有人机验证拦截页，会再拖慢第一次。

正确做法：先构建前端，由 **FastAPI :8000** 托管 `frontend/dist`（Gzip + 静态缓存 + SPA 回退），ngrok 只打 8000。

```bash
# 1. 构建前端（每次改完前端都要再跑一遍）
cd frontend
npm install
npm run build

# 2. 启动 / 重启后端（必须在 dist 生成之后；--reload 不会自动发现新建的 dist）
cd ../backend
source .venv/bin/activate   # 已激活可跳过
uvicorn app.main:app --reload --port 8000

# 3. 另开终端，把隧道从 5173 改到 8000
#    若旧隧道还在指 5173，先 Ctrl+C 停掉
ngrok http 8000
```

然后用 ngrok 打印的 `https://xxxx.ngrok-free.dev` 访问。

效果：

- 请求从几百个降到十几个（打包 + 按需分包）
- Gzip 压缩（主包大约从 1MB+ 压到约 360KB）+ 带 hash 的资源长期缓存，二次访问很快
- 切 tab 不重新下载页面、不挡接口：先进缓存再后台刷新
- 页面和 `/api` 同源，少一跳 Vite 代理
- `/topics` 等前端路由由后端回退到 `index.html`，直接刷新不会 404

验证后端已挂上静态资源：打开 `http://127.0.0.1:8000` 应看到登录页，而不是 404；`http://127.0.0.1:8000/api/health` 仍返回 JSON。

**日常开发**继续用 `npm run dev`（http://localhost:5173 热更新），与 ngrok 互不影响。只有给别人看的外网链接才走 8000。

免费版 ngrok 首次打开仍可能出现拦截页，点 Visit Site 即可，这是 ngrok 行为，不是站点故障。

## 改了前端之后

- **本机看效果**：什么都不用做，`npm run dev`（5173）会热更新。
- **ngrok / 外网看效果**：重新打包一次即可。

```bash
cd frontend && npm run build
```

然后重启一次后端（`uvicorn`）。ngrok 不用动，继续指 8000。不打包的话外网还是旧页面。

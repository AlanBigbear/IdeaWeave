# B-Star 虚拟编导工作台

小团队 B 站 UP 主的前期创作 Demo：粘贴文本 → LangChain 调大模型 → 本地 SQLite 存储。不处理图片 / 视频。

## 能做什么

登录后先选人设（分区、风格、更新、评论习惯），再按侧栏走：

- **灵感采集**：粘贴爆款摘要，提取爆点入库
- **选题库**：短平快 / 高成本筛选，随手记灵感，导出 Markdown
- **编导创意**：一个模糊想法 → 3 个差异化方案
- **大纲扩写**：大纲 + 拍摄清单 → 脚本、6 套封面 Prompt、审核风险
- **热点日历**：粘贴展会文本 → 日历卡片
- **设置**：人设、OpenAI 兼容模型（base_url / model / api_key）

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

打开 http://localhost:5173 → 注册登录 → 完善人设 → **设置**里填大模型 Key。

数据在 `backend/data/`（SQLite）。API Key 只写本机 `secrets.json`，不进库、不进 git。

可选：`docker compose up --build`，前端 http://localhost:8080 。

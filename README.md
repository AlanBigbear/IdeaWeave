# B-Star 虚拟编导工作台

小团队 B 站 UP 主的前期创作 Demo：粘贴文本 → LangChain 调大模型 → MySQL 存储。不处理图片 / 视频。

## 能做什么

登录后先选人设（分区、风格、更新、评论习惯），第 6 步可让 AI 把人设**编译成专属编导 Skill**（个性化 Prompt），再按侧栏走：

- **专属编导 Skill**：AI 按人设生成频道定位、3 个专属钩子公式、语言风格规则、选题偏好、脚本骨架、互动玩法、内容红线，并合成一份可手动微调的 Skill Prompt，注入后续所有 AI 模块；设置页可随时重新生成或编辑
- **灵感采集**：粘贴爆款摘要，或粘贴内容链接一键「抓取 → AI 读原文 → 提爆点」入库（带内网地址拦截等安全防护）
- **选题库**：短平快 / 高成本筛选，随手记灵感，导出 Markdown
- **编导创意**：一个模糊想法 → 3 个差异化方案
- **大纲扩写**：大纲 + 拍摄清单 → 脚本、6 套封面 Prompt、审核风险
- **热点日历**：一键捕捉近 90 天节日/大促/分区热点，也可手动增删改，或粘贴文本提取
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

打开 http://localhost:5173 → 注册登录 → 完善人设。默认已接 DeepSeek `deepseek-v4-flash`（Key 可写在 `backend/.env` 的 `DEFAULT_LLM_API_KEY`，用户覆盖存在 MySQL `user_settings`）。

数据默认写入 MySQL（`DATABASE_URL`）。未配置时回退本地 `backend/data/bstar.db`。

可选：`docker compose up --build`，前端 http://localhost:8080 。

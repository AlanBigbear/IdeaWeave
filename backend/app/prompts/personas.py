PERSONA_TEMPLATES = [
    {
        "key": "experience",
        "name": "体验派长视频",
        "style_desc": (
            "对标 B 站体验派长视频编导：线下真实体验、展会/门店走访、"
            "用叙事带观众走完全过程。开头强钩子，中段有冲突与发现，结尾给可执行建议。"
        ),
        "audience": "关心生活方式、线下活动、消费决策的年轻 B 站用户",
        "video_format": "B 站中长视频 8–20 分钟，口播 + 实拍体验",
        "taboos": "未体验先吹、隐瞒广告、夸张对比、引战、低俗擦边",
        "sample_tone": "先抛冲突或好奇，再带观众走进现场，结尾给值不值得去的建议。",
        "zone": "生活区",
        "content_style": "线下体验 / 探店",
        "update_freq": "一周 1 更",
        "comment_style": "高回复，评论当选题来源",
    },
    {
        "key": "review",
        "name": "测评派",
        "style_desc": "对比、指标、踩坑清单。结论先行，论据扎实，适合数码/消费决策。",
        "audience": "准备下单、需要避坑的理性观众",
        "video_format": "8–15 分钟测评口播 + 实拍对比",
        "taboos": "虚构参数、未实测结论、只说优点",
        "sample_tone": "先给结论和适用人群，再用 3 个维度拆开测，最后给购买建议。",
        "zone": "科技区",
        "content_style": "测评对比",
        "update_freq": "一周 1 更",
        "comment_style": "理性答疑，少情绪、多结论",
    },
    {
        "key": "vlog",
        "name": "生活 Vlog",
        "style_desc": "日常切片、情绪共鸣、轻松陪伴感。叙事松弛但每段仍要有小钩子。",
        "audience": "喜欢陪伴感和生活气息的粉丝",
        "video_format": "5–12 分钟生活记录",
        "taboos": "过度炫耀、隐私泄露、无意义流水账",
        "sample_tone": "像跟朋友聊天一样讲今天发生的一件小事，但把转折讲清楚。",
        "zone": "生活区",
        "content_style": "生活 Vlog",
        "update_freq": "一周 2–3 更",
        "comment_style": "弹幕互动，口播里埋提问",
    },
]

PERSONA_OPTIONS = {
    "zones": [
        {"key": "life", "label": "生活区", "desc": "日常、居住、情绪陪伴", "emoji": "🏠"},
        {"key": "food", "label": "美食区", "desc": "探店、食评、厨房记录", "emoji": "🍜"},
        {"key": "fashion", "label": "时尚区", "desc": "穿搭、美妆、生活方式", "emoji": "✨"},
        {"key": "tech", "label": "科技区", "desc": "数码、测评、开箱", "emoji": "📱"},
        {"key": "game", "label": "游戏区", "desc": "实况、盘点、二创", "emoji": "🎮"},
        {"key": "knowledge", "label": "知识区", "desc": "科普、教程、深度口播", "emoji": "📚"},
        {"key": "sports", "label": "运动区", "desc": "健身、户外、赛事体验", "emoji": "🏃"},
        {"key": "cine", "label": "影视区", "desc": "影评、片场、二创解读", "emoji": "🎬"},
        {"key": "music", "label": "音乐区", "desc": "翻唱、乐评、现场", "emoji": "🎵"},
        {"key": "travel", "label": "旅游出行", "desc": "城市漫游、展会、路线", "emoji": "🧳"},
        {"key": "auto", "label": "汽车区", "desc": "试驾、改装、用车日常", "emoji": "🚗"},
        {"key": "animal", "label": "动物圈", "desc": "宠物日常、救助、科普", "emoji": "🐾"},
    ],
    "content_styles": [
        "线下体验 / 探店",
        "展会探访",
        "测评对比",
        "生活 Vlog",
        "教程干货",
        "开箱分享",
        "口播观点",
        "剧情短片",
    ],
    "update_freqs": [
        {"key": "daily", "label": "日更", "desc": "保持曝光，适合短内容"},
        {"key": "w2", "label": "一周 2–3 更", "desc": "小团队最常见节奏"},
        {"key": "w1", "label": "一周 1 更", "desc": "体验派长视频推荐"},
        {"key": "biweekly", "label": "双周更", "desc": "精品向，制作周期长"},
        {"key": "monthly", "label": "月更精品", "desc": "高成本项目再启动"},
    ],
    "comment_styles": [
        {"key": "high_reply", "label": "高回复", "desc": "认真回粉丝问题，评论当选题来源"},
        {"key": "pin_guide", "label": "置顶引导", "desc": "置顶路线、票价、是否广告"},
        {"key": "danmaku", "label": "弹幕互动", "desc": "口播里埋弹幕梗和提问"},
        {"key": "rational", "label": "理性答疑", "desc": "少情绪、多结论和依据"},
        {"key": "persona", "label": "人设口吻", "desc": "固定语气回复，强化记忆点"},
    ],
}


def get_template(key: str) -> dict | None:
    return next((item for item in PERSONA_TEMPLATES if item["key"] == key), None)


def _persona_fact_lines(persona) -> list[str]:
    return [
        f"UP 主名称：{persona.name}",
        f"所在分区：{getattr(persona, 'zone', '') or '未指定'}",
        f"内容风格：{getattr(persona, 'content_style', '') or persona.style_desc}",
        f"更新节奏：{getattr(persona, 'update_freq', '') or '未指定'}",
        f"评论互动：{getattr(persona, 'comment_style', '') or '未指定'}",
        f"风格说明：{persona.style_desc}",
        f"受众：{persona.audience}",
        f"视频形态：{persona.video_format}",
        f"禁忌：{persona.taboos}",
        f"口吻样例：{persona.sample_tone}",
    ]


def persona_skill_fact_sheet(persona) -> str:
    return "\n".join(_persona_fact_lines(persona))


def persona_system_prompt(persona) -> str:
    base = (
        "你是面向小团队 B 站 UP 主的虚拟编导助手。"
        "输出必须可执行，避免空泛鸡汤。默认中文。"
    )
    skill = (getattr(persona, "skill_prompt", "") or "").strip()
    if skill:
        return (
            f"{base}\n\n"
            f"【该 UP 主的专属编导 Skill】\n{skill}\n\n"
            f"【人设硬约束（与 Skill 冲突时以此为准，禁忌绝不可违反）】\n"
            + "\n".join(_persona_fact_lines(persona))
            + "\n请严格按照专属 Skill 的定位、钩子公式、语言规则、脚本结构和红线来执行任务。"
        )
    return (
        f"{base}\n"
        + "\n".join(_persona_fact_lines(persona))
        + "\n请始终按该人设的分区调性、更新节奏和评论互动习惯来生成。"
        "选题要贴合分区；脚本里预埋符合其评论风格的互动。"
    )

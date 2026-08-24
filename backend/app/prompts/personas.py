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

_COMMON_STYLES = ["口播观点", "剧情短片", "教程干货"]

_ZONE_CONTENT_STYLES: dict[str, list[str]] = {
    "life": ["生活 Vlog", "线下体验 / 探店", "好物分享", "改造 / 收纳", "情绪碎碎念", "挑战打卡"],
    "food": ["探店实测", "家常菜教程", "街头小吃地图", "美食测评", "深夜食堂", "烘焙甜品"],
    "fashion": ["穿搭实测", "美妆测评", "一衣多穿", "平价替代", "改造旧衣", "发型 / 妆容教程"],
    "tech": ["测评对比", "开箱首测", "数码好物", "装机 / 折腾指南", "软件技巧", "新品前瞻解读"],
    "game": ["实况高光", "整活挑战", "游戏盘点", "新手教学", "速通 / 挑战纪录", "怀旧怀旧服"],
    "knowledge": ["硬核科普", "误区澄清", "保姆级教程", "深度解读", "冷知识盘点", "读书 / 涨知识"],
    "sports": ["训练打卡", "运动挑战", "装备实测", "赛事解读", "入门教学", "户外探险"],
    "cine": ["新片首评", "细节解读", "片单盘点", "拉片教学", "烂片吐槽", "幕后八卦考据"],
    "music": ["现场记录", "翻唱改编", "乐评速听", "编曲拆解", "乐器教学", "歌单盘点"],
    "travel": ["展会探访", "城市漫游", "穷游攻略", "避坑实测", "小众目的地", "特种兵行程"],
    "auto": ["试驾实测", "养车成本", "用车技巧", "改装记录", "新能源体验", "二手车避坑"],
    "animal": ["宠物日常", "救助记录", "养宠科普", "萌宠挑战", "宠物好物", "云吸猫狗"],
    "dance": ["翻跳实测", "宅舞打卡", "原创编舞", "舞室 vlog", "零基础教学", "齐舞舞台"],
    "otaku": ["手办开箱", "谷子吃谷", "漫展游记", "痛包分享", "模型制作", "二次元好物"],
    "danmu": ["鬼畜调音", "名场面二创", "配音整活", "mad/amv", "热梗混剪", "空耳合集"],
    "funny": ["街头整活", "情景短剧", "吐槽大会", "沙雕日常", "挑战企划", "评论区点梗"],
    "vlog_ent": ["明星动态盘点", "综艺名场面", "影视资讯速递", "红毯直击", "娱乐热点锐评", "追剧日常"],
    "digital": ["虚拟主播杂谈", "VTB 直播高光", "AI 工具体验", "数字生活改造", "虚拟偶像活动", "直播文化观察"],
    "campus": ["校园日常", "学习打卡", "宿舍好物", "社团活动", "备考经验", "毕业季记录"],
}

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
        {"key": "dance", "label": "舞蹈区", "desc": "宅舞、翻跳、原创编舞", "emoji": "💃"},
        {"key": "otaku", "label": "二次元", "desc": "手办、谷子、漫展", "emoji": "🎀"},
        {"key": "danmu", "label": "鬼畜区", "desc": "鬼畜调音、二创、混剪", "emoji": "🌀"},
        {"key": "funny", "label": "搞笑区", "desc": "整活、短剧、沙雕日常", "emoji": "🤣"},
        {"key": "vlog_ent", "label": "娱乐区", "desc": "明星、综艺、影视资讯", "emoji": "🌟"},
        {"key": "digital", "label": "虚拟主播", "desc": "VTB、AI、直播文化", "emoji": "🦊"},
        {"key": "campus", "label": "校园学习", "desc": "校园日常、备考、社团", "emoji": "🎒"},
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
    "zone_content_styles": _ZONE_CONTENT_STYLES,
    "common_content_styles": _COMMON_STYLES,
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
        {"key": "vote", "label": "投票审判", "desc": "把争议扔给评论区站队，下期公布结果"},
        {"key": "roast", "label": "欢迎来怼", "desc": "鼓励观众找茬挑错，错了发道歉小作文"},
        {"key": "story", "label": "故事征集", "desc": "让观众讲自己的经历，精选下期念出来"},
        {"key": "meme", "label": "梗图运营", "desc": "评论区玩梗接龙，名场面做成表情包"},
        {"key": "lurk", "label": "潜水党之光", "desc": "定期翻牌不常发言的粉丝，暖心挂人"},
    ],
}


def zone_content_styles(zone_label: str) -> list[str]:
    """该分区的专属风格 + 通用风格，未匹配分区时返回全部通用风格。"""
    key = next((z["key"] for z in PERSONA_OPTIONS["zones"] if z["label"] == zone_label), "")
    specific = _ZONE_CONTENT_STYLES.get(key, [])
    return specific + _COMMON_STYLES


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


def _persona_hard_constraints(persona) -> list[str]:
    """Skill 已包含人设细节，这里只保留不可被 Skill 覆盖的硬约束。"""
    lines = [f"UP 主名称：{persona.name}"]
    zone = (getattr(persona, "zone", "") or "").strip()
    if zone:
        lines.append(f"所在分区：{zone}")
    taboos = (persona.taboos or "").strip()
    if taboos:
        lines.append(f"禁忌（绝不可违反）：{taboos}")
    comment = (getattr(persona, "comment_style", "") or "").strip()
    if comment:
        lines.append(f"评论互动习惯：{comment}")
    return lines


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
            + "\n".join(_persona_hard_constraints(persona))
            + "\n请严格按照专属 Skill 的定位、钩子公式、语言规则、脚本结构和红线来执行任务。"
        )
    return (
        f"{base}\n"
        + "\n".join(_persona_fact_lines(persona))
        + "\n请始终严格按该人设的分区调性、更新节奏和评论互动习惯来生成："
        "选题必须落在其分区内且贴合其内容风格；标题和口播用其受众爱看的方式写；"
        "脚本里预埋符合其评论风格的互动；与分区无关的内容宁可标注不合适，不要硬套。"
    )

import ipaddress
import json
import logging
import secrets
import threading
import time
from collections import defaultdict, deque
from collections.abc import Generator
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Literal

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password
from app.models import (
    CalendarEvent,
    IdeaSession,
    Inspiration,
    Persona,
    Script,
    Topic,
    User,
    UserSettings,
)
from app.services.skill_presets import build_preset_skill_from_template

logger = logging.getLogger("bstar.errors")

TrialAccountKey = Literal["tech", "anime", "pet"]

_RESET_LOCK = threading.Lock()
_LIMIT_LOCK = threading.Lock()
_LOGIN_ATTEMPTS: dict[str, deque[float]] = defaultdict(deque)
_GENERATION_ATTEMPTS: dict[str, deque[float]] = defaultdict(deque)
_GENERATION_SLOTS = threading.BoundedSemaphore(max(settings.trial_generation_max_concurrency, 1))
_SWEEP_INTERVAL = 60.0
_LAST_SWEEP = time.monotonic()


def normalize_username(value: str) -> str:
    """把用户名规范化为用于比较的形式，与 MySQL 大小写不敏感唯一索引保持一致。"""
    return (value or "").strip().casefold()


def _configured_username(key: str) -> str:
    if key == "tech":
        return settings.trial_username
    if key == "anime":
        return settings.trial_anime_username
    if key == "pet":
        return settings.trial_pet_username
    raise ValueError(f"未知试用账号: {key}")


def is_reserved_trial_username(username: str) -> bool:
    """判断是否为任何已配置试用账号的保留用户名（含大小写变体）。"""
    normalized = normalize_username(username)
    return any(normalize_username(_configured_username(k)) == normalized for k in ("tech", "anime", "pet"))


def is_trial_user(user: User) -> bool:
    return is_reserved_trial_username(user.username)


@dataclass(frozen=True)
class TrialAccountSpec:
    key: TrialAccountKey
    username: str
    emoji: str
    display_name: str
    summary: str
    persona: dict
    skill_template: str
    inspiration_raw: str
    topics: list[dict]
    vague_idea: str
    ideas: list[dict]
    script: dict
    covers: list[dict]
    risks: list[dict]
    calendar: list[tuple[int, str, str, str, str]]


_TRIAL_BASELINES: dict[str, dict] = {
    "tech": {
        "emoji": "📱",
        "display_name": "科技数码",
        "summary": "测评对比，结论先行",
        "persona": {
            "template_key": "trial-tech-verdict",
            "name": "数码省钱实验室",
            "style_desc": "结论先行的实测型数码编导：统一测试条件，用数据帮普通人少花冤枉钱。",
            "audience": "预算有限、下单前想看真实对比的学生与年轻上班族",
            "video_format": "B 站 6–10 分钟横屏测评，口播结论 + 实拍对比 + 数据图表",
            "taboos": "虚构参数、隐藏赞助、未实测云测评、只讲优点、制造消费焦虑",
            "sample_tone": "先给结论和适用人群，再公开测试条件，最后用价格与体验给购买建议。",
            "zone": "科技区",
            "content_style": "测评对比",
            "update_freq": "一周 1 更",
            "comment_style": "理性答疑，置顶补充测试条件，把高频问题做成下期复测",
        },
        "skill_template": "tech-verdict",
        "inspiration_raw": (
            "开学季宿舍桌面升级讨论升温：很多学生预算只有 500 元，却在显示器灯、扩展坞、键盘和支架之间反复纠结。"
            "评论区最关心的不是参数堆料，而是有限预算先买什么、哪些平替真的能用，以及升级前后效率差多少。"
        ),
        "topics": [
            {
                "link_inspiration": True,
                "title": "实测500元宿舍桌面升级",
                "highlights": ["同一预算三种分配方案", "升级前后计时对比", "找出最不值的桌搭单品", "给出可抄作业清单"],
                "feasibility": "quick",
                "cost_note": "借用三套设备，补购约500元",
                "why": "预算明确、痛点普遍，结果可量化，适合做成开学季搜索长尾。",
                "source": "extract",
                "status": "ready",
                "priority": "high",
                "tags": ["数码测评", "学生党", "省钱", "桌搭"],
            },
            {
                "link_inspiration": True,
                "title": "对比百元扩展坞隐藏成本",
                "highlights": ["连续满载温度实测", "接口缩水逐项核对", "算清退换货时间成本"],
                "feasibility": "quick",
                "cost_note": "购买三款后保留表现最好的一款",
                "why": "同价产品差异隐蔽，真实压力测试能直接帮助观众避坑。",
                "source": "extract",
                "status": "inbox",
                "priority": "mid",
                "tags": ["扩展坞", "避坑", "实测"],
            },
            {
                "link_inspiration": False,
                "title": "追踪新款轻薄本续航真相",
                "highlights": ["统一亮度循环测试", "插电与离电性能差距", "一周通勤真实记录"],
                "feasibility": "deferred",
                "cost_note": "需借到三台新品并连续测试一周",
                "why": "搜索需求强，但样机和长周期测试门槛较高，先排入待办。",
                "source": "manual",
                "status": "paused",
                "priority": "low",
                "tags": ["笔记本", "续航", "长期测试"],
            },
        ],
        "vague_idea": "500 元预算，怎么把宿舍桌面升级得真正好用？",
        "ideas": [
            {
                "title": "500元怎么花最值",
                "angle": "把预算分别押在效率、舒适和氛围三条路线，实测哪套提升最大",
                "audience": "刚入学、桌面设备从零开始配的学生",
                "cost": "500元实购，单宿舍场景一天拍完",
                "hook": "先说结论：500元最不该先买的，恰好是桌搭视频里最显眼的那个",
                "why_different": "不是单品测评，而是有限预算的分配实验",
            },
            {
                "title": "旧桌面抢救挑战",
                "angle": "先记录真实低效操作，再每加一件设备复测一次完成任务的时间",
                "audience": "设备已经不少、但桌面仍难用的宿舍党",
                "cost": "可借设备，重点成本是布置与重复计时",
                "hook": "这张桌子看着装备齐全，交一份作业却白白多花了18分钟",
                "why_different": "用任务计时替代主观好不好用",
            },
            {
                "title": "网红桌搭反向清单",
                "angle": "拆解五件高出镜率单品，按占地、频率和替代成本做去留审判",
                "audience": "容易被种草、又怕宿舍空间浪费的人",
                "cost": "需借齐五件热门产品，拍摄约两天",
                "hook": "桌搭博主都在买的五样东西，我劝你至少省下其中三笔钱",
                "why_different": "从加购转为减法，冲突感更强",
            },
        ],
        "script": {
            "outline": "500元预算挑战 → 统一任务测试 → 三套分配路线 → 数据结论 → 分档购买清单",
            "shot_list": "升级前桌面、500元预算板、三套设备、计时器、温度计、数据图表、升级后全景",
            "comments_text": "- 预算只有300元该怎么减？\n- 扩展坞长时间传文件会不会掉速？\n- 已有键盘的人先买什么？",
            "body": {
                "title": "500元宿舍桌面升级：钱到底该花在哪",
                "hook": "先说结论：预算只有500元，最先买氛围灯，可能是整套桌搭里回报最低的一笔。",
                "duration_hint": "约8分钟",
                "shots": [
                    {"time_range": "0:00-0:15", "camera": "正面近景+升级前桌面", "action": "展示500元现金与四类设备", "line": "今天只花500元，看看效率、舒适和颜值到底谁最值得先救。", "interaction": "弹幕先押一件最值得买的"},
                    {"time_range": "0:15-0:55", "camera": "俯拍", "action": "公布测试任务与统一条件", "line": "不比玄学感受：接设备、整理资料、剪一分钟素材，每套都计时三遍。", "interaction": ""},
                    {"time_range": "0:55-2:00", "camera": "分屏对比", "action": "测试支架与键鼠路线", "line": "第一套把钱花在姿势和输入上，桌面立刻空出来，但速度提升并不平均。", "interaction": ""},
                    {"time_range": "2:00-3:15", "camera": "接口特写+温度计", "action": "测试扩展坞路线", "line": "第二套看着不出片，却少插拔四次；连续传文件后，温度和掉速也要算进去。", "interaction": "猜猜最便宜款会不会翻车"},
                    {"time_range": "3:15-4:20", "camera": "环境全景", "action": "测试灯光与收纳路线", "line": "第三套最像改造视频，但灯光只改善画面，真正省时间的是这根十几元理线带。", "interaction": ""},
                    {"time_range": "4:20-5:45", "camera": "数据图表+计时回放", "action": "汇总三轮数据", "line": "按每省一分钟花多少钱算，扩展坞第一，支架第二，氛围灯最后。", "interaction": ""},
                    {"time_range": "5:45-7:10", "camera": "手持逐件展示", "action": "给三档抄作业清单", "line": "只有200元先解决接口；300元补支架；到500元再考虑输入设备，别反过来。", "interaction": "评论区留下你的预算和设备"},
                    {"time_range": "7:10-8:00", "camera": "升级后正面中景", "action": "说明适用与不适用人群", "line": "这套适合笔记本宿舍党；已有显示器或主机的人，优先级要重排。", "interaction": "下期按最高赞桌面做复测"},
                ],
                "cta": "收藏这张预算顺序表，评论区留下你的预算，我挑最高赞配置复测。",
            },
        },
        "covers": [
            {"style": "数据对比", "prompt": "宿舍桌面左右对比，中央巨大500元，三件设备带红绿收益箭头，粉蓝科技感"},
            {"style": "避坑冲突", "prompt": "UP主手拿氛围灯摇头，扩展坞与支架高亮，标题钱别花反了，明亮宿舍"},
            {"style": "清单干货", "prompt": "200/300/500元三档桌搭俯拍，设备整齐排列，价格标签清晰，B站测评封面"},
            {"style": "实验现场", "prompt": "计时器温度计与笔记本同框，真实宿舍测试台，醒目实测二字"},
            {"style": "前后改造", "prompt": "杂乱桌面到高效桌面分屏，人物惊讶表情，500元改造结果"},
            {"style": "结论先行", "prompt": "三件桌搭产品领奖台，扩展坞第一氛围灯最后，强对比大字先买谁"},
        ],
        "risks": [
            {"level": "mid", "category": "测试代表性", "detail": "单一宿舍与设备可能不代表所有场景", "suggestion": "公开设备型号、任务和测试次数"},
            {"level": "low", "category": "价格波动", "detail": "促销会改变500元组合", "suggestion": "标注购买日期与到手价区间"},
            {"level": "high", "category": "商业披露", "detail": "借测或赞助若未说明会损害可信度", "suggestion": "片头和简介明确样品来源"},
        ],
        "calendar": [
            (7, "开学季宿舍数码避坑周", "线上 / 校园", "带500元实测清单去宿舍改造，拍升级前后任务计时", "学生数码品牌清单合作"),
            (16, "秋季轻薄本新品集中首发", "线上发布会", "不追参数复读，做三款新品适合谁/不适合谁快速判定", "新品借测"),
            (25, "双十一数码预售清单准备日", "线上", "回查历史价与常见缩水款，做先收藏别急买的反种草清单", "价格工具或电商合规合作"),
        ],
    },
    "anime": {
        "emoji": "🎀",
        "display_name": "二次元收藏",
        "summary": "吃谷避坑，开箱验货",
        "persona": {
            "template_key": "trial-otaku-hoarder",
            "name": "谷子收藏研究所",
            "style_desc": "吃谷避坑型二次元编导：开箱先验货、预算按清单，替收藏党看清周边值不值。",
            "audience": "喜欢手办谷子、担心被溢价和盗版坑的学生党与收藏党",
            "video_format": "B 站 6–10 分钟横屏开箱，口播验货 + 拆盒实拍 + 价格对比",
            "taboos": "推荐盗版山寨、引导溢价炒作、晒价诱导二手倒卖、隐藏赞助信息",
            "sample_tone": "先给出这只谷冲/观望/快跑的三级判断，再展示开箱验货过程、版本与价格依据。",
            "zone": "二次元",
            "content_style": "手办开箱、谷子吃谷",
            "update_freq": "一周 1 更",
            "comment_style": "理性答疑，置顶补充入手渠道与价格，把高频避坑问题做成下期复测",
        },
        "skill_template": "otaku-hoarder",
        "inspiration_raw": (
            "秋季新番周边预订热度上升：官店、旗舰店和代购之间的价格差、版本差和发货质量问题讨论很多。"
            "评论区最关心的不是谁家更便宜，而是哪些周边真的值得订、会不会翻车，以及二手交易怎么避坑。"
        ),
        "topics": [
            {
                "link_inspiration": True,
                "title": "实测300元吃谷预算怎么花",
                "highlights": ["官店与代购同款价差对比", "拆盒验货标准流程", "找出一件最不值的谷子", "给出可抄作业购买清单"],
                "feasibility": "quick",
                "cost_note": "购入三款后保留表现最好的一款",
                "why": "预算明确、痛点普遍，结果可量化，适合做成新番季搜索长尾。",
                "source": "extract",
                "status": "ready",
                "priority": "high",
                "tags": ["手办", "谷子", "避坑", "二次元"],
            },
            {
                "link_inspiration": True,
                "title": "对比官店与代购隐藏成本",
                "highlights": ["同款价差逐项核对", "发货与售后风险记录", "算清补款与转卖时间成本"],
                "feasibility": "quick",
                "cost_note": "下单前核对运费与关税",
                "why": "同款商品渠道差异隐蔽，真实比对能直接帮观众少花冤枉钱。",
                "source": "extract",
                "status": "inbox",
                "priority": "mid",
                "tags": ["吃谷", "渠道对比", "避坑"],
            },
            {
                "link_inspiration": False,
                "title": "追踪长期预定款价格波动真相",
                "highlights": ["新品发售前后价格走势", "二手市场供需变化", "一个月价格记录"],
                "feasibility": "deferred",
                "cost_note": "需每周记录多款商品价格",
                "why": "搜索需求强，但长周期跟踪门槛较高，先排入待办。",
                "source": "manual",
                "status": "paused",
                "priority": "low",
                "tags": ["手办", "价格", "长期记录"],
            },
        ],
        "vague_idea": "300 元预算，怎么在吃谷时买到真正值得的周边？",
        "ideas": [
            {
                "title": "300元怎么买最值",
                "angle": "把预算分别押在官店、代购和二手三条路线，实测哪条体验提升最大",
                "audience": "刚入坑、预算有限的谷子新人",
                "cost": "300元实购，单拆箱场景一天拍完",
                "hook": "先说结论：300元最不该先买的，恰好是开箱视频里最上镜的那个",
                "why_different": "不是单品开箱，而是有限预算的渠道分配实验",
            },
            {
                "title": "开箱验货挑战",
                "angle": "记录每件周边从到货到验货的标准流程，逐项核对瑕疵与正版特征",
                "audience": "担心买到瑕疵或盗版的收藏党",
                "cost": "三件不同渠道周边，重点成本是拍摄与核对",
                "hook": "同一个款，三个渠道到货，瑕疵率差得离谱",
                "why_different": "用标准化验货清单替代主观值不值",
            },
            {
                "title": "网红谷子反向清单",
                "angle": "拆解五件高热度周边，按溢价、做工和转手风险做去留审判",
                "audience": "容易被种草、怕买贵的人",
                "cost": "需借齐五件热门周边，拍摄约两天",
                "hook": "大家都在买的五样谷子，我劝你至少省下其中三笔钱",
                "why_different": "从加购转为减法，冲突感更强",
            },
        ],
        "script": {
            "outline": "300元预算挑战 → 统一验货流程 → 三套渠道路线 → 数据结论 → 分档购买清单",
            "shot_list": "定金截图、到货包裹、三件周边、验货放大镜、价差表格、二手平台、最终桌面展示",
            "comments_text": "- 预算只有100元该怎么减？\n- 官店和代购差的钱去哪了？\n- 已经买了贵款的人怎么办？",
            "body": {
                "title": "300元吃谷预算：钱到底该花在哪",
                "hook": "先说结论：预算只有300元，最先订热门大件，可能是整套吃谷计划里回报最低的一笔。",
                "duration_hint": "约8分钟",
                "shots": [
                    {"time_range": "0:00-0:15", "camera": "正面近景+未开箱周边", "action": "展示300元预算与三类渠道", "line": "今天只花300元，看看官店、代购和二手，到底谁最值得先订。", "interaction": "弹幕先押一个渠道"},
                    {"time_range": "0:15-0:55", "camera": "俯拍", "action": "公布统一验货流程", "line": "不比玄学感受：到货、拆盒、核对瑕疵和正版特征，每件都过一遍。", "interaction": ""},
                    {"time_range": "0:55-2:00", "camera": "分屏对比", "action": "测试官店渠道", "line": "第一套从官店下单，包装和售后最稳，但预售周期和溢价最明显。", "interaction": ""},
                    {"time_range": "2:00-3:15", "camera": "价差表格特写", "action": "测试代购渠道", "line": "第二套看着便宜，但运费、补款和发货时间都要算进成本。", "interaction": "猜猜哪一单最划算"},
                    {"time_range": "3:15-4:20", "camera": "环境全景", "action": "测试二手渠道", "line": "第三套最考验眼光，验货做不好翻车概率最高，但捡漏也最香。", "interaction": ""},
                    {"time_range": "4:20-5:45", "camera": "数据图表+回放", "action": "汇总三轮数据", "line": "按每省十块钱花多少精力算，官店第一，二手第二，代购最后。", "interaction": ""},
                    {"time_range": "5:45-7:10", "camera": "手持逐件展示", "action": "给三档抄作业清单", "line": "只有100元先选小件周边；300元可以冲一件大件；再往上就要考虑转卖风险。", "interaction": "评论区留下你的预算和入坑方向"},
                    {"time_range": "7:10-8:00", "camera": "补拍桌面展示", "action": "说明适用与不适用人群", "line": "这套适合刚入坑的学生党；收藏老手和只收绝版的，优先级要重排。", "interaction": "下期按最高赞谷子做复测"},
                ],
                "cta": "收藏这张渠道顺序表，评论区留下你的预算，我挑最高赞配置复测。",
            },
        },
        "covers": [
            {"style": "数据对比", "prompt": "官店代购二手三格对比，中央巨大300元，三件谷子带红绿箭头，粉蓝二次元风"},
            {"style": "避坑冲突", "prompt": "UP主手拿热门谷子摇头，瑕疵放大镜高亮，标题吃谷别踩坑，手办周边堆叠背景"},
            {"style": "清单干货", "prompt": "100/300/500元三档吃谷俯拍，周边整齐排列，价格标签清晰，B站开箱封面"},
            {"style": "开箱现场", "prompt": "剪刀与未拆快递同框，真实拆盒瞬间，醒目验货二字，柔和房间灯光"},
            {"style": "前后对比", "prompt": "空荡书桌到谷子展示墙分屏，人物惊喜表情，300元改造结果"},
            {"style": "结论先行", "prompt": "三件谷子领奖台，官店第一二手第二，强对比大字先订谁"},
        ],
        "risks": [
            {"level": "mid", "category": "样本代表性", "detail": "单次购买与个人渠道不代表所有情况", "suggestion": "公开渠道、价格和购买时间"},
            {"level": "low", "category": "价格波动", "detail": "行情和补款会改变成本组合", "suggestion": "标注购买日期与到手价区间"},
            {"level": "high", "category": "商业披露", "detail": "借测或团购未说明会损害可信度", "suggestion": "片头和简介明确样品来源"},
        ],
        "calendar": [
            (7, "秋季新番周边预订截止周", "线上商城", "做新番谷子预订避坑清单，提醒哪些值得蹲补款", "周边平台合作"),
            (16, "本地漫展开展日", "线下展馆", "用吃谷清单逛展，拍战利品与排队避坑实录", "漫展官方合作"),
            (25, "手办补款集中到货周", "线上 / 家中", "开箱验货按标准流程过一遍，做补款到货真相记录", "官店补款活动"),
        ],
    },
    "pet": {
        "emoji": "🐾",
        "display_name": "萌宠动物",
        "summary": "治愈日常，科学养宠",
        "persona": {
            "template_key": "trial-animal-healer",
            "name": "毛球生活观察局",
            "style_desc": "治愈系铲屎官：记录毛孩子日常，也讲科学饲养，萌与靠谱并存。",
            "audience": "云吸猫狗、想养和正在养宠的年轻人",
            "video_format": "B 站 6–10 分钟横屏，萌宠日常 + 科学喂养讲解 + 真实行为记录",
            "taboos": "摆拍伤害动物、推荐违规饲养、代替兽医诊断、制造弃养焦虑",
            "sample_tone": "用治愈画面讲清养宠常识，遇到医疗问题先建议咨询医生，再给行为观察建议。",
            "zone": "动物圈",
            "content_style": "宠物日常、养宠科普",
            "update_freq": "日更",
            "comment_style": "理性答疑，置顶补充动物福利边界，把高频问题做成下期复测",
        },
        "skill_template": "animal-healer",
        "inspiration_raw": (
            "领养回来的小猫适应期讨论升温：很多新晋铲屎官担心应激、乱抓和喂食问题，不知道第一周该做什么、"
            "哪些信号需要马上就医，以及怎么让猫咪舒服地适应新家。"
        ),
        "topics": [
            {
                "link_inspiration": True,
                "title": "实测七天领养适应计划",
                "highlights": ["第一天到第七天行为记录", "环境丰容清单", "找出最容易踩的应激雷区", "给出可抄作业适应表"],
                "feasibility": "quick",
                "cost_note": "基础用品约300元，重点成本是每天记录",
                "why": "痛点普遍、过程可记录，结果对新手铲屎官可直接照做。",
                "source": "extract",
                "status": "ready",
                "priority": "high",
                "tags": ["猫咪", "领养", "科普", "萌宠"],
            },
            {
                "link_inspiration": True,
                "title": "对比新手养宠常见误区",
                "highlights": ["喂食误区逐项核对", "常见行为误读演示", "算清科学照护时间成本"],
                "feasibility": "quick",
                "cost_note": "用家中现有物品演示，无需额外购买",
                "why": "误区隐蔽且影响大，真实对照能直接帮助新手避坑。",
                "source": "extract",
                "status": "inbox",
                "priority": "mid",
                "tags": ["养宠", "误区", "科普"],
            },
            {
                "link_inspiration": False,
                "title": "追踪新猫行为变化一个月",
                "highlights": ["每周行为变化记录", "饮食与体重追踪", "一个月适应总结"],
                "feasibility": "deferred",
                "cost_note": "需连续记录一个月",
                "why": "长周期行为数据有价值，但拍摄与记录门槛较高，先排入待办。",
                "source": "manual",
                "status": "paused",
                "priority": "low",
                "tags": ["猫咪", "行为", "长期记录"],
            },
        ],
        "vague_idea": "领养一只小猫，怎么让它快速适应新家又保持健康？",
        "ideas": [
            {
                "title": "七天领养适应计划",
                "angle": "按天拆解适应流程，每天只做一件关键事，记录行为变化",
                "audience": "刚领养猫、手忙脚乱的新手",
                "cost": "基础用品约300元，单场景一周拍完",
                "hook": "领养第一周别急着抱，先做对这三件事",
                "why_different": "用可执行的每日清单替代笼统的别应激",
            },
            {
                "title": "新手养宠误区大扫雷",
                "angle": "逐项演示常见误区与正确做法，标清哪些信号该就医",
                "audience": "想养宠、怕养错的年轻人",
                "cost": "用家中现有物品演示，无额外成本",
                "hook": "这五个养宠误区，九成新手都踩过",
                "why_different": "误区对照比道理更有说服力，就医边界写清楚",
            },
            {
                "title": "毛球行为观察日记",
                "angle": "连续记录行为与环境的对应关系，找出舒适区",
                "audience": "想更懂自己毛孩子的铲屎官",
                "cost": "连续一周记录，重点成本是耐心",
                "hook": "看完这个观察日记，你会更懂你的猫",
                "why_different": "用行为数据替代主观猜测",
            },
        ],
        "script": {
            "outline": "领养第七天复盘 → 每天关键动作 → 三件重要事 → 就医信号清单 → 新手可抄作业",
            "shot_list": "第一天接猫、隔离房间、猫砂盆、喂食碗、逗猫棒、行为记录表、兽医咨询电话",
            "comments_text": "- 多猫家庭怎么适应？\n- 猫咪一直躲怎么办？\n- 什么情况必须马上去医院？",
            "body": {
                "title": "领养小猫第七天：我们做对了什么",
                "hook": "先说结论：领养第一周最该做的，不是天天抱，而是先让猫咪有自己的安全角落。",
                "duration_hint": "约8分钟",
                "shots": [
                    {"time_range": "0:00-0:15", "camera": "正面近景+新到家小猫", "action": "展示七天记录与关键时间线", "line": "这只小猫到家七天，我们做对了三件事，也踩了一个雷。", "interaction": "弹幕先猜猜雷是什么"},
                    {"time_range": "0:15-0:55", "camera": "俯拍隔离房间", "action": "公布第一天布置", "line": "第一天不急着互动，先给独立房间、躲藏处和安静的空间。", "interaction": ""},
                    {"time_range": "0:55-2:00", "camera": "分屏对比", "action": "演示猫砂与饮食安排", "line": "第二件事是让吃喝拉撒全部定点，气味熟悉了，情绪才稳定。", "interaction": ""},
                    {"time_range": "2:00-3:15", "camera": "行为特写", "action": "展示互动时机", "line": "第三件事是等它主动靠近再互动，强抱反而会加重应激。", "interaction": "你家猫到家第几天敢靠近你？"},
                    {"time_range": "3:15-4:20", "camera": "环境全景", "action": "演示丰容与玩耍", "line": "用逗猫棒和纸箱做环境丰容，探索欲起来，适应就快多了。", "interaction": ""},
                    {"time_range": "4:20-5:45", "camera": "记录表特写", "action": "汇总七天行为数据", "line": "把躲藏时长、进食量和便便情况记下来，变化趋势一眼看清。", "interaction": ""},
                    {"time_range": "5:45-7:10", "camera": "手持逐项讲解", "action": "给就医信号清单", "line": "出现精神萎靡、拒食超过24小时或持续呕吐，别查攻略，先问医生。", "interaction": "评论区留下你遇到的情况"},
                    {"time_range": "7:10-8:00", "camera": "升级后家中全景", "action": "说明适用与不适用人群", "line": "这套适合单猫新家；多猫或已养宠家庭，隔离和引入方式要重排。", "interaction": "下期按最高赞问题做复测"},
                ],
                "cta": "收藏这份适应计划表，评论区留下你的问题，我挑最高赞做下期复测。",
            },
        },
        "covers": [
            {"style": "数据对比", "prompt": "七天行为记录表与小猫同框，三件关键事带勾选，粉蓝治愈风"},
            {"style": "避坑冲突", "prompt": "UP主摆手示意不要强抱，小猫躲进纸箱，标题别急着抱，明亮客厅"},
            {"style": "清单干货", "prompt": "领养第一周每日清单俯拍，猫砂盆喂食碗整齐排列，清晰步骤，B站科普封面"},
            {"style": "记录现场", "prompt": "手写记录表与小猫同框，真实领养第七天，醒目科学二字"},
            {"style": "前后对比", "prompt": "躲藏小猫到主动蹭手分屏，温馨表情，领养七天变化"},
            {"style": "结论先行", "prompt": "三件关键事领奖台，安全角落第一，强对比大字先做什么"},
        ],
        "risks": [
            {"level": "mid", "category": "个体差异", "detail": "单只猫咪的表现不代表所有品种", "suggestion": "公开猫咪年龄与性格，标注个体差异"},
            {"level": "low", "category": "记录偏差", "detail": "居家记录可能不够客观", "suggestion": "固定观察时间与记录格式"},
            {"level": "high", "category": "医疗边界", "detail": "科普不能替代兽医诊断", "suggestion": "涉及症状先引导就医，明确免责说明"},
        ],
        "calendar": [
            (7, "国际领养日公益倡导周", "线下 / 社区", "用七天适应计划做领养科普，记录志愿者探访", "宠物公益组织合作"),
            (16, "秋季宠物换季护理提醒", "线上", "做换季饮食与毛发护理清单，拍日常护理实录", "宠物用品品牌合作"),
            (25, "宠物友好空间开放日", "线下空间", "记录宠物友好空间实地体验，给带宠出行攻略", "宠物空间官方合作"),
        ],
    },
}


def get_trial_account(account_key: str) -> TrialAccountSpec:
    if account_key not in _TRIAL_BASELINES:
        raise ValueError(f"未知试用账号: {account_key}")
    base = _TRIAL_BASELINES[account_key]
    return TrialAccountSpec(
        key=account_key,  # type: ignore[arg-type]
        username=_configured_username(account_key),
        emoji=base["emoji"],
        display_name=base["display_name"],
        summary=base["summary"],
        persona=base["persona"],
        skill_template=base["skill_template"],
        inspiration_raw=base["inspiration_raw"],
        topics=base["topics"],
        vague_idea=base["vague_idea"],
        ideas=base["ideas"],
        script=base["script"],
        covers=base["covers"],
        risks=base["risks"],
        calendar=base["calendar"],
    )


def iter_trial_accounts() -> list[TrialAccountSpec]:
    return [get_trial_account(key) for key in _TRIAL_BASELINES]


def _client_ip(request: Request) -> str:
    peer = request.client.host if request.client else "unknown"
    try:
        trusted_peer = ipaddress.ip_address(peer).is_loopback or ipaddress.ip_address(peer).is_private
    except ValueError:
        trusted_peer = False
    if trusted_peer:
        forwarded = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
        if forwarded:
            return forwarded
    return peer


def _check_window(bucket: dict[str, deque[float]], key: str, *, limit: int, seconds: int) -> None:
    now = time.monotonic()
    with _LIMIT_LOCK:
        attempts = bucket[key]
        while attempts and attempts[0] <= now - seconds:
            attempts.popleft()
        if len(attempts) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="试用空间今天有点忙，请稍后再来～",
            )
        attempts.append(now)


def _sweep_buckets() -> None:
    global _LAST_SWEEP
    now = time.monotonic()
    if now - _LAST_SWEEP < _SWEEP_INTERVAL:
        return
    _LAST_SWEEP = now
    horizon = max(60, settings.trial_generation_window_seconds)
    with _LIMIT_LOCK:
        for bucket in (_LOGIN_ATTEMPTS, _GENERATION_ATTEMPTS):
            for key in list(bucket):
                deq = bucket[key]
                while deq and deq[0] <= now - horizon:
                    deq.popleft()
                if not deq:
                    bucket.pop(key, None)


def limit_trial_login(request: Request) -> None:
    _sweep_buckets()
    if not settings.trial_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="试用空间暂未开放")
    _check_window(
        _LOGIN_ATTEMPTS,
        _client_ip(request),
        limit=max(settings.trial_login_requests_per_minute, 1),
        seconds=60,
    )


def acquire_trial_generation_slot(request: Request, user: User) -> bool:
    if not is_trial_user(user):
        return False
    _sweep_buckets()
    _check_window(
        _GENERATION_ATTEMPTS,
        _client_ip(request),
        limit=max(settings.trial_generation_requests_per_window, 1),
        seconds=max(settings.trial_generation_window_seconds, 1),
    )
    if not _GENERATION_SLOTS.acquire(blocking=False):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="试用空间的编导娘都在忙，请稍后再试～",
        )
    return True


def release_trial_generation_slot(acquired: bool) -> None:
    if acquired:
        _GENERATION_SLOTS.release()


def trial_generation_slot(
    request: Request,
    user: User = Depends(get_current_user),
) -> Generator[None, None, None]:
    acquired = acquire_trial_generation_slot(request, user)
    try:
        yield
    finally:
        release_trial_generation_slot(acquired)


def _dump(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _build_persona(user_id: int, spec: TrialAccountSpec, now: datetime) -> Persona:
    persona = Persona(user_id=user_id, created_at=now, **spec.persona)
    skill = build_preset_skill_from_template(persona, spec.skill_template)
    if skill is None:
        raise RuntimeError(f"试用 Skill 模板不存在: {spec.skill_template}")
    persona.skill_prompt = skill["system_prompt"]
    persona.skill_brief_json = _dump(skill)
    persona.skill_generated_at = now
    return persona


def _seed_baseline(db: Session, user: User, spec: TrialAccountSpec) -> None:
    now = datetime.now(timezone.utc)
    today = date.today()
    user.active_persona_id = None
    user.password_hash = hash_password(secrets.token_urlsafe(32))
    db.flush()

    for model in (Script, IdeaSession, Topic, Inspiration, CalendarEvent, Persona, UserSettings):
        db.query(model).filter(model.user_id == user.id).delete(synchronize_session=False)

    db.add(
        UserSettings(
            user_id=user.id,
            llm_base_url=settings.default_llm_base_url,
            llm_model=settings.default_llm_model,
            llm_api_key="",
            updated_at=now,
        )
    )
    persona = _build_persona(user.id, spec, now)
    db.add(persona)
    db.flush()

    inspiration = Inspiration(
        user_id=user.id,
        raw_text=spec.inspiration_raw,
        source_note="试用空间 · 示例灵感",
        created_at=now,
    )
    db.add(inspiration)
    db.flush()

    topics: list[Topic] = []
    for t in spec.topics:
        topics.append(
            Topic(
                user_id=user.id,
                inspiration_id=inspiration.id if t.get("link_inspiration", True) else None,
                title=t["title"],
                highlights=_dump(t["highlights"]),
                feasibility=t["feasibility"],
                cost_note=t["cost_note"],
                why=t["why"],
                source=t["source"],
                status=t["status"],
                priority=t["priority"],
                tags=_dump(t["tags"]),
                created_at=now,
            )
        )
    db.add_all(topics)
    db.flush()
    primary = topics[0]

    idea_session = IdeaSession(
        user_id=user.id,
        topic_id=primary.id,
        vague_idea=spec.vague_idea,
        ideas_json=_dump(spec.ideas),
        selected_index=0,
        saved_json="[0]",
        created_at=now,
    )
    db.add(idea_session)
    db.flush()

    db.add(
        Script(
            user_id=user.id,
            topic_id=primary.id,
            idea_session_id=idea_session.id,
            outline=spec.script["outline"],
            shot_list=spec.script["shot_list"],
            comments_text=spec.script["comments_text"],
            script_json=_dump(spec.script["body"]),
            cover_prompts_json=_dump(spec.covers),
            risks_json=_dump(spec.risks),
            created_at=now,
        )
    )

    for offset, title, location, vlog_fit, commercial in spec.calendar:
        day = (today + timedelta(days=offset)).isoformat()
        db.add(
            CalendarEvent(
                user_id=user.id,
                title=title,
                start_date=day,
                end_date=day,
                location=location,
                vlog_fit=vlog_fit,
                commercial=commercial,
                raw_text="试用空间按人设预置",
                source="capture",
                created_at=now,
            )
        )

    user.active_persona_id = persona.id


def _acquire_database_lock(engine: Engine, account_key: str) -> tuple[object | None, bool]:
    """MySQL 使用连接级命名锁；SQLite 单进程依赖线程锁即可。"""
    if engine.dialect.name != "mysql":
        return None, True
    conn = engine.connect()
    try:
        got = bool(conn.execute(text(f"SELECT GET_LOCK('ideaweave:trial-reset:{account_key}', 2)")).scalar())
        if not got:
            conn.close()
            return None, False
        return conn, True
    except Exception:
        conn.close()
        raise


def _release_database_lock(conn: object, account_key: str) -> None:
    try:
        conn.execute(text(f"SELECT RELEASE_LOCK('ideaweave:trial-reset:{account_key}')"))
    finally:
        conn.close()


def reset_trial_account(account_key: str = "tech") -> User | None:
    account = get_trial_account(account_key)
    with _RESET_LOCK:
        lock_conn = None
        acquired = False
        db = SessionLocal()
        try:
            lock_conn, acquired = _acquire_database_lock(engine, account.key)
            if not acquired:
                return None
            user = db.query(User).filter(User.username == account.username).one_or_none()
            if user is None:
                user = User(
                    username=account.username,
                    password_hash=hash_password(secrets.token_urlsafe(32)),
                    created_at=datetime.now(timezone.utc),
                )
                db.add(user)
                db.flush()
            _seed_baseline(db, user, account)
            db.commit()
            db.refresh(user)
            return user
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
            if lock_conn is not None:
                try:
                    _release_database_lock(lock_conn, account.key)
                except Exception:
                    logger.exception("释放试用重置锁失败")


def reset_all_trial_accounts() -> dict[str, User | None]:
    results: dict[str, User | None] = {}
    for account in iter_trial_accounts():
        try:
            results[account.key] = reset_trial_account(account.key)
        except Exception:
            logger.exception("试用空间 %s 初始化失败，服务继续", account.key)
            results[account.key] = None
    return results


def _is_initialized(db: Session, user: User) -> bool:
    if not user.active_persona_id:
        return False
    persona = db.get(Persona, user.active_persona_id)
    has_settings = db.query(UserSettings.id).filter(UserSettings.user_id == user.id).first()
    return bool(persona and persona.user_id == user.id and persona.skill_prompt and has_settings)


def trial_login(db: Session, account_key: str = "tech") -> tuple[User, str]:
    if not settings.trial_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="试用空间暂未开放")
    try:
        account = get_trial_account(account_key)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的试用账号")
    user = db.query(User).filter(User.username == account.username).one_or_none()
    if user is not None and _is_initialized(db, user):
        return user, create_access_token(user.id, user.username, expire_minutes=settings.trial_jwt_expire_minutes)
    db.rollback()
    try:
        reset_trial_account(account.key)
    except Exception:
        db.rollback()
        logger.exception("初始化试用账号 %s 失败", account.key)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="体验空间正在初始化，请稍后重试")
    db.expire_all()
    user = db.query(User).filter(User.username == account.username).one_or_none()
    if user is None or not _is_initialized(db, user):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="体验空间正在初始化，请稍后重试")
    return user, create_access_token(user.id, user.username, expire_minutes=settings.trial_jwt_expire_minutes)

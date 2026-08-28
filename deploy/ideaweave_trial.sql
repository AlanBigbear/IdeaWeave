-- IdeaWeave public trial workspace baseline (MySQL 8, DML only)
-- Prerequisite: import deploy/ideaweave_schema.sql first.
-- WARNING: `demo` / `demo-anime` / `demo-pet` are reserved disposable accounts.
--          This script replaces only data owned by those three usernames, one block each.
--          Importing twice restores the same logical baseline; user IDs stay stable.
-- No provider key or plaintext password is stored here.

SET NAMES utf8mb4;
START TRANSACTION;

-- ============================================================================
-- Block 1/3 · tech（科技数码 · 数码省钱实验室）
-- ============================================================================

INSERT INTO `users` (`username`, `password_hash`, `active_persona_id`, `created_at`)
VALUES ('demo', '$2b$12$3NBSraxa/Li1jLqTheNvruIFNN3gEE.bTKUWWZeTIkY1KMElsIJOu', NULL, UTC_TIMESTAMP())
ON DUPLICATE KEY UPDATE `id` = LAST_INSERT_ID(`id`), `active_persona_id` = NULL;
SET @trial_tech_user_id = LAST_INSERT_ID();

DELETE FROM `scripts` WHERE `user_id` = @trial_tech_user_id;
DELETE FROM `idea_sessions` WHERE `user_id` = @trial_tech_user_id;
DELETE FROM `topics` WHERE `user_id` = @trial_tech_user_id;
DELETE FROM `inspirations` WHERE `user_id` = @trial_tech_user_id;
DELETE FROM `calendar_events` WHERE `user_id` = @trial_tech_user_id;
DELETE FROM `personas` WHERE `user_id` = @trial_tech_user_id;
DELETE FROM `user_settings` WHERE `user_id` = @trial_tech_user_id;

INSERT INTO `user_settings` (`user_id`, `llm_base_url`, `llm_model`, `llm_api_key`, `updated_at`)
VALUES (@trial_tech_user_id, 'https://api.deepseek.com/v1', 'deepseek-v4-pro', '', UTC_TIMESTAMP());

SET @skill_brief = JSON_OBJECT(
  'positioning', '用实测数据替观众做消费决策，给下单前犹豫的人看，靠「结论先行+条件标注」被记住',
  'hook_formula', JSON_ARRAY(
    '先说结论：这台闭眼入 / 千万别买——三个理由，测完再骂也来得及',
    '同样预算，A和B到底谁更值？先把测试条件摆桌上',
    '参数看着很美，但真实使用最容易翻车的是这一项'
  ),
  'tone_rules', JSON_ARRAY('结尾固定「适合谁 / 不适合谁」两行清单', '结论先行再给证据', '所有数据标注测试条件', '不制造消费焦虑'),
  'topic_preferences', JSON_ARRAY('优先做同价对比与长期实测', '追踪学生党和通勤党真实痛点', '不做未上手的云测评', '一周1更，优先可复现测试'),
  'script_structure', '0-15秒先给结论；中段公开条件、逐项实测、展示反例；结尾列适合谁/不适合谁和购买时机',
  'interaction_style', '口播先让观众押结果；置顶补充测试条件；高频质疑进入下期复测',
  'red_lines', JSON_ARRAY('不编造参数', '不隐藏赞助', '不做云测评', '不只讲优点'),
  'system_prompt', '你是为 UP 主「数码省钱实验室」工作的虚拟编导。频道用统一条件下的真实测试，替预算有限、下单前犹豫的学生与年轻上班族做消费决策。所有内容先给明确结论和适用人群，再公开设备版本、环境、价格、样本与测试次数，用可复现数据解释原因。选题优先同价横评、长期体验、缩水避坑和有限预算分配，不追没有样机的参数新闻，不制造消费焦虑。脚本开头十五秒必须抛出闭眼入或千万别买的判断；中段安排实拍、计时、温度或任务对比，并主动展示反例；结尾固定列出适合谁、不适合谁与购买时机。口播短句、具体、有条件，不用绝对化广告词。评论区先让观众押结果，置顶补充测试条件，把高频质疑做成下期复测。严禁虚构参数、未实测云测评、隐藏借测或赞助、只讲优点。'
);

INSERT INTO `personas` (
  `user_id`, `template_key`, `name`, `style_desc`, `audience`, `video_format`, `taboos`, `sample_tone`,
  `zone`, `content_style`, `update_freq`, `comment_style`, `skill_prompt`, `skill_brief_json`, `skill_generated_at`, `created_at`
) VALUES (
  @trial_tech_user_id, 'trial-tech-verdict', '数码省钱实验室',
  '结论先行的实测型数码编导：统一测试条件，用数据帮普通人少花冤枉钱。',
  '预算有限、下单前想看真实对比的学生与年轻上班族',
  'B 站 6–10 分钟横屏测评，口播结论 + 实拍对比 + 数据图表',
  '虚构参数、隐藏赞助、未实测云测评、只讲优点、制造消费焦虑',
  '先给结论和适用人群，再公开测试条件，最后用价格与体验给购买建议。',
  '科技区', '测评对比', '一周 1 更', '理性答疑，置顶补充测试条件，把高频问题做成下期复测',
  JSON_UNQUOTE(JSON_EXTRACT(@skill_brief, '$.system_prompt')), CAST(@skill_brief AS CHAR), UTC_TIMESTAMP(), UTC_TIMESTAMP()
);
SET @trial_tech_persona_id = LAST_INSERT_ID();

INSERT INTO `inspirations` (`user_id`, `raw_text`, `source_note`, `created_at`)
VALUES (
  @trial_tech_user_id,
  '开学季宿舍桌面升级讨论升温：很多学生预算只有500元，却在显示器灯、扩展坞、键盘和支架之间反复纠结。评论区最关心的不是参数堆料，而是有限预算先买什么、哪些平替真的能用，以及升级前后效率差多少。',
  '试用空间 · 示例灵感', UTC_TIMESTAMP()
);
SET @trial_tech_inspiration_id = LAST_INSERT_ID();

INSERT INTO `topics` (`user_id`, `inspiration_id`, `title`, `highlights`, `feasibility`, `cost_note`, `why`, `source`, `status`, `priority`, `tags`, `created_at`)
VALUES (
  @trial_tech_user_id, @trial_tech_inspiration_id, '实测500元宿舍桌面升级',
  JSON_ARRAY('同一预算三种分配方案', '升级前后计时对比', '找出最不值的桌搭单品', '给出可抄作业清单'),
  'quick', '借用三套设备，补购约500元', '预算明确、痛点普遍，结果可量化，适合做成开学季搜索长尾。',
  'extract', 'ready', 'high', JSON_ARRAY('数码测评', '学生党', '省钱', '桌搭'), UTC_TIMESTAMP()
);
SET @trial_tech_topic_id = LAST_INSERT_ID();

INSERT INTO `topics` (`user_id`, `inspiration_id`, `title`, `highlights`, `feasibility`, `cost_note`, `why`, `source`, `status`, `priority`, `tags`, `created_at`)
VALUES
(@trial_tech_user_id, @trial_tech_inspiration_id, '对比百元扩展坞隐藏成本', JSON_ARRAY('连续满载温度实测', '接口缩水逐项核对', '算清退换货时间成本'), 'quick', '购买三款后保留表现最好的一款', '同价产品差异隐蔽，真实压力测试能直接帮助观众避坑。', 'extract', 'inbox', 'mid', JSON_ARRAY('扩展坞', '避坑', '实测'), UTC_TIMESTAMP()),
(@trial_tech_user_id, NULL, '追踪新款轻薄本续航真相', JSON_ARRAY('统一亮度循环测试', '插电与离电性能差距', '一周通勤真实记录'), 'deferred', '需借到三台新品并连续测试一周', '搜索需求强，但样机和长周期测试门槛较高，先排入待办。', 'manual', 'paused', 'low', JSON_ARRAY('笔记本', '续航', '长期测试'), UTC_TIMESTAMP());

SET @ideas = JSON_ARRAY(
  JSON_OBJECT('title','500元怎么花最值','angle','把预算分别押在效率、舒适和氛围三条路线，实测哪套提升最大','audience','刚入学、桌面设备从零开始配的学生','cost','500元实购，单宿舍场景一天拍完','hook','先说结论：500元最不该先买的，恰好是桌搭视频里最显眼的那个','why_different','不是单品测评，而是有限预算的分配实验'),
  JSON_OBJECT('title','旧桌面抢救挑战','angle','先记录真实低效操作，再每加一件设备复测一次完成任务的时间','audience','设备已经不少、但桌面仍难用的宿舍党','cost','可借设备，重点成本是布置与重复计时','hook','这张桌子看着装备齐全，交一份作业却白白多花了18分钟','why_different','用任务计时替代主观好不好用'),
  JSON_OBJECT('title','网红桌搭反向清单','angle','拆解五件高出镜率单品，按占地、频率和替代成本做去留审判','audience','容易被种草、又怕宿舍空间浪费的人','cost','需借齐五件热门产品，拍摄约两天','hook','桌搭博主都在买的五样东西，我劝你至少省下其中三笔钱','why_different','从加购转为减法，冲突感更强')
);
INSERT INTO `idea_sessions` (`user_id`, `topic_id`, `vague_idea`, `ideas_json`, `selected_index`, `saved_json`, `created_at`)
VALUES (@trial_tech_user_id, @trial_tech_topic_id, '500 元预算，怎么把宿舍桌面升级得真正好用？', CAST(@ideas AS CHAR), 0, '[0]', UTC_TIMESTAMP());
SET @trial_tech_idea_id = LAST_INSERT_ID();

SET @script = JSON_OBJECT(
  'title','500元宿舍桌面升级：钱到底该花在哪',
  'hook','先说结论：预算只有500元，最先买氛围灯，可能是整套桌搭里回报最低的一笔。',
  'duration_hint','约8分钟',
  'shots',JSON_ARRAY(
    JSON_OBJECT('time_range','0:00-0:15','camera','正面近景+升级前桌面','action','展示500元现金与四类设备','line','今天只花500元，看看效率、舒适和颜值到底谁最值得先救。','interaction','弹幕先押一件最值得买的'),
    JSON_OBJECT('time_range','0:15-0:55','camera','俯拍','action','公布测试任务与统一条件','line','不比玄学感受：接设备、整理资料、剪一分钟素材，每套都计时三遍。','interaction',''),
    JSON_OBJECT('time_range','0:55-2:00','camera','分屏对比','action','测试支架与键鼠路线','line','第一套把钱花在姿势和输入上，桌面立刻空出来，但速度提升并不平均。','interaction',''),
    JSON_OBJECT('time_range','2:00-3:15','camera','接口特写+温度计','action','测试扩展坞路线','line','第二套看着不出片，却少插拔四次；连续传文件后，温度和掉速也要算进去。','interaction','猜猜最便宜款会不会翻车'),
    JSON_OBJECT('time_range','3:15-4:20','camera','环境全景','action','测试灯光与收纳路线','line','第三套最像改造视频，但灯光只改善画面，真正省时间的是这根十几元理线带。','interaction',''),
    JSON_OBJECT('time_range','4:20-5:45','camera','数据图表+计时回放','action','汇总三轮数据','line','按每省一分钟花多少钱算，扩展坞第一，支架第二，氛围灯最后。','interaction',''),
    JSON_OBJECT('time_range','5:45-7:10','camera','手持逐件展示','action','给三档抄作业清单','line','只有200元先解决接口；300元补支架；到500元再考虑输入设备，别反过来。','interaction','评论区留下你的预算和设备'),
    JSON_OBJECT('time_range','7:10-8:00','camera','升级后正面中景','action','说明适用与不适用人群','line','这套适合笔记本宿舍党；已有显示器或主机的人，优先级要重排。','interaction','下期按最高赞桌面做复测')
  ),
  'cta','收藏这张预算顺序表，评论区留下你的预算，我挑最高赞配置复测。'
);
SET @covers = JSON_ARRAY(
  JSON_OBJECT('style','数据对比','prompt','宿舍桌面左右对比，中央巨大500元，三件设备带红绿收益箭头，粉蓝科技感'),
  JSON_OBJECT('style','避坑冲突','prompt','UP主手拿氛围灯摇头，扩展坞与支架高亮，标题钱别花反了，明亮宿舍'),
  JSON_OBJECT('style','清单干货','prompt','200/300/500元三档桌搭俯拍，设备整齐排列，价格标签清晰，B站测评封面'),
  JSON_OBJECT('style','实验现场','prompt','计时器温度计与笔记本同框，真实宿舍测试台，醒目实测二字'),
  JSON_OBJECT('style','前后改造','prompt','杂乱桌面到高效桌面分屏，人物惊讶表情，500元改造结果'),
  JSON_OBJECT('style','结论先行','prompt','三件桌搭产品领奖台，扩展坞第一氛围灯最后，强对比大字先买谁')
);
SET @risks = JSON_ARRAY(
  JSON_OBJECT('level','mid','category','测试代表性','detail','单一宿舍与设备可能不代表所有场景','suggestion','公开设备型号、任务和测试次数'),
  JSON_OBJECT('level','low','category','价格波动','detail','促销会改变500元组合','suggestion','标注购买日期与到手价区间'),
  JSON_OBJECT('level','high','category','商业披露','detail','借测或赞助若未说明会损害可信度','suggestion','片头和简介明确样品来源')
);
INSERT INTO `scripts` (`user_id`, `topic_id`, `idea_session_id`, `outline`, `shot_list`, `comments_text`, `script_json`, `cover_prompts_json`, `risks_json`, `created_at`)
VALUES (@trial_tech_user_id, @trial_tech_topic_id, @trial_tech_idea_id, '500元预算挑战 → 统一任务测试 → 三套分配路线 → 数据结论 → 分档购买清单', '升级前桌面、500元预算板、三套设备、计时器、温度计、数据图表、升级后全景', '- 预算只有300元该怎么减？\n- 扩展坞长时间传文件会不会掉速？\n- 已有键盘的人先买什么？', CAST(@script AS CHAR), CAST(@covers AS CHAR), CAST(@risks AS CHAR), UTC_TIMESTAMP());

INSERT INTO `calendar_events` (`user_id`, `title`, `start_date`, `end_date`, `location`, `vlog_fit`, `commercial`, `raw_text`, `source`, `created_at`)
VALUES
(@trial_tech_user_id, '开学季宿舍数码避坑周', DATE_FORMAT(DATE_ADD(UTC_DATE(), INTERVAL 7 DAY), '%Y-%m-%d'), DATE_FORMAT(DATE_ADD(UTC_DATE(), INTERVAL 7 DAY), '%Y-%m-%d'), '线上 / 校园', '带500元实测清单去宿舍改造，拍升级前后任务计时', '学生数码品牌清单合作', '试用空间按人设预置', 'capture', UTC_TIMESTAMP()),
(@trial_tech_user_id, '秋季轻薄本新品集中首发', DATE_FORMAT(DATE_ADD(UTC_DATE(), INTERVAL 16 DAY), '%Y-%m-%d'), DATE_FORMAT(DATE_ADD(UTC_DATE(), INTERVAL 16 DAY), '%Y-%m-%d'), '线上发布会', '不追参数复读，做三款新品适合谁/不适合谁快速判定', '新品借测', '试用空间按人设预置', 'capture', UTC_TIMESTAMP()),
(@trial_tech_user_id, '双十一数码预售清单准备日', DATE_FORMAT(DATE_ADD(UTC_DATE(), INTERVAL 25 DAY), '%Y-%m-%d'), DATE_FORMAT(DATE_ADD(UTC_DATE(), INTERVAL 25 DAY), '%Y-%m-%d'), '线上', '回查历史价与常见缩水款，做先收藏别急买的反种草清单', '价格工具或电商合规合作', '试用空间按人设预置', 'capture', UTC_TIMESTAMP());

UPDATE `users` SET `active_persona_id` = @trial_tech_persona_id WHERE `id` = @trial_tech_user_id;

-- ============================================================================
-- Block 2/3 · anime（二次元收藏 · 谷子收藏研究所）
-- ============================================================================

INSERT INTO `users` (`username`, `password_hash`, `active_persona_id`, `created_at`)
VALUES ('demo-anime', '$2b$12$3NBSraxa/Li1jLqTheNvruIFNN3gEE.bTKUWWZeTIkY1KMElsIJOu', NULL, UTC_TIMESTAMP())
ON DUPLICATE KEY UPDATE `id` = LAST_INSERT_ID(`id`), `active_persona_id` = NULL;
SET @trial_anime_user_id = LAST_INSERT_ID();

DELETE FROM `scripts` WHERE `user_id` = @trial_anime_user_id;
DELETE FROM `idea_sessions` WHERE `user_id` = @trial_anime_user_id;
DELETE FROM `topics` WHERE `user_id` = @trial_anime_user_id;
DELETE FROM `inspirations` WHERE `user_id` = @trial_anime_user_id;
DELETE FROM `calendar_events` WHERE `user_id` = @trial_anime_user_id;
DELETE FROM `personas` WHERE `user_id` = @trial_anime_user_id;
DELETE FROM `user_settings` WHERE `user_id` = @trial_anime_user_id;

INSERT INTO `user_settings` (`user_id`, `llm_base_url`, `llm_model`, `llm_api_key`, `updated_at`)
VALUES (@trial_anime_user_id, 'https://api.deepseek.com/v1', 'deepseek-v4-pro', '', UTC_TIMESTAMP());

SET @skill_brief = JSON_OBJECT(
  'positioning', '用正版验货和预算清单帮收藏党买得明白，给开箱前犹豫的人看，靠「三级判断+条件标注」被记住',
  'hook_formula', JSON_ARRAY(
    '先说结论：这只谷冲 / 观望 / 快跑——三个理由，拆开给你看',
    '同样的谷子，官店、代购和二手到底差多少？先把到货成本摆桌上',
    '看着很有性价比，但真实吃谷最容易翻车的是这一项'
  ),
  'tone_rules', JSON_ARRAY('结尾固定「适合谁 / 不适合谁」两行清单', '先给结论再给证据', '所有价格标注渠道与日期', '不引导溢价炒作'),
  'topic_preferences', JSON_ARRAY('优先做同款横评与渠道避坑', '追踪新番季学生党真实痛点', '不做盗版推荐与晒价诱导', '一周1更，优先可复现验货'),
  'script_structure', '0-15秒先给结论；中段公开渠道、逐项验货、展示反例；结尾列适合谁/不适合谁和入手时机',
  'interaction_style', '口播先让观众押渠道；置顶补充渠道与价格；高频质疑进入下期复测',
  'red_lines', JSON_ARRAY('不推荐盗版山寨', '不引导溢价炒作', '不晒价诱导二手倒卖', '不隐藏赞助信息'),
  'system_prompt', '你是为 UP 主「谷子收藏研究所」工作的虚拟编导。频道用标准化的开箱验货流程和预算清单，替担心买到瑕疵、盗版或买贵的二次元收藏党做消费决策。所有内容先给冲/观望/快跑三级判断，再公开渠道、价格、版本与验货过程，用可复现的细节解释原因。选题优先同款渠道横评、预算吃谷、开箱避坑和价格追踪，不做盗版推荐、不晒价诱导二手倒卖，不制造炒作氛围。脚本开头十五秒必须抛出冲或观望的判断；中段安排拆盒实拍、版本对照和价格对比，并主动展示反例；结尾固定列出适合谁、不适合谁与入手时机。口播短句、具体、有版本意识，不用绝对化广告词。评论区先让观众押渠道，置顶补充购买信息，把高频质疑做成下期复测。严禁推荐盗版山寨、引导溢价炒作、晒价诱导二手倒卖、隐藏赞助信息。'
);

INSERT INTO `personas` (
  `user_id`, `template_key`, `name`, `style_desc`, `audience`, `video_format`, `taboos`, `sample_tone`,
  `zone`, `content_style`, `update_freq`, `comment_style`, `skill_prompt`, `skill_brief_json`, `skill_generated_at`, `created_at`
) VALUES (
  @trial_anime_user_id, 'trial-otaku-hoarder', '谷子收藏研究所',
  '吃谷避坑型二次元编导：开箱先验货、预算按清单，替收藏党看清周边值不值。',
  '喜欢手办谷子、担心被溢价和盗版坑的学生党与收藏党',
  'B 站 6–10 分钟横屏开箱，口播验货 + 拆盒实拍 + 价格对比',
  '推荐盗版山寨、引导溢价炒作、晒价诱导二手倒卖、隐藏赞助信息',
  '先给出这只谷冲/观望/快跑的三级判断，再展示开箱验货过程、版本与价格依据。',
  '二次元', '手办开箱、谷子吃谷', '一周 1 更', '理性答疑，置顶补充入手渠道与价格，把高频避坑问题做成下期复测',
  JSON_UNQUOTE(JSON_EXTRACT(@skill_brief, '$.system_prompt')), CAST(@skill_brief AS CHAR), UTC_TIMESTAMP(), UTC_TIMESTAMP()
);
SET @trial_anime_persona_id = LAST_INSERT_ID();

INSERT INTO `inspirations` (`user_id`, `raw_text`, `source_note`, `created_at`)
VALUES (
  @trial_anime_user_id,
  '秋季新番周边预订热度上升：官店、旗舰店和代购之间的价格差、版本差和发货质量问题讨论很多。评论区最关心的不是谁家更便宜，而是哪些周边真的值得订、会不会翻车，以及二手交易怎么避坑。',
  '试用空间 · 示例灵感', UTC_TIMESTAMP()
);
SET @trial_anime_inspiration_id = LAST_INSERT_ID();

INSERT INTO `topics` (`user_id`, `inspiration_id`, `title`, `highlights`, `feasibility`, `cost_note`, `why`, `source`, `status`, `priority`, `tags`, `created_at`)
VALUES (
  @trial_anime_user_id, @trial_anime_inspiration_id, '实测300元吃谷预算怎么花',
  JSON_ARRAY('官店与代购同款价差对比', '拆盒验货标准流程', '找出一件最不值的谷子', '给出可抄作业购买清单'),
  'quick', '购入三款后保留表现最好的一款', '预算明确、痛点普遍，结果可量化，适合做成新番季搜索长尾。',
  'extract', 'ready', 'high', JSON_ARRAY('手办', '谷子', '避坑', '二次元'), UTC_TIMESTAMP()
);
SET @trial_anime_topic_id = LAST_INSERT_ID();

INSERT INTO `topics` (`user_id`, `inspiration_id`, `title`, `highlights`, `feasibility`, `cost_note`, `why`, `source`, `status`, `priority`, `tags`, `created_at`)
VALUES
(@trial_anime_user_id, @trial_anime_inspiration_id, '对比官店与代购隐藏成本', JSON_ARRAY('同款价差逐项核对', '发货与售后风险记录', '算清补款与转卖时间成本'), 'quick', '下单前核对运费与关税', '同款商品渠道差异隐蔽，真实比对能直接帮观众少花冤枉钱。', 'extract', 'inbox', 'mid', JSON_ARRAY('吃谷', '渠道对比', '避坑'), UTC_TIMESTAMP()),
(@trial_anime_user_id, NULL, '追踪长期预定款价格波动真相', JSON_ARRAY('新品发售前后价格走势', '二手市场供需变化', '一个月价格记录'), 'deferred', '需每周记录多款商品价格', '搜索需求强，但长周期跟踪门槛较高，先排入待办。', 'manual', 'paused', 'low', JSON_ARRAY('手办', '价格', '长期记录'), UTC_TIMESTAMP());

SET @ideas = JSON_ARRAY(
  JSON_OBJECT('title','300元怎么买最值','angle','把预算分别押在官店、代购和二手三条路线，实测哪条体验提升最大','audience','刚入坑、预算有限的谷子新人','cost','300元实购，单拆箱场景一天拍完','hook','先说结论：300元最不该先买的，恰好是开箱视频里最上镜的那个','why_different','不是单品开箱，而是有限预算的渠道分配实验'),
  JSON_OBJECT('title','开箱验货挑战','angle','记录每件周边从到货到验货的标准流程，逐项核对瑕疵与正版特征','audience','担心买到瑕疵或盗版的收藏党','cost','三件不同渠道周边，重点成本是拍摄与核对','hook','同一个款，三个渠道到货，瑕疵率差得离谱','why_different','用标准化验货清单替代主观值不值'),
  JSON_OBJECT('title','网红谷子反向清单','angle','拆解五件高热度周边，按溢价、做工和转手风险做去留审判','audience','容易被种草、怕买贵的人','cost','需借齐五件热门周边，拍摄约两天','hook','大家都在买的五样谷子，我劝你至少省下其中三笔钱','why_different','从加购转为减法，冲突感更强')
);
INSERT INTO `idea_sessions` (`user_id`, `topic_id`, `vague_idea`, `ideas_json`, `selected_index`, `saved_json`, `created_at`)
VALUES (@trial_anime_user_id, @trial_anime_topic_id, '300 元预算，怎么在吃谷时买到真正值得的周边？', CAST(@ideas AS CHAR), 0, '[0]', UTC_TIMESTAMP());
SET @trial_anime_idea_id = LAST_INSERT_ID();

SET @script = JSON_OBJECT(
  'title','300元吃谷预算：钱到底该花在哪',
  'hook','先说结论：预算只有300元，最先订热门大件，可能是整套吃谷计划里回报最低的一笔。',
  'duration_hint','约8分钟',
  'shots',JSON_ARRAY(
    JSON_OBJECT('time_range','0:00-0:15','camera','正面近景+未开箱周边','action','展示300元预算与三类渠道','line','今天只花300元，看看官店、代购和二手，到底谁最值得先订。','interaction','弹幕先押一个渠道'),
    JSON_OBJECT('time_range','0:15-0:55','camera','俯拍','action','公布统一验货流程','line','不比玄学感受：到货、拆盒、核对瑕疵和正版特征，每件都过一遍。','interaction',''),
    JSON_OBJECT('time_range','0:55-2:00','camera','分屏对比','action','测试官店渠道','line','第一套从官店下单，包装和售后最稳，但预售周期和溢价最明显。','interaction',''),
    JSON_OBJECT('time_range','2:00-3:15','camera','价差表格特写','action','测试代购渠道','line','第二套看着便宜，但运费、补款和发货时间都要算进成本。','interaction','猜猜哪一单最划算'),
    JSON_OBJECT('time_range','3:15-4:20','camera','环境全景','action','测试二手渠道','line','第三套最考验眼光，验货做不好翻车概率最高，但捡漏也最香。','interaction',''),
    JSON_OBJECT('time_range','4:20-5:45','camera','数据图表+回放','action','汇总三轮数据','line','按每省十块钱花多少精力算，官店第一，二手第二，代购最后。','interaction',''),
    JSON_OBJECT('time_range','5:45-7:10','camera','手持逐件展示','action','给三档抄作业清单','line','只有100元先选小件周边；300元可以冲一件大件；再往上就要考虑转卖风险。','interaction','评论区留下你的预算和入坑方向'),
    JSON_OBJECT('time_range','7:10-8:00','camera','补拍桌面展示','action','说明适用与不适用人群','line','这套适合刚入坑的学生党；收藏老手和只收绝版的，优先级要重排。','interaction','下期按最高赞谷子做复测')
  ),
  'cta','收藏这张渠道顺序表，评论区留下你的预算，我挑最高赞配置复测。'
);
SET @covers = JSON_ARRAY(
  JSON_OBJECT('style','数据对比','prompt','官店代购二手三格对比，中央巨大300元，三件谷子带红绿箭头，粉蓝二次元风'),
  JSON_OBJECT('style','避坑冲突','prompt','UP主手拿热门谷子摇头，瑕疵放大镜高亮，标题吃谷别踩坑，手办周边堆叠背景'),
  JSON_OBJECT('style','清单干货','prompt','100/300/500元三档吃谷俯拍，周边整齐排列，价格标签清晰，B站开箱封面'),
  JSON_OBJECT('style','开箱现场','prompt','剪刀与未拆快递同框，真实拆盒瞬间，醒目验货二字，柔和房间灯光'),
  JSON_OBJECT('style','前后对比','prompt','空荡书桌到谷子展示墙分屏，人物惊喜表情，300元改造结果'),
  JSON_OBJECT('style','结论先行','prompt','三件谷子领奖台，官店第一二手第二，强对比大字先订谁')
);
SET @risks = JSON_ARRAY(
  JSON_OBJECT('level','mid','category','样本代表性','detail','单次购买与个人渠道不代表所有情况','suggestion','公开渠道、价格和购买时间'),
  JSON_OBJECT('level','low','category','价格波动','detail','行情和补款会改变成本组合','suggestion','标注购买日期与到手价区间'),
  JSON_OBJECT('level','high','category','商业披露','detail','借测或团购未说明会损害可信度','suggestion','片头和简介明确样品来源')
);
INSERT INTO `scripts` (`user_id`, `topic_id`, `idea_session_id`, `outline`, `shot_list`, `comments_text`, `script_json`, `cover_prompts_json`, `risks_json`, `created_at`)
VALUES (@trial_anime_user_id, @trial_anime_topic_id, @trial_anime_idea_id, '300元预算挑战 → 统一验货流程 → 三套渠道路线 → 数据结论 → 分档购买清单', '定金截图、到货包裹、三件周边、验货放大镜、价差表格、二手平台、最终桌面展示', '- 预算只有100元该怎么减？\n- 官店和代购差的钱去哪了？\n- 已经买了贵款的人怎么办？', CAST(@script AS CHAR), CAST(@covers AS CHAR), CAST(@risks AS CHAR), UTC_TIMESTAMP());

INSERT INTO `calendar_events` (`user_id`, `title`, `start_date`, `end_date`, `location`, `vlog_fit`, `commercial`, `raw_text`, `source`, `created_at`)
VALUES
(@trial_anime_user_id, '秋季新番周边预订截止周', DATE_FORMAT(DATE_ADD(UTC_DATE(), INTERVAL 7 DAY), '%Y-%m-%d'), DATE_FORMAT(DATE_ADD(UTC_DATE(), INTERVAL 7 DAY), '%Y-%m-%d'), '线上商城', '做新番谷子预订避坑清单，提醒哪些值得蹲补款', '周边平台合作', '试用空间按人设预置', 'capture', UTC_TIMESTAMP()),
(@trial_anime_user_id, '本地漫展开展日', DATE_FORMAT(DATE_ADD(UTC_DATE(), INTERVAL 16 DAY), '%Y-%m-%d'), DATE_FORMAT(DATE_ADD(UTC_DATE(), INTERVAL 16 DAY), '%Y-%m-%d'), '线下展馆', '用吃谷清单逛展，拍战利品与排队避坑实录', '漫展官方合作', '试用空间按人设预置', 'capture', UTC_TIMESTAMP()),
(@trial_anime_user_id, '手办补款集中到货周', DATE_FORMAT(DATE_ADD(UTC_DATE(), INTERVAL 25 DAY), '%Y-%m-%d'), DATE_FORMAT(DATE_ADD(UTC_DATE(), INTERVAL 25 DAY), '%Y-%m-%d'), '线上 / 家中', '开箱验货按标准流程过一遍，做补款到货真相记录', '官店补款活动', '试用空间按人设预置', 'capture', UTC_TIMESTAMP());

UPDATE `users` SET `active_persona_id` = @trial_anime_persona_id WHERE `id` = @trial_anime_user_id;

-- ============================================================================
-- Block 3/3 · pet（萌宠动物 · 毛球生活观察局）
-- ============================================================================

INSERT INTO `users` (`username`, `password_hash`, `active_persona_id`, `created_at`)
VALUES ('demo-pet', '$2b$12$3NBSraxa/Li1jLqTheNvruIFNN3gEE.bTKUWWZeTIkY1KMElsIJOu', NULL, UTC_TIMESTAMP())
ON DUPLICATE KEY UPDATE `id` = LAST_INSERT_ID(`id`), `active_persona_id` = NULL;
SET @trial_pet_user_id = LAST_INSERT_ID();

DELETE FROM `scripts` WHERE `user_id` = @trial_pet_user_id;
DELETE FROM `idea_sessions` WHERE `user_id` = @trial_pet_user_id;
DELETE FROM `topics` WHERE `user_id` = @trial_pet_user_id;
DELETE FROM `inspirations` WHERE `user_id` = @trial_pet_user_id;
DELETE FROM `calendar_events` WHERE `user_id` = @trial_pet_user_id;
DELETE FROM `personas` WHERE `user_id` = @trial_pet_user_id;
DELETE FROM `user_settings` WHERE `user_id` = @trial_pet_user_id;

INSERT INTO `user_settings` (`user_id`, `llm_base_url`, `llm_model`, `llm_api_key`, `updated_at`)
VALUES (@trial_pet_user_id, 'https://api.deepseek.com/v1', 'deepseek-v4-pro', '', UTC_TIMESTAMP());

SET @skill_brief = JSON_OBJECT(
  'positioning', '用治愈日常和科学照护帮铲屎官养得明白，给养宠和想养的人看，靠「行为记录+就医边界」被记住',
  'hook_formula', JSON_ARRAY(
    '先说结论：领养第一周，先别急着抱',
    '同样的小猫，为什么别人家的适应那么快？把行为记录摆出来',
    '看着很治愈，但新手养宠最容易踩的是这几个坑'
  ),
  'tone_rules', JSON_ARRAY('结尾固定「就医信号 / 照护清单」两行', '先给结论再给行为依据', '涉及健康先引导就医', '不制造弃养焦虑'),
  'topic_preferences', JSON_ARRAY('优先做适应期与照护误区', '追踪新手铲屎官真实痛点', '不做摆拍伤害与违规饲养', '日更，优先可复现观察'),
  'script_structure', '0-15秒先给结论；中段按天记录行为、演示正确照护、展示反例；结尾列就医信号与照护清单',
  'interaction_style', '口播先让观众猜行为含义；置顶补充照护边界；高频问题进入下期复测',
  'red_lines', JSON_ARRAY('不摆拍伤害动物', '不推荐违规饲养', '不代替兽医诊断', '不制造弃养焦虑'),
  'system_prompt', '你是为 UP 主「毛球生活观察局」工作的虚拟编导。频道用连续的日常行为记录和科学照护知识，替新晋和潜在铲屎官做养宠决策。所有内容先给明确结论，再展示行为依据、环境布置和照护步骤，涉及症状先引导就医，不代替兽医诊断。选题优先领养适应、照护误区、行为观察和动物福利，不摆拍伤害动物、不推荐违规饲养、不制造弃养焦虑。脚本开头十五秒必须抛出先别做什么的判断；中段安排每日记录、环境丰容演示并主动展示反例；结尾固定列出就医信号与照护清单。口播温柔、具体、有科学依据，不用绝对化保证。评论区先让观众猜行为含义，置顶补充照护边界，把高频问题做成下期复测。严禁摆拍伤害动物、推荐违规饲养、代替兽医诊断、制造弃养焦虑。'
);

INSERT INTO `personas` (
  `user_id`, `template_key`, `name`, `style_desc`, `audience`, `video_format`, `taboos`, `sample_tone`,
  `zone`, `content_style`, `update_freq`, `comment_style`, `skill_prompt`, `skill_brief_json`, `skill_generated_at`, `created_at`
) VALUES (
  @trial_pet_user_id, 'trial-animal-healer', '毛球生活观察局',
  '治愈系铲屎官：记录毛孩子日常，也讲科学饲养，萌与靠谱并存。',
  '云吸猫狗、想养和正在养宠的年轻人',
  'B 站 6–10 分钟横屏，萌宠日常 + 科学喂养讲解 + 真实行为记录',
  '摆拍伤害动物、推荐违规饲养、代替兽医诊断、制造弃养焦虑',
  '用治愈画面讲清养宠常识，遇到医疗问题先建议咨询医生，再给行为观察建议。',
  '动物圈', '宠物日常、养宠科普', '日更', '理性答疑，置顶补充动物福利边界，把高频问题做成下期复测',
  JSON_UNQUOTE(JSON_EXTRACT(@skill_brief, '$.system_prompt')), CAST(@skill_brief AS CHAR), UTC_TIMESTAMP(), UTC_TIMESTAMP()
);
SET @trial_pet_persona_id = LAST_INSERT_ID();

INSERT INTO `inspirations` (`user_id`, `raw_text`, `source_note`, `created_at`)
VALUES (
  @trial_pet_user_id,
  '领养回来的小猫适应期讨论升温：很多新晋铲屎官担心应激、乱抓和喂食问题，不知道第一周该做什么、哪些信号需要马上就医，以及怎么让猫咪舒服地适应新家。',
  '试用空间 · 示例灵感', UTC_TIMESTAMP()
);
SET @trial_pet_inspiration_id = LAST_INSERT_ID();

INSERT INTO `topics` (`user_id`, `inspiration_id`, `title`, `highlights`, `feasibility`, `cost_note`, `why`, `source`, `status`, `priority`, `tags`, `created_at`)
VALUES (
  @trial_pet_user_id, @trial_pet_inspiration_id, '实测七天领养适应计划',
  JSON_ARRAY('第一天到第七天行为记录', '环境丰容清单', '找出最容易踩的应激雷区', '给出可抄作业适应表'),
  'quick', '基础用品约300元，重点成本是每天记录', '痛点普遍、过程可记录，结果对新手铲屎官可直接照做。',
  'extract', 'ready', 'high', JSON_ARRAY('猫咪', '领养', '科普', '萌宠'), UTC_TIMESTAMP()
);
SET @trial_pet_topic_id = LAST_INSERT_ID();

INSERT INTO `topics` (`user_id`, `inspiration_id`, `title`, `highlights`, `feasibility`, `cost_note`, `why`, `source`, `status`, `priority`, `tags`, `created_at`)
VALUES
(@trial_pet_user_id, @trial_pet_inspiration_id, '对比新手养宠常见误区', JSON_ARRAY('喂食误区逐项核对', '常见行为误读演示', '算清科学照护时间成本'), 'quick', '用家中现有物品演示，无需额外购买', '误区隐蔽且影响大，真实对照能直接帮助新手避坑。', 'extract', 'inbox', 'mid', JSON_ARRAY('养宠', '误区', '科普'), UTC_TIMESTAMP()),
(@trial_pet_user_id, NULL, '追踪新猫行为变化一个月', JSON_ARRAY('每周行为变化记录', '饮食与体重追踪', '一个月适应总结'), 'deferred', '需连续记录一个月', '长周期行为数据有价值，但拍摄与记录门槛较高，先排入待办。', 'manual', 'paused', 'low', JSON_ARRAY('猫咪', '行为', '长期记录'), UTC_TIMESTAMP());

SET @ideas = JSON_ARRAY(
  JSON_OBJECT('title','七天领养适应计划','angle','按天拆解适应流程，每天只做一件关键事，记录行为变化','audience','刚领养猫、手忙脚乱的新手','cost','基础用品约300元，单场景一周拍完','hook','领养第一周别急着抱，先做对这三件事','why_different','用可执行的每日清单替代笼统的别应激'),
  JSON_OBJECT('title','新手养宠误区大扫雷','angle','逐项演示常见误区与正确做法，标清哪些信号该就医','audience','想养宠、怕养错的年轻人','cost','用家中现有物品演示，无额外成本','hook','这五个养宠误区，九成新手都踩过','why_different','误区对照比道理更有说服力，就医边界写清楚'),
  JSON_OBJECT('title','毛球行为观察日记','angle','连续记录行为与环境的对应关系，找出舒适区','audience','想更懂自己毛孩子的铲屎官','cost','连续一周记录，重点成本是耐心','hook','看完这个观察日记，你会更懂你的猫','why_different','用行为数据替代主观猜测')
);
INSERT INTO `idea_sessions` (`user_id`, `topic_id`, `vague_idea`, `ideas_json`, `selected_index`, `saved_json`, `created_at`)
VALUES (@trial_pet_user_id, @trial_pet_topic_id, '领养一只小猫，怎么让它快速适应新家又保持健康？', CAST(@ideas AS CHAR), 0, '[0]', UTC_TIMESTAMP());
SET @trial_pet_idea_id = LAST_INSERT_ID();

SET @script = JSON_OBJECT(
  'title','领养小猫第七天：我们做对了什么',
  'hook','先说结论：领养第一周最该做的，不是天天抱，而是先让猫咪有自己的安全角落。',
  'duration_hint','约8分钟',
  'shots',JSON_ARRAY(
    JSON_OBJECT('time_range','0:00-0:15','camera','正面近景+新到家小猫','action','展示七天记录与关键时间线','line','这只小猫到家七天，我们做对了三件事，也踩了一个雷。','interaction','弹幕先猜猜雷是什么'),
    JSON_OBJECT('time_range','0:15-0:55','camera','俯拍隔离房间','action','公布第一天布置','line','第一天不急着互动，先给独立房间、躲藏处和安静的空间。','interaction',''),
    JSON_OBJECT('time_range','0:55-2:00','camera','分屏对比','action','演示猫砂与饮食安排','line','第二件事是让吃喝拉撒全部定点，气味熟悉了，情绪才稳定。','interaction',''),
    JSON_OBJECT('time_range','2:00-3:15','camera','行为特写','action','展示互动时机','line','第三件事是等它主动靠近再互动，强抱反而会加重应激。','interaction','你家猫到家第几天敢靠近你？'),
    JSON_OBJECT('time_range','3:15-4:20','camera','环境全景','action','演示丰容与玩耍','line','用逗猫棒和纸箱做环境丰容，探索欲起来，适应就快多了。','interaction',''),
    JSON_OBJECT('time_range','4:20-5:45','camera','记录表特写','action','汇总七天行为数据','line','把躲藏时长、进食量和便便情况记下来，变化趋势一眼看清。','interaction',''),
    JSON_OBJECT('time_range','5:45-7:10','camera','手持逐项讲解','action','给就医信号清单','line','出现精神萎靡、拒食超过24小时或持续呕吐，别查攻略，先问医生。','interaction','评论区留下你遇到的情况'),
    JSON_OBJECT('time_range','7:10-8:00','camera','升级后家中全景','action','说明适用与不适用人群','line','这套适合单猫新家；多猫或已养宠家庭，隔离和引入方式要重排。','interaction','下期按最高赞问题做复测')
  ),
  'cta','收藏这份适应计划表，评论区留下你的问题，我挑最高赞做下期复测。'
);
SET @covers = JSON_ARRAY(
  JSON_OBJECT('style','数据对比','prompt','七天行为记录表与小猫同框，三件关键事带勾选，粉蓝治愈风'),
  JSON_OBJECT('style','避坑冲突','prompt','UP主摆手示意不要强抱，小猫躲进纸箱，标题别急着抱，明亮客厅'),
  JSON_OBJECT('style','清单干货','prompt','领养第一周每日清单俯拍，猫砂盆喂食碗整齐排列，清晰步骤，B站科普封面'),
  JSON_OBJECT('style','记录现场','prompt','手写记录表与小猫同框，真实领养第七天，醒目科学二字'),
  JSON_OBJECT('style','前后对比','prompt','躲藏小猫到主动蹭手分屏，温馨表情，领养七天变化'),
  JSON_OBJECT('style','结论先行','prompt','三件关键事领奖台，安全角落第一，强对比大字先做什么')
);
SET @risks = JSON_ARRAY(
  JSON_OBJECT('level','mid','category','个体差异','detail','单只猫咪的表现不代表所有品种','suggestion','公开猫咪年龄与性格，标注个体差异'),
  JSON_OBJECT('level','low','category','记录偏差','detail','居家记录可能不够客观','suggestion','固定观察时间与记录格式'),
  JSON_OBJECT('level','high','category','医疗边界','detail','科普不能替代兽医诊断','suggestion','涉及症状先引导就医，明确免责说明')
);
INSERT INTO `scripts` (`user_id`, `topic_id`, `idea_session_id`, `outline`, `shot_list`, `comments_text`, `script_json`, `cover_prompts_json`, `risks_json`, `created_at`)
VALUES (@trial_pet_user_id, @trial_pet_topic_id, @trial_pet_idea_id, '领养第七天复盘 → 每天关键动作 → 三件重要事 → 就医信号清单 → 新手可抄作业', '第一天接猫、隔离房间、猫砂盆、喂食碗、逗猫棒、行为记录表、兽医咨询电话', '- 多猫家庭怎么适应？\n- 猫咪一直躲怎么办？\n- 什么情况必须马上去医院？', CAST(@script AS CHAR), CAST(@covers AS CHAR), CAST(@risks AS CHAR), UTC_TIMESTAMP());

INSERT INTO `calendar_events` (`user_id`, `title`, `start_date`, `end_date`, `location`, `vlog_fit`, `commercial`, `raw_text`, `source`, `created_at`)
VALUES
(@trial_pet_user_id, '国际领养日公益倡导周', DATE_FORMAT(DATE_ADD(UTC_DATE(), INTERVAL 7 DAY), '%Y-%m-%d'), DATE_FORMAT(DATE_ADD(UTC_DATE(), INTERVAL 7 DAY), '%Y-%m-%d'), '线下 / 社区', '用七天适应计划做领养科普，记录志愿者探访', '宠物公益组织合作', '试用空间按人设预置', 'capture', UTC_TIMESTAMP()),
(@trial_pet_user_id, '秋季宠物换季护理提醒', DATE_FORMAT(DATE_ADD(UTC_DATE(), INTERVAL 16 DAY), '%Y-%m-%d'), DATE_FORMAT(DATE_ADD(UTC_DATE(), INTERVAL 16 DAY), '%Y-%m-%d'), '线上', '做换季饮食与毛发护理清单，拍日常护理实录', '宠物用品品牌合作', '试用空间按人设预置', 'capture', UTC_TIMESTAMP()),
(@trial_pet_user_id, '宠物友好空间开放日', DATE_FORMAT(DATE_ADD(UTC_DATE(), INTERVAL 25 DAY), '%Y-%m-%d'), DATE_FORMAT(DATE_ADD(UTC_DATE(), INTERVAL 25 DAY), '%Y-%m-%d'), '线下空间', '记录宠物友好空间实地体验，给带宠出行攻略', '宠物空间官方合作', '试用空间按人设预置', 'capture', UTC_TIMESTAMP());

UPDATE `users` SET `active_persona_id` = @trial_pet_persona_id WHERE `id` = @trial_pet_user_id;

COMMIT;

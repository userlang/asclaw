# 暗影地牢 · AI 勇者养成计划 —— 逐步照抄实现文档

> 配套设计文档：`../backend/test`（游戏规则、数值配平、七步接线指南都在那里，本文不重复）。
> 本文是**实现文档**：每一步给出完整、可直接复制的代码。你照抄即可，无需自己补任何实现。
>
> 目标闭环：**每件装备都锻造 20 级之后，方可击败地牢之主。**
> （20 级即全套 6 件装备各升至 20 级；数值在原设计上小幅配平，见"数值改动一览"。）

运行方式（仓库根目录）：

```shell
backend/.venv/bin/python test/game_agent.py
```

前置条件与 `../backend/test` 完全一致：`DASHSCOPE_API_KEY` 已设置（或写入 `backend/.env`，脚本会自动读取）。

---

## 第 0 步 · 新建文件，抄导入块与配置

新建 `../backend/test`。头部整段抄自 `../backend/test`（跑通过的），一个字不用改：

```python
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from agentscope.agent import ReActAgent
from agentscope.formatter import OpenAIChatFormatter
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel
from agentscope.plan import PlanNotebook
from agentscope.token import OpenAITokenCounter
from agentscope.tool import Toolkit, ToolResponse
from agentscope.message import TextBlock
from loguru import logger

# ---------------------------------------------------------------------------
# 配置读取：优先环境变量，其次尝试解析 backend/.env（避免强依赖 backend 包导入）
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv_fallback() -> None:
    """把 backend/.env 中的键补进 os.environ（不覆盖已有环境变量）。"""
    env_file = REPO_ROOT / 'backend' / '.env'
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv_fallback()

DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', 'sk-xxx')
DASHSCOPE_BASE_URL = os.getenv(
    'DASHSCOPE_BASE_URL',
    'http://api-ai.stage-xy.ktopia.cn:82/v1',
)
DASHSCOPE_CHAT_MODEL = os.getenv('DASHSCOPE_CHAT_MODEL', 'qwen3.7-max')
```

> 注意：`DASHSCOPE_API_KEY` 的默认值请抄 `react_agent_demo.py` 第 81 行那个真实 key（本文写成 `sk-xxx` 防止泄露进 git）。

**自检 ①：**

```shell
backend/.venv/bin/python -c "import sys; sys.path.insert(0,'test'); import game_agent"
```

不报错才能进下一步。

---

## 第 1 步 · 抄规则常量（本案例新增的核心数值）

原设计的 10 点造价 / 5 件护甲改成了 **20 级升级制**。以下常量整段抄：

```python
# ---------------------------------------------------------------------------
# 暗影地牢 · 规则常量（数值配平见 agent-game 文档）
# ---------------------------------------------------------------------------

FORGE_COST = 10                    # 每级锻造消耗：10 经验
ARMOR_DEFENSE = {'肩甲': 2, '胸甲': 3, '鞋子': 1, '护腿': 2, '腰带': 1}
ARMOR_SLOTS = tuple(ARMOR_DEFENSE) + ('武器',)
FORGE_MAX_LEVEL = 20               # ← 每件装备 20 级封顶
BOSS_UNLOCK_LEVEL = FORGE_MAX_LEVEL  # 击败地牢之主的门槛：全部 6 件都到 20 级
SPAWN_LIMIT = 25                   # 召唤法阵每次上限
MONSTER_HP = 8
BOSS_HP = 100
BOSS_ATTACK = 10
HERO_START_HP = 50
REST_COST, REST_HEAL, REST_MAX = 5, 10, 3   # 篝火：−5 经验回 10 血，每局 3 次
```

**数值改动一览**（相对原设计文档）：

| 项目 | 原设计 | 现在 | 为什么 |
|---|---|---|---|
| 锻造 | 一次性 −10 经验，6 件成型 | 每件 **20 级**，每级 −10 经验 | 你的新目标：闭环在"全 20 级" |
| 全套总账 | 60 经验 | 6 件 × 20 级 × 10 = **1200 经验 = 1200 杀 = 48 批召唤** | 一局工具调用数大幅上升，见第 4 步 max_iters |
| 击败 Boss 条件 | 护甲 ≥ 8 的数值推演 | **硬门槛**：6 件全部 20 级才允许挑战成功，否则 Boss 直接免疫并给出缺口报告 | 规则写在工具里（三铁律之一），模型骗不过 if |
| Boss 战斗 | 回合制 −(10−护甲) | 门槛未达标时**跳过回合制**，直接免疫 + 诊断；达标后一回合一结算 | 避免为刷等级打 200 回合的日志洪水 |

---

## 第 2 步 · 抄 GameState（世界状态）

```python
from dataclasses import dataclass, field


@dataclass
class GameState:
    hp: int = HERO_START_HP
    xp: int = 0
    attack: int = 10                              # 木剑
    equipment: dict = field(default_factory=dict)  # slot -> 当前等级（1~20）
    monsters_alive: int = 0
    boss_hp: int = BOSS_HP
    map_created: bool = False
    treasure_found: bool = False
    has_weapon: bool = False
    rest_used: int = 0


STATE = GameState()   # 模块级单例：这就是"世界"本身，所有工具共享读写
```

**自检 ②：**

```shell
backend/.venv/bin/python -c "import sys; sys.path.insert(0,'test'); import game_agent; print(game_agent.STATE.hp)"
```

打印 `50` 才进下一步。

---

## 第 3 步 · 抄 9 个工具函数（完整代码，直接复制）

每个函数的 docstring 就是模型看到的说明书（**变量提示词**），函数体就是规则执法。整段抄：

### 工具 1/9：create_map

```python
def create_map(theme: str, difficulty: str) -> ToolResponse:
    """创建暗影地牢的地图。

    Args:
        theme (`str`):
            地牢主题，例如 "腐朽回廊"、"白骨大厅"、"深渊之眼"。
        difficulty (`str`):
            难度，可选："简单"、"普通"、"噩梦"。

    Returns:
        `ToolResponse`:
            地图描述与房间数；提示"传说深处藏有一个宝箱"。
    """
    import random
    STATE.map_created = True
    rooms = random.randint(8, 15)
    logger.info('[tool] create_map({}, {})', theme, difficulty)
    return ToolResponse(content=[TextBlock(type='text', text=(
        f'地图已展开：【{theme}】（难度：{difficulty}），共 {rooms} 个房间。'
        f'传说深处藏有一个宝箱，找到它可获得额外奖励。'
    ))])
```

### 工具 2/9：spawn_monsters

```python
def spawn_monsters(count: int) -> ToolResponse:
    """在当前房间召唤怪物。

    Args:
        count (`int`):
            想召唤的怪物数量，每次最多 25 只。超出会被直接拒绝，请分批召唤。

    Returns:
        `ToolResponse`:
            召唤结果与当前房间怪物总数。
    """
    if not STATE.map_created:
        return ToolResponse(content=[TextBlock(type='text', text=(
            'Error: 还没有地图，请先用 create_map 创建地牢。'
        ))])
    if count > SPAWN_LIMIT:
        return ToolResponse(content=[TextBlock(type='text', text=(
            f'Error: 召唤法阵每次最多拉来 {SPAWN_LIMIT} 只怪物（你要求 {count} 只）。'
            f'请分批召唤，例如每次 {SPAWN_LIMIT} 只。'
        ))])
    if count < 1:
        return ToolResponse(content=[TextBlock(type='text', text=(
            'Error: 至少召唤 1 只怪物。'
        ))])
    STATE.monsters_alive += count
    logger.info('[tool] spawn_monsters({})', count)
    return ToolResponse(content=[TextBlock(type='text', text=(
        f'召唤成功！{count} 只怪物从阴影中爬出（HP {MONSTER_HP}，会反击）。'
        f'当前房间怪物总数：{STATE.monsters_alive}。'
    ))])
```

### 工具 3/9：fight_monsters

```python
def fight_monsters(target: str) -> ToolResponse:
    """与当前房间的怪物战斗。

    Args:
        target (`str`):
            "all" 表示清空全场怪物；或某只怪的编号如 "1"（暂只支持 "all"）。

    Returns:
        `ToolResponse`:
            击杀数、经验变化、HP 变化、剩余怪物数——一条播报里给全。
    """
    if STATE.monsters_alive == 0:
        return ToolResponse(content=[TextBlock(type='text', text=(
            'Error: 房间里没有怪物可打。请先用 spawn_monsters 召唤。'
        ))]
        )
    killed = STATE.monsters_alive
    gain = killed                                   # 每杀 1 只 +1 经验
    STATE.xp += gain
    # 每只怪对勇者造成 max(0, 1 − 护甲) 点伤害（原设计公式）：
    # 任一护甲部位锻造后护甲 ≥ 1 → 每只 0 伤害（安全期）；裸装刷怪刀刀见血（痛期）
    defense = sum(ARMOR_DEFENSE[s] for s in ARMOR_DEFENSE if s in STATE.equipment)
    damage_taken = killed * max(0, 1 - defense)
    STATE.hp = max(0, STATE.hp - damage_taken)
    STATE.monsters_alive = 0
    logger.info('[tool] fight_monsters(all) killed={}', killed)
    return ToolResponse(content=[TextBlock(type='text', text=(
        f'战斗结束！击杀 {killed} 只，经验 +{gain} → 当前 {STATE.xp}。'
        f'受到 {damage_taken} 点伤害，HP → {STATE.hp}。'
        f'房间里已无怪物。'
        + ('（护甲 ≥ 1，安全期：刷怪零损伤）' if defense >= 1 else
           '（⚠️ 裸装痛期：每杀 1 只掉 1 血，先锻一件护甲吧！）')
    ))])
```

### 工具 4/9：create_weapon

```python
def create_weapon(name: str, material: str) -> ToolResponse:
    """领取一把初始武器（攻击力 10）。仅当手上没有武器时可用。

    Args:
        name (`str`):
            武器名字，例如 "木剑"。
        material (`str`):
            材质，例如 "橡木"、"铁木"。

    Returns:
        `ToolResponse`:
            武器名与攻击力；已有武器时拒绝。
    """
    if STATE.has_weapon:
        return ToolResponse(content=[TextBlock(type='text', text=(
            f'Error: 你已有武器（攻击力 {STATE.attack}），不能重复领取。'
            f'想提升攻击力请用 forge_equipment 锻造"武器"部位。'
        ))])
    STATE.has_weapon = True
    STATE.attack = 10
    logger.info('[tool] create_weapon({}, {})', name, material)
    return ToolResponse(content=[TextBlock(type='text', text=(
        f'你握住了 {material}打造的「{name}」，攻击力 10。'
        f'想升到 18 并解锁 20 级成长，请用 forge_equipment 锻造"武器"部位。'
    ))])
```

### 工具 5/9：forge_equipment（本案例最核心的工具）

```python
def forge_equipment(slot: str) -> ToolResponse:
    """把指定部位升 1 级（每件最高 20 级），消耗 10 经验值。锻造后立即穿戴。

    Args:
        slot (`str`):
            装备部位，可选：肩甲 / 胸甲 / 鞋子 / 护腿 / 腰带 / 武器。
            锻造武器后攻击力从 10 提升到 18。
            **只有全部 6 件都升到 20 级，才有资格击败地牢之主。**

    Returns:
        `ToolResponse`:
            升级结果、当前等级、剩余经验、距"全 20 级"的总进度。
    """
    if slot not in ARMOR_SLOTS:
        return ToolResponse(content=[TextBlock(type='text', text=(
            f'Error: 部位「{slot}」不合法，可选：{"、".join(ARMOR_SLOTS)}。'
        ))])
    if not STATE.has_weapon and slot == '武器':
        return ToolResponse(content=[TextBlock(type='text', text=(
            'Error: 你还没有武器，请先用 create_weapon 领取，再锻造升级。'
        ))])
    if STATE.xp < FORGE_COST:
        return ToolResponse(content=[TextBlock(type='text', text=(
            f'Error: 经验不足！升 1 级需要 {FORGE_COST} 点，当前只有 {STATE.xp} 点，'
            f'还差 {FORGE_COST - STATE.xp} 点。先去打怪攒经验吧！'
        ))])
    level = STATE.equipment.get(slot, 0)
    if level >= FORGE_MAX_LEVEL:
        return ToolResponse(content=[TextBlock(type='text', text=(
            f'Error: {slot} 已是满级 {FORGE_MAX_LEVEL} 级，无需再锻。'
            f'把经验花在还没满级的部位上。'
        ))])

    STATE.xp -= FORGE_COST
    level += 1
    STATE.equipment[slot] = level
    if slot == '武器':
        STATE.attack = 18
        msg = f'锻造成功！武器升到 {level} 级，攻击力 18。'
    else:
        msg = f'锻造成功！{slot} 升到 {level} 级（护甲 +{ARMOR_DEFENSE[slot]}）。'

    # 全局进度播报：模型靠这段推算"还差多少"
    maxed = [s for s in ARMOR_SLOTS if STATE.equipment.get(s, 0) >= FORGE_MAX_LEVEL]
    total_levels = sum(STATE.equipment.get(s, 0) for s in ARMOR_SLOTS)
    boss_ready = total_levels >= len(ARMOR_SLOTS) * FORGE_MAX_LEVEL
    logger.info('[tool] forge_equipment({}) -> Lv{}', slot, level)
    return ToolResponse(content=[TextBlock(type='text', text=(
        f'{msg} 剩余经验 {STATE.xp}。'
        f'总进度：{total_levels}/{len(ARMOR_SLOTS) * FORGE_MAX_LEVEL} 级'
        f'（已满级部位：{"、".join(maxed) or "无"}）。'
        + ('🏆 全部 20 级达成！你现在有资格挑战地牢之主了！'
           if boss_ready else
           f'记住：全部 6 件都到 {FORGE_MAX_LEVEL} 级才能击败地牢之主。')
    ))])
```

### 工具 6/9：query_status

```python
def query_status() -> ToolResponse:
    """查看勇者的完整状态面板。

    Returns:
        `ToolResponse`:
            HP / 经验 / 攻击力 / 各部位等级 / 场上怪物 / Boss 状态 一览。
    """
    equip_txt = '、'.join(
        f'{s} Lv{lv}' for s, lv in STATE.equipment.items()
    ) or '（尚未锻造任何装备）'
    boss_ready = sum(STATE.equipment.get(s, 0) for s in ARMOR_SLOTS) \
        >= len(ARMOR_SLOTS) * FORGE_MAX_LEVEL
    logger.info('[tool] query_status')
    return ToolResponse(content=[TextBlock(type='text', text=(
        f'===== 勇者面板 =====\n'
        f'HP：{STATE.hp}    经验：{STATE.xp}    攻击力：{STATE.attack}\n'
        f'装备：{equip_txt}\n'
        f'场上怪物：{STATE.monsters_alive} 只    地牢之主 HP：{STATE.boss_hp}\n'
        f'挑战资格：{"✅ 全 20 级已达成" if boss_ready else "❌ 尚未达成（全部 6 件都要 20 级）"}'
    ))])
```

### 工具 7/9：search_treasure

```python
def search_treasure() -> ToolResponse:
    """在当前地图搜寻宝箱（每张地图只藏一个，找到后消失）。

    Returns:
        `ToolResponse`:
            奖励结果（随机 +15 经验 或 回满血）；没找到时给出提示。
    """
    import random
    if not STATE.map_created:
        return ToolResponse(content=[TextBlock(type='text', text=(
            'Error: 还没有地图，请先用 create_map 创建地牢。'
        ))])
    if STATE.treasure_found:
        return ToolResponse(content=[TextBlock(type='text', text=(
            'Error: 这张地图的宝箱已经被你搜刮过了。'
        ))])
    STATE.treasure_found = True
    if random.random() < 0.5:
        STATE.xp += 15
        msg = f'你撬开宝箱，里面是远古经验结晶！经验 +15 → 当前 {STATE.xp}。'
    else:
        STATE.hp = HERO_START_HP
        msg = f'你撬开宝箱，里面是一瓶生命药剂！HP 回满 → {STATE.hp}。'
    logger.info('[tool] search_treasure')
    return ToolResponse(content=[TextBlock(type='text', text=msg)])
```

### 工具 8/9：challenge_boss（门槛执法在这里）

```python
def challenge_boss() -> ToolResponse:
    """挑战地牢之主（HP 100）。

    Returns:
        `ToolResponse`:
            胜利 → 结算报告；未达成"全部 6 件 20 级"门槛 → 地牢之主免疫
            所有伤害，并给出缺口报告（哪几件还差多少级）。
    """
    if STATE.boss_hp <= 0:
        return ToolResponse(content=[TextBlock(type='text', text=(
            '地牢之主已被击败。本局已通关，无需再战。'
        ))])
    total_levels = sum(STATE.equipment.get(s, 0) for s in ARMOR_SLOTS)
    need = len(ARMOR_SLOTS) * FORGE_MAX_LEVEL
    if total_levels < need:
        # ← 规则执法：门槛未到，Boss 免疫，直接给可行动的诊断
        gaps = '、'.join(
            f'{s} Lv{STATE.equipment.get(s, 0)}→20'
            for s in ARMOR_SLOTS
            if STATE.equipment.get(s, 0) < FORGE_MAX_LEVEL
        )
        logger.info('[tool] challenge_boss -> 门槛未达标')
        return ToolResponse(content=[TextBlock(type='text', text=(
            f'地牢之主免疫了你的攻击！'
            f'（装备总等级 {total_levels}/{need}，未达成"全部 6 件 20 级"）\n'
            f'缺口报告：{gaps}。\n'
            f'继续刷怪攒经验、锻造升级，等你全身 20 级再来。'
            f'（装备保留，经验保留，地牢之主在嘲笑你。）'
        ))])
    # 门槛达成：回合制结算，勇者必胜
    rounds = -(-BOSS_HP // STATE.attack)      # 向上取整需要的回合数
    STATE.boss_hp = 0
    logger.info('[tool] challenge_boss -> 胜利（{} 回合）', rounds)
    return ToolResponse(content=[TextBlock(type='text', text=(
        f'⚔️ 最终决战！你的攻击力 {STATE.attack}，'
        f'经过 {rounds} 个回合的鏖战，地牢之主轰然倒地！\n'
        f'===== 通关结算 =====\n'
        f'最终 HP：{STATE.hp}    总等级：{total_levels}/{need}    剩余经验：{STATE.xp}\n'
        f'暗影地牢恢复了平静。恭喜你，AI 勇者「阿爪」！'
    ))])
```

### 工具 9/9：rest_at_bonfire

```python
def rest_at_bonfire() -> ToolResponse:
    """在篝火旁休息：消耗 5 经验，回复 10 点 HP（每局最多 3 次）。

    Returns:
        `ToolResponse`:
            HP 变化与剩余次数；经验不足或次数用尽时拒绝。
    """
    if STATE.rest_used >= REST_MAX:
        return ToolResponse(content=[TextBlock(type='text', text=(
            f'Error: 篝火今天已经休息过 {REST_MAX} 次，不能再休了。'
        ))])
    if STATE.xp < REST_COST:
        return ToolResponse(content=[TextBlock(type='text', text=(
            f'Error: 休息需要 {REST_COST} 经验，当前只有 {STATE.xp} 点。先去打怪。'
        ))])
    STATE.xp -= REST_COST
    STATE.rest_used += 1
    STATE.hp += REST_HEAL
    logger.info('[tool] rest_at_bonfire')
    return ToolResponse(content=[TextBlock(type='text', text=(
        f'你在篝火旁歇了一会儿：HP +{REST_HEAL} → {STATE.hp}，'
        f'经验 −{REST_COST} → {STATE.xp}。剩余次数：{REST_MAX - STATE.rest_used}。'
    ))])
```

**自检 ③（裸调，不花 token）：**

```shell
backend/.venv/bin/python -c "
import sys; sys.path.insert(0,'test'); import game_agent as g
print(g.spawn_monsters(30).content[0]['text'])   # 期望：最多 25 只 的拒绝
print(g.forge_equipment('胸甲').content[0]['text'])  # 期望：经验不足 的拒绝
g.STATE.map_created = True
g.spawn_monsters(25); print(g.fight_monsters('all').content[0]['text'])  # 期望：+25 经验
print(g.challenge_boss().content[0]['text'])  # 期望：门槛未达 的免疫诊断
"
```

四条全符合预期，引擎就是好的。

---

## 第 4 步 · 抄 build_agent（装配 + 注册）

```python
# ---------------------------------------------------------------------------
# 组装 ReActAgent
# ---------------------------------------------------------------------------

def build_agent() -> ReActAgent:
    """创建暗影地牢勇者 agent「阿爪」。"""
    sys_prompt = (
        '你是 AI 勇者「阿爪」，被召唤进暗影地牢，唯一目标：击败地牢之主（HP 100）。'
        '你了解这个世界的法则：击杀一只怪物 +1 经验；锻造升 1 级装备消耗 10 经验，'
        '每件装备最高 20 级；召唤法阵每次最多拉来 25 只怪。量入为出，祝你好运。'
        '老猎人只留下一句忠告："孩子，攒够了再去见地牢之主——'
        '全身 20 级，一件都别少。"'
    )

    toolkit = Toolkit()
    toolkit.register_tool_function(create_map)          # 1 创建地图
    toolkit.register_tool_function(spawn_monsters)      # 2 召唤怪物
    toolkit.register_tool_function(fight_monsters)      # 3 打怪
    toolkit.register_tool_function(create_weapon)       # 4 领武器
    toolkit.register_tool_function(forge_equipment)     # 5 锻造升级
    toolkit.register_tool_function(query_status)        # 6 状态面板
    toolkit.register_tool_function(search_treasure)     # 7 搜宝箱
    toolkit.register_tool_function(challenge_boss)      # 8 挑战 Boss
    toolkit.register_tool_function(rest_at_bonfire)     # 9 篝火休息

    return ReActAgent(
        name='阿爪',
        sys_prompt=sys_prompt,
        model=OpenAIChatModel(
            model_name=DASHSCOPE_CHAT_MODEL,
            api_key=DASHSCOPE_API_KEY,
            stream=True,
            client_kwargs={'base_url': DASHSCOPE_BASE_URL},
        ),
        formatter=OpenAIChatFormatter(),
        toolkit=toolkit,
        long_term_memory=None,
        long_term_memory_mode='both',
        compression_config=ReActAgent.CompressionConfig(
            enable=True,
            agent_token_counter=OpenAITokenCounter('gpt-4o'),
            trigger_threshold=12000,
            keep_recent=4,
        ),
        enable_meta_tool=True,
        # 与咖啡馆 demo 的不同点 1：游戏工具全是写操作且顺序敏感，必须关并行
        parallel_tool_calls=False,
        plan_notebook=PlanNotebook(max_subtasks=6),
        print_hint_msg=True,
        # 与咖啡馆 demo 的不同点 2：一局约 50~60 次工具调用（1200 经验 ÷ 25/批 × 2
        # + 120 次锻造 + 杂项），默认 10 会中途"总结陈词"弃赛
        max_iters=90,
        tts_model=None,
    )
```

> **max_iters 为什么是 90：** 全 20 级 = 120 级锻造 + 48 批召唤 × 2（召唤+战斗）+ 领武器 + 面板等杂项 ≈ 120 + 96 + 5 ≈ **220 次调用**。
> 如果中途触发 `_summarizing` 强制收工，就调大；`qwen3.7-max` 单局 220 轮对 context 是考验，compression_config 已兜底。
> 想先小步验证：把 `FORGE_MAX_LEVEL` 临时改成 2（总账 12 经验），跑通一局再改回 20。

---

## 第 5 步 · 抄 main()（发起对局）

```python
async def main() -> None:
    if not DASHSCOPE_API_KEY:
        logger.error(
            '缺少 DASHSCOPE_API_KEY：请设置环境变量，或写入 backend/.env（本脚本会自动读取）。',
        )
        sys.exit(1)

    agent = build_agent()

    query = (
        '进入暗影地牢，开始你的冒险。目标：击败地牢之主。'
        '祝你好运，勇者阿爪。'
    )
    logger.info('>>> 召唤阵: {}', query)
    response = await agent(Msg('user', query, 'user'))
    text = ''.join(
        block.get('text', '')
        for block in (response.content or [])
        if isinstance(block, dict) and block.get('type') == 'text'
    )
    logger.info('<<< 阿爪: {}', text or '(空回复)')


if __name__ == '__main__':
    asyncio.run(main())
```

> 任务文案没有剧透最优解（没写"先刷 48 批再锻造"）——它只会自己算。

---

## 第 6 步 · 跑起来，观察

```shell
backend/.venv/bin/python test/game_agent.py
```

日志三种行的含义（与设计文档"5 个观察瞬间"对照）：

| 日志行 | 对应循环里的什么 |
|---|---|
| `[tool] spawn_monsters(25)` | toolkit 真实执行 |
| `[tool] forge_equipment(胸甲) -> Lv7` | 升级进度在推进 |
| `Unsupported block type thinking` | 模型思考块被 formatter 跳过——正常现象 |

**重点观察：**
1. **25 上限被拒**后是否自己算出分批；
2. **经验不足被拒**后是否转头刷怪；
3. **门槛未达冲 Boss** 后是否读懂缺口报告回去补级；
4. **forge 返回里的总进度播报**是否让它少调 query_status。

---

## 常见翻车速查表

| 症状 | 断的线 | 处方 |
|---|---|---|
| 一局跑一半模型"总结陈词"收工 | 循环守卫 | `max_iters` 调大（全 20 级需要 90+，见第 4 步） |
| 同时发多个 tool_call，状态错乱 | 行动空间 | 确认 `parallel_tool_calls=False` 生效 |
| 挑战 Boss 一直失败但不补级 | 观察质量 | challenge_boss 的缺口报告加粗"还差 X 级" |
| 填错参数（count 传字符串） | 工具 schema | docstring 的 Args 段重写：类型+范围+例子 |
| ModuleNotFoundError | 环境 | 仓库根目录 + `backend/.venv/bin/python` |

---

## 完整文件顺序小结（自上而下拼起来就是 test/game_agent.py）

1. 导入块 + 配置（第 0 步）
2. 规则常量（第 1 步）
3. `GameState` + `STATE`（第 2 步）
4. 9 个工具函数（第 3 步，顺序无所谓，建议按 1~9 排）
5. `build_agent()`（第 4 步）
6. `main()` + `__main__` 守卫（第 5 步）

每一步的自检都过了再拼下一段。全部拼完、自检 ①~③ 全绿，就可以跑第 6 步看阿爪通关了。

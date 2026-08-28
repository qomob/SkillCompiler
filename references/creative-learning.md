# Creative Learning — Skill Mutation Loop（能力演进闭环）

**加载时机：** 📍 Creative Skill 运行期采集到真实反馈（accepted / rejected / human preference）且 `learning.enabled=true` 时加载；编译期 C3 配置 `learning` 字段时参考本文件。

**定位：** Memory ≠ Learning。记忆只**记录**（Failure Memory / Preference），学习要**改变能力**。本文件定义从反馈到 Skill 版本升级的完整闭环——Skill 从"静态文件"变成"会进化的能力"的分水岭。

***

## §1 Mutation Loop 全流程

```
Runtime Feedback（accepted / rejected / human preference L5 数据）
  ↓ ① Pattern 提取（≥ min_pattern_occurrences 次同类反馈才成模式）
  ↓ ② Preference Update（写入 memory.capture.user_preferences）
  ↓ ③ Capability Delta（诊断：哪条原则/权重/反例/套路参照系需要变）
  ↓ ④ Candidate Skill vNext（IR 增量修改提案 + 变更理由 + 反馈溯源）
  ↓ ⑤ Benchmark 回归（benchmark_runner.py：vNow vs vNext，golden-set.json）
  ↓ ⑥ Human Approval（人工审批——禁止静默升级）
  ↓ ⑦ Skill vNext 发布（版本号 +1，CHANGELOG 记录 delta）
```

**回路缺任何一环都不算学习：** 只有 ①② 是记忆；只有 ①-④ 是未经检验的自我修改（风险最高）；跳过 ⑤ 的升级是赌博；跳过 ⑥ 的升级是对 Skill 所有者的背叛。

***

## §2 各阶段规则

### ① Pattern 提取 — 单例不改规则

* `learning.mutation.min_pattern_occurrences`（默认 3）次**同类**反馈才允许触发规则变更——单次差评可能只是个案（同 AP-11 单轨迹过拟合：不基于单次运行经验调整编译策略）

* "同类"的判定按解析后的 symptom 聚类（如 genericPhraseTolerance / tooCommercial），不按用户原话字面

* 反馈必须先经 Preference 解析（creative-runtime.md §6：feedback → symptom → inferred preference → adjustment），原文不是数据

### ③ Capability Delta — 诊断先于修改

Mutation 提案必须回答四个问题，缺一即退回：

| 问题                    | 对应 IR 位置                                     |
| --------------------- | -------------------------------------------- |
| 哪个能力不足/过度？            | principles / heuristics / judgment.weighting |
| 证据是什么（≥3 次反馈 + 具体输出）？ | 反馈记录 + Candidate 产物                          |
| 改动会破坏什么？              | 受影响的 principles / fingerprint 基准             |
| 怎么证明改了更好？             | golden-set 回归预期                              |

### ④ Candidate Skill vNext — 增量提案格式

```json
{
  "from_version": "1.2.0",
  "to_version": "1.3.0",
  "deltas": [
    {
      "ir_path": "judgment.weighting.specificity",
      "from": 0.20, "to": 0.30,
      "reason": "3 次同类反馈：具体度不足被反复否决",
      "feedback_refs": ["fb-001", "fb-017", "fb-042"]
    }
  ],
  "expected_benchmark_effect": {"specificity": "+0.05~0.10", "style_fidelity": "不退化"}
}
```

约束：

* **fingerprint 不许通过 mutation 修改**——风格基准只随新语料（用 style\_analyzer.py 重测）变，不随反馈变。反馈说"太克制了"应产生 policy/weighting 的 delta，而不是偷偷挪基准

* 每条 delta 必须带 feedback\_refs（可溯源到真实反馈记录）

* **收紧容易放松难**：新增惩罚/反例的门槛低于删除惩罚——删除一条反例需要双倍反馈证据

### ⑤ Benchmark 回归 — 数据闸门

```bash
python3 scripts/benchmark_runner.py \
  --golden-set tests/golden-set.json \
  --runs runs/v1.2.0.json runs/v1.3.0.json \
  --report reports/regression-1.3.0.md
```

* vNext 在任何核心指标（style\_fidelity / novelty / revision\_gain）上相对 vNow 退化超过 0.05 → 拒绝本次 mutation

* "修了一个能力，毁掉另一个能力"是 skill 演进最常见的失败——回归不是可选项（`requires_benchmark` 默认 true，禁止关闭）

### ⑥ Human Approval — 所有权边界

* Skill 的原则/权重是所有者（创作者本人或品牌方）的创作意志体现，AI 只有提案权

* 审批输出三选一：approve（发布 vNext）/ reject（记录否决理由进 Failure Memory）/ revise（修改提案重走 ⑤）

* `requires_human_approval` 默认 true。禁止静默升级

***

## §3 与 Memory 的分工

| <br /> | Memory（记录层）                    | Learning（演进层）                    |
| ------ | ------------------------------ | -------------------------------- |
| 回答     | "发生过什么"                        | "下次该怎么变"                         |
| 产出     | Failure Memory / Preference 记录 | Skill vNext（IR delta + 版本号）      |
| 生效范围   | 单次运行（DIVERGE 降权 / JUDGE 惩罚）    | 永久（原则/权重/反例变更）                   |
| 门槛     | 无（记录本身无风险）                     | Pattern ≥3 + Benchmark 回归 + 人工审批 |
| IR 字段  | `memory`                       | `learning`                       |

`learning.enabled=false`（默认）时：反馈照常进 Memory，Mutation Loop 不触发——记录与演进解耦，演进是显式开启的严肃动作。

***

## §4 编译期（C3）的 learning 配置

C3 配置 `learning` 字段时：

1. 源材料若含持续性的偏好修正记录（≥3 次"同类否决"），开启 `enabled=true` 并预填 `feedback_capture`
2. `min_pattern_occurrences` 不低于 3；`requires_benchmark` / `requires_human_approval` 不允许设为 false（设了也会被 C5 判 CONDITIONAL）
3. 产物 runtime.md 中渲染 Mutation Loop 触发条件与审批接口（MEMORY\_UPDATE 状态的下游延伸）
4. 诚实边界声明：本 skill 的学习闭环依赖真实反馈量，反馈不足时 vNext 提案不会产生


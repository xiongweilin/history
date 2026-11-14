# 跨会话续写、提交和恢复操作手册（WORKFLOW.md）

## 一、唯一入口

仓库：https://github.com/xiongweilin/history

推荐新会话最简指令：

> 阅读 https://github.com/xiongweilin/history 中的 AGENTS.md、progress.json 和完整目录，按照现有规范继续讲下一国，并将完成的讲解提交回同一仓库。一次一国。

如果新会话已经打开并读取了本仓库，用户可以只说“继续”。若完全新开、没有仓库上下文，仓库本身不能触发自动访问，也不能赋予第三方GitHub写权限。

## 二、读取优先级

1. AGENTS.md — 写作与归档规则
2. progress.json — 唯一动态进度
3. data/countries.json — 固定国别序列与各国状态、标准路径
4. COUNTRY_INDEX.md — 人类可读目录
5. 00-阅读说明与目录.md — 统计口径和目录原则
6. 01—04号共同知识文件
7. 上一国的国家文件；若涉及直接历史联系再看前面相关国家
8. QUALITY_STANDARD.md — 发布前逐项核对

**不得用旧聊天、README或AI记忆覆盖较新的已核实GitHub状态。**

## 三、状态机

`data/countries.json.countries[*].status` 只采用：

- `pending`：尚未完成，没有正文路径（path 为 null）。
- `published`：已形成可读取的国家专题正文，实际文件存在并已提交。

**不使用“draft”充当完成进度。** 草稿可存在临时工作区或分支，但未合并至main时仍保持 pending。

`progress.json` 中：

- `total` 必须为195；
- `completed_count` 为已发布国家数量；
- `last_completed_rank` = completed_count；
- `next_rank` = completed_count + 1，全部完成后为 null；
- `completed` 逐国记录1—completed_count，路径真实存在；
- `next` 必须与 countries.json 中下一条一致；
- `updated_at` 是最后一次进度变更的日期，不是当前阅读日期。

## 四、单国发布事务

发布第N国之前：

1. 读取 `main` 最新版本，确认N国 pending。
2. 如果已经存在正文文件但状态 pending，先核查是否此前部分提交失败；修复而不是重复创建或跳号。
3. 撰写正文并查证资料；保持一定深度，用户尤其重视历史机制、前置解释及近现代部分。
4. 用可用GitHub连接器提交完整的 `countries/NNN-slug/README.md`。
5. 修改 countries.json、COUNTRY_INDEX.md、README.md 与 progress.json。
6. 运行验证：`python3 scripts/validate.py`；若无法运行脚本，至少人工执行与其等效的检查。
7. 重新获取 GitHub 文件/提交SHA，确认新的真实状态，最后再告知用户。
8. **发生任何失败，要保留准确现场和报告；不能先报“成功”后再尝试修复。**

写入顺序优先：国家正文 → 索引和countries.json → README → progress.json（最后），避免状态指向不存在的正文。支持原子多文件提交时可一次提交。

## 五、修订已发布历史

- 发现旧国家的事实错误，修订其正文，并解释影响（如从“301年确证建国”改为“301年建国传说”）。
- 旧国已发布状态不回退，除非正文确实丢失或不可用；这种情况应在用户确认后进行重大进度修复。
- 仅修订根目录共同知识、质量规则和参考资料，不增加已完成国家数量。
- 大范围重排195国必须有来源、变更计划与用户明确授权，否则保留固定序号。
- 不把二次整理的文章写成“对话原文字字一致”。

## 六、失败与并发冲突

如果本次会话没有GitHub权限：
- 可以在当前会话完成用户要求的内容；
- 明确说明无法回写仓库，提供完整可复制文档或补丁；
- `progress.json` 不得更新；
- 用户下次恢复时需先同步再推进。

如果同时有两段新会话开始“下一国”：
- 读取状态时二者可能都认为第N国 pending。
- 提交前再次读取 main 状态；若N国已 published，停止重复发布，并确认用户期望是否修改还是继续。
- 使用GitHub文件SHA或提交基线防止覆盖其他人的改动；遇到冲突重新读取文件，禁止强推。
- 不采用没有核验的盲目并行写入。

## 七、示例（不代表第008国已经开始）

当未来要发布第008国时，预计：

`countries/008-saint-kitts-and-nevis/README.md`

在文件真正提交成功前，`data/countries.json` 中第008国保持 pending，`path` 保持 null，`progress.json.next_rank` 仍为8；不得通过先创建空标题或占位文件来“打卡完成”。

## 八、发布后必须能回答的问题

- 当前已完成第几国？
- 下一国是哪个，为什么？
- 前置知识在哪里？
- 刚讲完的国家文件在哪里？
- 面积排名来源与统计口径是什么？
- 用户能否只阅读仓库而理解核心历史？
- GitHub上的正文、索引和状态是否全部一致？

若任一回答不明确，就不应声称实现了完全可接续。

# 投资分析工作台 Agent 化改造计划

## 已下载的开源项目

- 项目：`msitarzewski/agency-agents`
- 本地路径：`E:\codex\work\agency-agents`
- 性质：一套 agent 角色库，不是现成 Web 产品

## 适合本产品的 Agent 组合

1. Investment Researcher
   - 负责指数/赛道研究、牛熊逻辑、风险触发器
   - 来源：`E:\codex\work\agency-agents\finance\finance-investment-researcher.md`

2. Financial Analyst
   - 负责评分模型、情景分析、仓位建议、敏感性分析
   - 来源：`E:\codex\work\agency-agents\finance\finance-financial-analyst.md`

3. Data Engineer
   - 负责数据采集、清洗、质量检查、增量更新
   - 来源：`E:\codex\work\agency-agents\engineering\engineering-data-engineer.md`

4. Product Manager
   - 负责普通投资者使用流程、功能优先级、产品说明
   - 来源：`E:\codex\work\agency-agents\product\product-manager.md`

## 工作台应该怎么变

静态 HTML 原型要升级为真正的投资分析工作台，至少需要 5 个真实能力：

1. 数据源接入
   - 基金净值、费率、规模、成交额
   - 指数成分、权重、行业暴露
   - 宏观利率、通胀、PMI、信用周期

2. Agent 分析流程
   - Data Engineer 更新数据
   - Investment Researcher 生成赛道和指数研究
   - Financial Analyst 重算评分和仓位建议
   - Product Manager 把结果转成普通用户能执行的说明

3. 分析报告
   - 每个指数基金生成一份结构化报告
   - 包括长期逻辑、当前时点、风险点、仓位建议、同类比较

4. 组合检查
   - 检查用户已有持仓是否与半导体、AI、创业板等高度重叠
   - 给出“新增买入是否会过度集中”的判断

5. 更新与留痕
   - 每次数据更新后保存模型版本
   - 每次建议变化都记录原因
   - 允许回看历史判断是否有效

## 下一步开发顺序

1. 把当前静态页面拆成产品壳 + 数据 JSON
2. 建立 `data/` 目录，放入基金、指数、宏观、评分四类数据
3. 写评分引擎 `scoring.js`
4. 写半导体指数基金的第一份真实分析模板
5. 再接自动数据收集 skill

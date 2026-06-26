# 全国文宣行业信息化招投标监测看板系统

> CultureProcure Monitor — 实时追踪全国文化、旅游、体育、宣传领域的信息化采购动态

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Data Source](https://img.shields.io/badge/data%20source-ccgp.gov.cn-green.svg)](http://www.ccgp.gov.cn)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

## 项目简介

CultureProcure Monitor 是一个基于纯前端技术的招投标信息聚合与可视化监测平台，自动抓取中国政府采购网（ccgp.gov.cn）公开的采购公告，覆盖**文化、旅游、体育、宣传**四大行业的信息化建设项目。

系统提供多维度的数据筛选、统计分析、趋势可视化和数据导出功能，帮助行业从业者、研究人员和供应商及时掌握全国文宣领域的信息化采购动态。

## 核心功能

### 数据监测
- **349+ 条真实项目数据**，覆盖 31 个省份及 8 个国家部委
- 数据范围：2026 年 5 月至今（持续更新）
- 数据来源：中国政府采购网公开信息

### 六大可视化模块
| 模块 | 说明 |
|------|------|
| 总览驾驶舱 | KPI 指标卡 + 月度趋势图 + 行业分布 + 阶段分布 |
| 项目阶段看板 | 采购意向 → 招标公告 → 中标公示 → 合同签订 全流程追踪 |
| TOP100 榜单 | 按预算金额排序的头部项目，支持搜索/排序 |
| 31 省厅专区 | 按省份分组统计，可视化各省采购热度 |
| 头部委专区 | 文旅部、广电总局、文物局等 8 个部委专项追踪 |
| 信息化专项 | IT 项目类型分类分析（智慧平台/大数据/融媒体等） |

### 数据操作
- **多维筛选**：省份 / 时间 / 行业 / 阶段 / IT 类型联动过滤
- **表格交互**：列排序、关键词搜索、分页浏览
- **项目详情**：侧滑面板展示完整采购信息
- **Excel 导出**：一键导出当前筛选结果（SheetJS）
- **Chart.js 图表**：趋势曲线、饼图、柱状图

## 技术架构

```
┌─────────────────────────────────────────────────┐
│                  dashboard.html                  │
│              (单页应用 · 1468 行)                  │
├────────────┬────────────┬───────────────────────┤
│  Chart.js  │  SheetJS   │  Vanilla JavaScript   │
│  (CDN)     │  (CDN)     │  (原生 JS · 无框架)    │
├────────────┴────────────┴───────────────────────┤
│               ccgp_data.json                     │
│          (349 条项目 · JSON 格式)                 │
├──────────────────────────────────────────────────┤
│              scripts/ (Python)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ crawler  │→│  sync    │→│ build_enriched   │ │
│  │ (采集)   │ │ (合并)    │ │ (增强+统计)       │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
└──────────────────────────────────────────────────┘
```

**技术栈**：HTML5 + CSS3 + 原生 JavaScript + Chart.js 4 + SheetJS + Python 3

## 快速开始

### 方式一：直接打开
```bash
# 克隆仓库
git clone https://github.com/songweilovelj-cyber/culture-procurement-monitor.git
cd culture-procurement-monitor

# 用浏览器打开 dashboard.html 即可使用
# 推荐 Chrome / Edge 浏览器
```

### 方式二：本地服务器（推荐）
```bash
# Python 3
python -m http.server 8080

# 或 Node.js
npx serve

# 然后访问 http://localhost:8080
```

> **注意**：使用 `file://` 协议直接打开时，部分浏览器可能阻止 `fetch` 加载本地 JSON。建议使用本地服务器方式。

## 数据更新

项目内置的数据截至 2026 年 6 月。如需更新数据，运行以下脚本：

```bash
cd scripts

# 1. 数据采集（需要网络访问 ccgp.gov.cn）
python crawler_ccgp_safe.py

# 2. 数据同步合并
python sync_ccgp_data.py

# 3. 数据增强（补充中标单位、预算金额等）
python build_enriched_data.py
```

详细的数据结构说明见 [数据格式文档](docs/DATA_FORMAT.md)。

## 项目结构

```
culture-procurement-monitor/
├── dashboard.html              # 主应用（单页 HTML）
├── ccgp_data.json              # 项目数据（349 条）
├── scripts/
│   ├── crawler_ccgp_safe.py    # 政府采购网爬虫（低频安全版）
│   ├── sync_ccgp_data.py       # 数据同步合并工具
│   ├── build_enriched_data.py  # 数据增强脚本
│   └── merge_may_data.py       # 历史数据合并工具
├── .github/
│   ├── ISSUE_TEMPLATE/         # Issue 模板
│   └── PULL_REQUEST_TEMPLATE.md
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── LICENSE
└── .gitignore
```

## 数据字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 项目唯一标识 |
| `title` | string | 公告标题 |
| `url` | string | 原始公告链接 |
| `industry` | string | 行业分类（文化/旅游/体育/宣传） |
| `province` | string | 省份（含"部委"） |
| `phase` | string | 采购阶段（采购意向/招标公告/中标公示/合同签订） |
| `budget` | float\|null | 预算金额（万元） |
| `agency` | string | 采购单位 |
| `agent` | string | 代理机构 |
| `date` | string | 发布日期 (YYYY-MM-DD) |
| `isIT` | boolean | 是否为信息化项目 |
| `itType` | string | IT 类型分类 |
| `isMinistry` | boolean | 是否为部委项目 |
| `winner` | string\|null | 中标单位 |

## 截图预览

系统采用深蓝商务配色（navy-900 → navy-700 渐变 + 金色 #c9a96e 点缀），PC 端宽屏布局，包含：

- 顶部导航栏（品牌标识 + 数据状态 + 导出按钮）
- 六标签页切换
- 左侧多维筛选栏
- 主内容区（KPI 卡片 / 图表 / 数据表格）
- 右侧滑项目详情面板

## 开源协议

本项目基于 [MIT License](LICENSE) 开源，可自由使用、修改和分发。

数据来源为中国政府采购网公开信息，版权归原作者所有。

## 贡献指南

欢迎提交 Issue 和 Pull Request！请阅读 [贡献指南](CONTRIBUTING.md) 了解详情。

## 致谢

- [Chart.js](https://chartjs.org/) — 数据可视化
- [SheetJS](https://sheetjs.com/) — Excel 导出
- [中国政府采购网](http://www.ccgp.gov.cn/) — 数据来源

---

<p align="center">Made with care for the cultural sector</p>

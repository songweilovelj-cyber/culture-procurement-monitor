# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-26

### Added
- Initial public release
- Dashboard application with 6 visualization modules:
  - Overview cockpit (KPI cards + trend charts)
  - Project phase kanban (procurement lifecycle tracking)
  - TOP100 ranking (budget-sorted project list)
  - 31-province dashboard (regional procurement analysis)
  - 8-ministry dashboard (national-level tracking)
  - IT specialization analysis (technology type breakdown)
- Multi-dimensional filtering system (province / time / industry / phase / IT type)
- Interactive data table with column sorting, keyword search, and pagination
- Project detail slide-out panel
- Excel export functionality (SheetJS)
- Chart.js trend visualization (line / pie / bar charts)
- 349 real project records from ccgp.gov.cn
- Data coverage: 31 provinces + 8 national ministries
- Time range: May 2026 – June 2026
- Python crawler scripts for data collection:
  - `crawler_ccgp_safe.py` — low-frequency safe crawler with 8-15s delays
  - `sync_ccgp_data.py` — URL-based dedup merge tool
  - `build_enriched_data.py` — data enrichment with verified budget/winner data
  - `merge_may_data.py` — historical data batch merge tool
- Deep blue business theme (navy gradient + gold accents)
- Responsive PC widescreen layout (min-width 1366px)
- Defensive rendering with multi-layer error recovery
- Seed data fallback for offline resilience

### Technical Details
- Pure frontend application (HTML5 + CSS3 + Vanilla JS)
- 1,468 lines of code in dashboard.html
- 31 JavaScript functions
- External dependencies: Chart.js 4.4.1, SheetJS 0.18.5 (CDN)
- Data file: ccgp_data.json (~218KB, 349 projects)
- 100% IT project classification accuracy
- 27 projects with verified budget amounts
- 39 projects with confirmed winning bidders

### Data Sources
- China Government Procurement Website (www.ccgp.gov.cn)
- 7 keyword search categories: 智慧文旅, 文化数字化, 体育信息化, 融媒体平台, 智慧旅游系统, 文物数字化, 广电信息化
- 4 detail page extractions for precise budget/winner verification

# 贡献指南

感谢你对 CultureProcure Monitor 项目的关注！欢迎以任何方式参与贡献。

## 如何贡献

### 报告问题

如果发现 Bug 或有功能建议，请 [提交 Issue](https://github.com/songweilovelj-cyber/culture-procurement-monitor/issues/new/choose)，选择对应模板：

- **Bug 报告**：描述问题、复现步骤、预期行为、实际行为
- **功能建议**：描述需求场景、期望效果

### 提交代码

1. **Fork** 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature-name`
3. 提交更改：`git commit -m 'feat: add some feature'`
4. 推送分支：`git push origin feature/your-feature-name`
5. 提交 **Pull Request**

### 提交规范

请遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 代码重构 |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具变更 |

示例：
```
feat: add provincial heatmap visualization
fix: resolve chart rendering on Safari 17
docs: update data field documentation
```

### 代码风格

#### JavaScript / HTML
- 使用 2 空格缩进
- 函数和变量命名使用 camelCase
- 常量使用 UPPER_SNAKE_CASE
- 添加必要的注释说明复杂逻辑
- 防御性编程：对 DOM 操作进行 null 检查

#### Python
- 遵循 PEP 8 规范
- 使用 UTF-8 编码
- 添加 docstring 说明函数用途
- 爬虫脚本必须包含合理的请求间隔（≥ 8 秒）

### 数据贡献

如发现数据缺失或有更准确的信息（预算金额、中标单位等），欢迎提交 PR 更新 `ccgp_data.json`：

1. 确保数据来源为 ccgp.gov.cn 公开信息
2. 验证 URL 唯一性（避免重复）
3. 保持 JSON 格式一致性
4. 在 PR 中说明数据来源和验证方式

### 开发环境

```bash
# 克隆仓库
git clone https://github.com/songweilovelj-cyber/culture-procurement-monitor.git
cd culture-procurement-monitor

# 启动本地服务器
python -m http.server 8080

# 在浏览器中访问
# http://localhost:8080
```

**环境要求**：
- Python 3.8+（运行脚本）
- 现代浏览器（Chrome 90+ / Edge 90+ / Firefox 88+）

### PR 检查清单

提交 PR 前，请确认：

- [ ] 代码已本地测试通过
- [ ] 没有引入新的外部依赖（除 CDN 资源外）
- [ ] HTML 文件可通过浏览器直接打开运行
- [ ] 数据格式与现有结构一致
- [ ] 提交信息符合 Conventional Commits 规范
- [ ] 如果是新功能，已在 CHANGELOG.md 中记录

## 项目维护者

- [@songweilovelj-cyber](https://github.com/songweilovelj-cyber)

## 行为准则

参与本项目即表示你同意遵守 [行为准则](CODE_OF_CONDUCT.md)。请保持友善和尊重。

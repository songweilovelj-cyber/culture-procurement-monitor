const state = {
  data: null,
  portfolio: null,
  portfolioMeta: null,
  selectedId: "semiconductor",
  query: "",
  activeTab: "overview"
};

const el = {
  tabButtons: Array.from(document.querySelectorAll(".tab-btn")),
  views: Array.from(document.querySelectorAll(".view")),
  horizon: document.getElementById("horizonRange"),
  risk: document.getElementById("riskRange"),
  horizonText: document.getElementById("horizonText"),
  riskText: document.getElementById("riskText"),
  freshness: document.getElementById("freshness"),
  search: document.getElementById("searchInput"),
  themeList: document.getElementById("themeList"),
  selectedCategory: document.getElementById("selectedCategory"),
  selectedName: document.getElementById("selectedName"),
  selectedRole: document.getElementById("selectedRole"),
  actionText: document.getElementById("actionText"),
  positionText: document.getElementById("positionText"),
  scoreGrid: document.getElementById("scoreGrid"),
  rationale: document.getElementById("rationale"),
  reviewCadence: document.getElementById("reviewCadence"),
  fundRows: document.getElementById("fundRows"),
  fundCountTag: document.getElementById("fundCountTag"),
  overlapList: document.getElementById("overlapList"),
  overlapSummary: document.getElementById("overlapSummary"),
  overlapRiskTag: document.getElementById("overlapRiskTag"),
  warningList: document.getElementById("warningList"),
  triggerList: document.getElementById("triggerList"),
  sourceList: document.getElementById("sourceList"),
  macroBox: document.getElementById("macroBox"),
  updateButton: document.getElementById("updateButton"),
  updateStatus: document.getElementById("updateStatus"),
  portfolioSourceTag: document.getElementById("portfolioSourceTag"),
  portfolioSummary: document.getElementById("portfolioSummary"),
  holdingEditorRows: document.getElementById("holdingEditorRows"),
  addHoldingButton: document.getElementById("addHoldingButton"),
  savePortfolioButton: document.getElementById("savePortfolioButton"),
  resetPortfolioButton: document.getElementById("resetPortfolioButton"),
  portfolioStatus: document.getElementById("portfolioStatus"),
  portfolioRows: document.getElementById("portfolioRows"),
  portfolioWeightTag: document.getElementById("portfolioWeightTag")
};

function params() {
  return new URLSearchParams({
    horizon: el.horizon.value,
    risk: el.risk.value
  });
}

async function loadDashboard() {
  const response = await fetch(`/api/dashboard?${params().toString()}`);
  state.data = await response.json();
  if (!state.data.evaluations.some(item => item.id === state.selectedId)) {
    state.selectedId = state.data.evaluations[0]?.id;
  }
  render();
}

async function loadPortfolio() {
  const response = await fetch("/api/portfolio");
  state.portfolio = await response.json();
  state.portfolioMeta = state.portfolio;
}

function selected() {
  return state.data.evaluations.find(item => item.id === state.selectedId) || state.data.evaluations[0];
}

function riskLabel(value) {
  const risk = Number(value);
  if (risk <= 3) return "保守";
  if (risk <= 7) return "中等";
  return "激进";
}

function actionClass(action) {
  if (["正常买入", "加速分批", "分批买入"].includes(action)) return "good";
  if (["小额试探", "等待回落"].includes(action)) return "warn";
  return "bad";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderThemeList() {
  const q = state.query.trim().toLowerCase();
  const items = state.data.evaluations.filter(item => {
    return !q || item.name.toLowerCase().includes(q) || item.category.toLowerCase().includes(q) || item.role.toLowerCase().includes(q);
  });
  el.themeList.innerHTML = items.map(item => `
    <button class="theme-card ${item.id === state.selectedId ? "active" : ""}" data-id="${item.id}">
      <strong>${escapeHtml(item.name)}</strong>
      <span>${item.role} · ${item.riskLevel}风险 · ${item.matchedFundCount} 只 · <b>${item.action}</b></span>
    </button>
  `).join("") || `<div class="theme-card"><span>没有找到匹配主题</span></div>`;
}

function setActiveTab(tab) {
  state.activeTab = tab;
  el.tabButtons.forEach(button => {
    const active = button.dataset.tab === tab;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
  el.views.forEach(view => {
    const active = view.dataset.view === tab;
    view.hidden = !active;
    view.classList.toggle("active", active);
  });
}

function renderDecision(item) {
  el.selectedCategory.textContent = `${item.category} · ${item.role} · ${item.riskLevel}风险`;
  el.selectedName.textContent = item.name;
  el.selectedRole.textContent = `当前持仓 ${item.position.currentWeight}%；建议上限 ${item.position.maxWeight}%。`;
  el.actionText.textContent = item.action;
  el.actionText.className = actionClass(item.action);
  el.positionText.textContent = item.position.text;
  el.reviewCadence.textContent = item.nextReview;
}

function renderScores(item) {
  const cards = [
    ["总分", item.scores.total, "综合长期、时点、产品和组合适配"],
    ["长期结构", item.scores.longTerm, "指数质量、长期逻辑、政策支持"],
    ["当前时点", item.scores.timing, "估值、拥挤度、宏观环境"],
    ["产品执行", item.scores.product, "费率、跟踪误差、规模与流动性"],
    ["组合适配", item.scores.portfolioFit, "是否和已有持仓过度重叠"],
    ["估值舒适", item.scores.valuationComfort, "越高代表越舒服"],
    ["拥挤度", item.scores.crowding, "越高越不适合追买"],
    ["波动风险", item.scores.volatilityRisk, "越高越需要控制仓位"]
  ];
  el.scoreGrid.innerHTML = cards.map(([label, value, desc]) => `
    <div class="score-card">
      <span>${label}</span>
      <strong>${value}</strong>
      <p>${desc}</p>
    </div>
  `).join("");
}

function renderReport(item) {
  el.rationale.innerHTML = item.rationale.map(text => `<div>${text}</div>`).join("");
  el.warningList.innerHTML = item.warnings.map(text => `<div>${text}</div>`).join("");
  el.triggerList.innerHTML = item.thesis.triggers.map(text => `<div>${text}</div>`).join("");
}

function renderFunds(item) {
  el.fundCountTag.textContent = `已匹配 ${item.matchedFundCount} 只`;
  el.fundRows.innerHTML = item.funds.map(fund => `
    <tr>
      <td>${fund.name}</td>
      <td>${fund.code}</td>
      <td>${fund.fee.toFixed(2)}%</td>
      <td>${fund.trackingError.toFixed(2)}%</td>
      <td><span class="pill ${fund.productScore >= 80 ? "good" : "warn"}">${fund.productScore}</span></td>
      <td>${fund.fit}</td>
    </tr>
  `).join("");
}

function portfolioThemeName(themeId) {
  return state.data?.evaluations.find(item => item.id === themeId)?.name || themeId || "-";
}

function portfolioSourceLabel(source) {
  if (source === "user") return "用户持仓";
  if (source === "sample") return "样例组合";
  return "未知";
}

function normalizePortfolioHoldings(holdings) {
  const cleaned = holdings
    .map(holding => ({
      name: String(holding.name || "").trim(),
      theme: String(holding.theme || "").trim(),
      amount: Number(holding.amount || 0),
      weight: Number(holding.weight || 0)
    }))
    .filter(holding => holding.name && holding.theme && (holding.amount > 0 || holding.weight > 0));
  const totalAmount = cleaned.reduce((sum, holding) => sum + Math.max(0, holding.amount), 0);
  if (totalAmount > 0) {
    return cleaned.map(holding => ({
      name: holding.name,
      theme: holding.theme,
      amount: holding.amount,
      weight: Number(((holding.amount / totalAmount) * 100).toFixed(2))
    }));
  }
  return cleaned;
}

function themeOptions(selectedTheme) {
  const options = [
    ...(state.data?.evaluations || []).map(item => ({ id: item.id, name: item.name })),
    { id: "cash", name: "现金/货币基金" }
  ];
  return options.map(option => `
    <option value="${escapeHtml(option.id)}" ${option.id === selectedTheme ? "selected" : ""}>${escapeHtml(option.name)}</option>
  `).join("");
}

function amountFromHolding(holding) {
  if (Number(holding.amount) > 0) return Number(holding.amount);
  return Number(holding.weight || 0);
}

function readHoldingsFromEditor() {
  return Array.from(el.holdingEditorRows.querySelectorAll(".holding-row")).map(row => ({
    name: row.querySelector("[data-field='name']").value,
    theme: row.querySelector("[data-field='theme']").value,
    amount: Number(row.querySelector("[data-field='amount']").value || 0)
  }));
}

function renderHoldingEditor(holdings) {
  el.holdingEditorRows.innerHTML = holdings.map((holding, index) => {
    const amount = amountFromHolding(holding);
    return `
      <div class="holding-row" data-index="${index}">
        <label>
          <span>基金名称</span>
          <input data-field="name" value="${escapeHtml(holding.name || "")}" placeholder="例如：沪深300ETF" />
        </label>
        <label>
          <span>主题映射</span>
          <select data-field="theme">${themeOptions(holding.theme)}</select>
        </label>
        <label>
          <span>金额/市值</span>
          <input data-field="amount" type="number" min="0" step="100" value="${amount}" />
        </label>
        <div class="holding-weight">
          <span>仓位</span>
          <strong data-field="weight">${Number(holding.weight || 0).toFixed(1)}%</strong>
        </div>
        <button class="icon-button danger" type="button" data-action="delete-holding" aria-label="删除持仓">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M4 7h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M10 11v6M14 11v6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M6 7l1 14h10l1-14M9 7V4h6v3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    `;
  }).join("");
  updatePortfolioDraftPreview();
}

function addHoldingRow(holding = { name: "", theme: "csi300", amount: 0 }) {
  const holdings = readHoldingsFromEditor();
  holdings.push(holding);
  renderHoldingEditor(normalizePortfolioHoldings(holdings).concat(
    holding.name ? [] : [holding]
  ));
}

function updatePortfolioDraftPreview() {
  const holdings = normalizePortfolioHoldings(readHoldingsFromEditor());
  const totalAmount = holdings.reduce((sum, holding) => sum + Number(holding.amount || 0), 0);
  el.holdingEditorRows.querySelectorAll(".holding-row").forEach((row, index) => {
    const amount = Number(row.querySelector("[data-field='amount']").value || 0);
    const weight = totalAmount > 0 ? (amount / totalAmount) * 100 : 0;
    row.querySelector("[data-field='weight']").textContent = `${weight.toFixed(1)}%`;
  });
  renderPortfolioSummary(holdings);
  renderPortfolioRows(holdings);
  el.portfolioStatus.textContent = `待保存：${holdings.length} 条 · ${holdings.reduce((sum, holding) => sum + holding.weight, 0).toFixed(1)}%`;
}

function renderPortfolioSummary(holdings) {
  const totalWeight = holdings.reduce((sum, holding) => sum + Number(holding.weight || 0), 0);
  const totalAmount = holdings.reduce((sum, holding) => sum + Number(holding.amount || 0), 0);
  const maxHolding = holdings.reduce((top, holding) => (Number(holding.weight || 0) > Number(top?.weight || 0) ? holding : top), null);
  el.portfolioWeightTag.textContent = `${totalWeight.toFixed(1)}%`;
  el.portfolioSummary.innerHTML = `
    <div class="mini-stat"><span>持仓数量</span><strong>${holdings.length}</strong><p>记录的基金仓位条目</p></div>
    <div class="mini-stat"><span>总金额</span><strong>${totalAmount.toLocaleString("zh-CN")}</strong><p>用于自动换算仓位比例</p></div>
    <div class="mini-stat"><span>最大持仓</span><strong>${maxHolding ? escapeHtml(maxHolding.name) : "-"}</strong><p>${maxHolding ? `${Number(maxHolding.weight).toFixed(1)}%` : "暂无持仓"}</p></div>
  `;
}

function renderPortfolioRows(holdings) {
  el.portfolioRows.innerHTML = holdings.length
    ? holdings.map(holding => `
      <tr>
        <td>${escapeHtml(holding.name)}</td>
        <td>${escapeHtml(portfolioThemeName(holding.theme))}</td>
        <td>${Number(holding.amount || 0).toLocaleString("zh-CN")}</td>
        <td>${Number(holding.weight).toFixed(1)}%</td>
      </tr>
    `).join("")
    : `<tr><td colspan="4">暂无持仓，先添加一条基金持仓。</td></tr>`;
}

function currentPortfolioHoldings() {
  const portfolio = state.portfolio?.portfolio || state.portfolio || {};
  return Array.isArray(portfolio.holdings) ? portfolio.holdings : [];
}

function renderPortfolio() {
  const portfolio = state.portfolio?.portfolio || state.portfolio || {};
  const holdings = normalizePortfolioHoldings(currentPortfolioHoldings());
  const source = state.portfolio?.source || portfolio.source || "sample";
  el.portfolioSourceTag.textContent = portfolioSourceLabel(source);
  renderHoldingEditor(holdings);
  renderPortfolioSummary(holdings);
  renderPortfolioRows(holdings);
  el.portfolioStatus.textContent = state.portfolio?.holdingsCount != null
    ? `当前为 ${portfolioSourceLabel(source)} · ${state.portfolio.holdingsCount} 条`
    : "修改金额后点击保存，模型会重新计算。";
}

function overlapRisk(rows) {
  const max = Math.max(0, ...rows.map(row => Number(row.overlap) || 0));
  if (max >= 60) {
    return {
      label: "重叠偏高",
      className: "bad",
      advice: "新增买入前，先降低已有相似主题或核心宽基的重复暴露。"
    };
  }
  if (max >= 35) {
    return {
      label: "重叠中等",
      className: "warn",
      advice: "可以买，但更适合作为小额分批或替换配置，避免同类主题越买越集中。"
    };
  }
  return {
    label: "重叠较低",
    className: "good",
    advice: "与当前组合重复度不高，仓位决策主要看估值、宏观和波动承受能力。"
  };
}

function renderOverlap(item) {
  const rows = item.holdingsOverlap || [];
  const risk = overlapRisk(rows);
  const top = [...rows].sort((a, b) => b.overlap - a.overlap)[0];
  el.overlapRiskTag.textContent = risk.label;
  el.overlapRiskTag.className = `tag ${risk.className}`;
  el.overlapSummary.innerHTML = `
    <div>
      <span>这个模块看什么</span>
      <strong>买入 ${item.name} 后，组合是否会更集中</strong>
      <p>它不是收益预测，而是用来判断你是不是在不同基金名字下反复买同一种风险。</p>
    </div>
    <div>
      <span>当前结论</span>
      <strong>${top ? `与「${top.name}」重叠最高，为 ${top.overlap}%` : "暂无明显重叠"}</strong>
      <p>${risk.advice}</p>
    </div>
  `;
  el.overlapList.innerHTML = rows.map(row => `
    <div class="bar">
      <div class="bar-row"><span>${row.name}</span><strong>${row.overlap}%</strong></div>
      <div class="track"><div class="fill" style="width:${row.overlap}%"></div></div>
    </div>
  `).join("");
}

function renderSources() {
  el.sourceList.innerHTML = state.data.dataSources.map(source => `
    <div>
      <b>${source.name}</b><br />
      ${source.cadence} · ${source.freshness} · 当前状态：${source.status}${source.count ? ` · ${source.count} 条` : ""}
    </div>
  `).join("");
}

function renderMacro() {
  const macro = state.data.macro;
  el.macroBox.innerHTML = `
    <div class="macro-hero">
      <span>当前判定 · 置信度 ${macro.confidence}</span>
      <strong>${macro.label}</strong>
    </div>
    <ul>${macro.explanation.reasons.map(reason => `<li>${reason}</li>`).join("")}</ul>
  `;
}

function renderHeader() {
  el.horizonText.textContent = `${el.horizon.value} 年`;
  el.riskText.textContent = riskLabel(el.risk.value);
  el.freshness.textContent = `数据：${new Date(state.data.asOf).toLocaleString("zh-CN", { hour12: false })}`;
}

function render() {
  if (!state.data) return;
  const item = selected();
  renderHeader();
  renderThemeList();
  renderDecision(item);
  renderScores(item);
  renderReport(item);
  renderFunds(item);
  renderOverlap(item);
  renderSources();
  renderMacro();
  renderPortfolio();
  setActiveTab(state.activeTab);
}

el.themeList.addEventListener("click", event => {
  const button = event.target.closest("[data-id]");
  if (!button) return;
  state.selectedId = button.dataset.id;
  render();
});

el.search.addEventListener("input", () => {
  state.query = el.search.value;
  renderThemeList();
});

[...el.tabButtons].forEach(button => {
  button.addEventListener("click", () => {
    setActiveTab(button.dataset.tab);
  });
});

[el.horizon, el.risk].forEach(input => {
  input.addEventListener("input", loadDashboard);
});

el.addHoldingButton.addEventListener("click", () => {
  addHoldingRow();
  el.portfolioStatus.textContent = "已添加空白持仓，填写名称、主题和金额后保存。";
});

el.holdingEditorRows.addEventListener("input", event => {
  if (event.target.matches("input, select")) {
    updatePortfolioDraftPreview();
  }
});

el.holdingEditorRows.addEventListener("change", event => {
  if (event.target.matches("select")) {
    updatePortfolioDraftPreview();
  }
});

el.holdingEditorRows.addEventListener("click", event => {
  const button = event.target.closest("[data-action='delete-holding']");
  if (!button) return;
  button.closest(".holding-row").remove();
  updatePortfolioDraftPreview();
  el.portfolioStatus.textContent = "已删除一条持仓，保存后生效。";
});

el.savePortfolioButton.addEventListener("click", async () => {
  try {
    const holdings = normalizePortfolioHoldings(readHoldingsFromEditor());
    if (!holdings.length) {
      throw new Error("至少保留一条有效持仓");
    }
    el.savePortfolioButton.disabled = true;
    el.savePortfolioButton.classList.add("loading");
    el.portfolioStatus.textContent = "保存中：正在写入本地持仓...";
    const payload = {
      userType: state.portfolio?.portfolio?.userType || "普通长期投资者",
      targetHorizonYears: Number(el.horizon.value),
      riskTolerance: Number(el.risk.value),
      holdings
    };
    const response = await fetch("/api/portfolio", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || result.message || "保存失败");
    }
    el.portfolioStatus.textContent = `保存成功：${result.holdingsCount} 条，${result.totalWeight.toFixed(1)}%。`;
    await loadPortfolio();
    await loadDashboard();
    setActiveTab("portfolio");
  } catch (error) {
    el.portfolioStatus.textContent = `导入失败：${error.message}`;
  } finally {
    el.savePortfolioButton.disabled = false;
    el.savePortfolioButton.classList.remove("loading");
  }
});

el.resetPortfolioButton.addEventListener("click", async () => {
  el.resetPortfolioButton.disabled = true;
  el.portfolioStatus.textContent = "恢复中：正在清除用户持仓并回到样例组合...";
  try {
    const response = await fetch("/api/portfolio", { method: "DELETE" });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || result.message || "恢复失败");
    }
    el.portfolioStatus.textContent = "已恢复样例组合。";
    await loadPortfolio();
    await loadDashboard();
  } catch (error) {
    el.portfolioStatus.textContent = `恢复失败：${error.message}`;
  } finally {
    el.resetPortfolioButton.disabled = false;
  }
});

el.updateButton.addEventListener("click", async () => {
  el.updateButton.disabled = true;
  el.updateButton.classList.add("loading");
  el.updateStatus.textContent = "更新中：正在抓取基金库并重建主题数据...";
  try {
    const response = await fetch("/api/update-data", { method: "POST" });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error?.message || payload.message || "数据更新失败");
    }
    const result = payload.result;
    el.updateStatus.textContent = `更新完成：指数基金 ${result.indexFundCount} 只，主题 ${result.themeCount} 个。`;
    await loadDashboard();
  } catch (error) {
    el.updateStatus.textContent = `更新失败：${error.message}`;
  } finally {
    el.updateButton.disabled = false;
    el.updateButton.classList.remove("loading");
  }
});

await loadPortfolio();
await loadDashboard();

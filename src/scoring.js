const clamp = (value, min = 0, max = 100) => Math.max(min, Math.min(max, value));
const round = (value) => Math.round(value);

export function scoreFundProduct(product) {
  const feeScore = clamp(100 - product.fee * 80);
  const trackingScore = clamp(100 - product.trackingError * 160);
  return round(feeScore * 0.35 + trackingScore * 0.35 + product.liquidity * 0.2 + product.aumScore * 0.1);
}

export function evaluateFundTheme(theme, market, portfolio, options = {}) {
  const regimeKey = options.regime || "neutral";
  const horizon = Number(options.horizon || portfolio.targetHorizonYears || 5);
  const risk = Number(options.risk || portfolio.riskTolerance || 5);
  const regime = market.macroRegimes[regimeKey] || market.macroRegimes.neutral;
  const s = theme.scores;

  const longTermScore = clamp(
    s.longTermThesis * 0.34 +
      s.indexQuality * 0.22 +
      s.policySupport * 0.14 +
      s.executionQuality * 0.14 +
      s.costEfficiency * 0.1 +
      s.portfolioFit * 0.06 +
      (horizon - 5) * 1.2
  );

  const macroAdjustment =
    regime.riskAppetite * (s.macroSensitivity / 100) -
    regime.durationPressure * ((s.macroSensitivity - 50) / 100) +
    regime.cyclicalSupport * (theme.category.includes("主题") ? 0.8 : 0.25) +
    regime.dividendSupport * (theme.id.includes("dividend") ? 1 : 0);

  const timingScore = clamp(
    s.valuationComfort * 0.34 +
      (100 - s.crowding) * 0.22 +
      (100 - s.volatilityRisk) * 0.14 +
      s.policySupport * 0.12 +
      s.executionQuality * 0.08 +
      58 * 0.1 +
      macroAdjustment +
      (risk - 5) * 1.1
  );

  const bestFundScore = Math.max(...theme.funds.map(scoreFundProduct));
  const portfolioWeight = portfolio.holdings
    .filter((holding) => holding.theme === theme.id)
    .reduce((sum, holding) => sum + holding.weight, 0);
  const relatedTechWeight = portfolio.holdings
    .filter((holding) => ["ai", "semiconductor"].includes(holding.theme))
    .reduce((sum, holding) => sum + holding.weight, 0);

  const overlapPenalty =
    theme.role === "卫星仓"
      ? Math.max(0, relatedTechWeight - 18) * 0.7 + Math.max(0, portfolioWeight - 12) * 0.9
      : Math.max(0, portfolioWeight - 45) * 0.4;

  const portfolioFitScore = clamp(s.portfolioFit - overlapPenalty + (theme.role.includes("核心") ? 8 : 0));

  const totalScore = clamp(
    longTermScore * 0.42 +
      timingScore * 0.28 +
      bestFundScore * 0.18 +
      portfolioFitScore * 0.12
  );

  const action = decideAction(totalScore, longTermScore, timingScore, theme, risk);
  const position = decidePosition(action, theme, risk, portfolioWeight);
  const nextReview = decideReviewCadence(action, theme);

  return {
    id: theme.id,
    name: theme.name,
    category: theme.category,
    role: theme.role,
    riskLevel: theme.riskLevel,
    matchedFundCount: theme.matchedFundCount || theme.funds.length,
    scores: {
      total: round(totalScore),
      longTerm: round(longTermScore),
      timing: round(timingScore),
      product: round(bestFundScore),
      portfolioFit: round(portfolioFitScore),
      valuationComfort: s.valuationComfort,
      crowding: s.crowding,
      volatilityRisk: s.volatilityRisk
    },
    action,
    position,
    nextReview,
    currentWeight: portfolioWeight,
    relatedTechWeight,
    thesis: theme.thesis,
    holdingsOverlap: theme.holdingsOverlap,
    funds: theme.funds.map((fund) => ({
      ...fund,
      productScore: scoreFundProduct(fund)
    })).sort((a, b) => b.productScore - a.productScore),
    rationale: buildRationale(theme, action, longTermScore, timingScore, portfolioFitScore, regime),
    warnings: buildWarnings(theme, timingScore, portfolioFitScore, portfolioWeight, relatedTechWeight)
  };
}

function decideAction(total, longTerm, timing, theme, risk) {
  if (longTerm < 62) return "回避";
  if (total >= 84 && timing >= 72) return theme.role === "卫星仓" ? "加速分批" : "正常买入";
  if (total >= 74) return "分批买入";
  if (total >= 62) return risk >= 7 ? "小额试探" : "等待回落";
  return "先观望";
}

function decidePosition(action, theme, risk, currentWeight) {
  const satelliteCap = risk >= 8 ? 18 : risk >= 5 ? 12 : 8;
  const coreCap = risk >= 8 ? 60 : risk >= 5 ? 48 : 36;
  const cap = theme.role === "卫星仓" ? satelliteCap : coreCap;
  const room = Math.max(0, cap - currentWeight);
  const add = {
    "正常买入": Math.min(room, 12),
    "加速分批": Math.min(room, 8),
    "分批买入": Math.min(room, 5),
    "小额试探": Math.min(room, 2),
    "等待回落": 0,
    "先观望": 0,
    "回避": 0
  }[action] ?? 0;

  return {
    currentWeight,
    suggestedAdd: round(add * 10) / 10,
    maxWeight: cap,
    text: add > 0 ? `新增 ${round(add * 10) / 10}% 以内，分 4-8 次完成` : "不建议新增，保留观察"
  };
}

function decideReviewCadence(action, theme) {
  if (["先观望", "等待回落"].includes(action)) return "每周复查估值和拥挤度";
  if (theme.role === "卫星仓") return "每两周复查仓位和主题热度";
  return "每月复查一次即可";
}

function buildRationale(theme, action, longTerm, timing, portfolioFit, regime) {
  return [
    `长期结构分 ${round(longTerm)}：${theme.role}属性明确，长期逻辑主要来自 ${theme.thesis.bull[0]}`,
    `当前时点分 ${round(timing)}：宏观环境为「${regime.label}」，模型没有把它当作一次性重仓信号。`,
    `组合适配分 ${round(portfolioFit)}：主题仓需要看和已有 AI、科技、宽基持仓的重叠。`,
    `行动建议为「${action}」：产品优先控制买入节奏，而不是预测短期涨跌。`
  ];
}

function buildWarnings(theme, timing, portfolioFit, currentWeight, relatedTechWeight) {
  const warnings = [...theme.thesis.bear];
  if (timing < 60) warnings.unshift("当前买点舒适度不高，新增仓位应慢。");
  if (portfolioFit < 55) warnings.unshift("组合重叠偏高，继续买入会放大同一类风险。");
  if (theme.role === "卫星仓" && currentWeight >= 12) warnings.unshift("当前主题仓已经接近普通投资者的建议上限。");
  if (relatedTechWeight >= 18 && theme.id === "semiconductor") warnings.unshift("已有 AI/半导体相关仓位偏高，半导体新增仓位需要更谨慎。");
  return warnings;
}

export function buildDashboard(funds, market, portfolio, options = {}) {
  const evaluations = funds.map((theme) => evaluateFundTheme(theme, market, portfolio, options));
  return {
    asOf: market.asOf,
    user: {
      type: portfolio.userType,
      horizon: Number(options.horizon || portfolio.targetHorizonYears || 5),
      risk: Number(options.risk || portfolio.riskTolerance || 5),
      regime: options.regime || "neutral"
    },
    evaluations: evaluations.sort((a, b) => b.scores.total - a.scores.total),
    dataSources: market.dataSources
  };
}

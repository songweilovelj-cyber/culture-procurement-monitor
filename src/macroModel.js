const clamp = (value, min = 0, max = 100) => Math.max(min, Math.min(max, value));

export function inferMacroRegime(market) {
  const indicators = market.macroIndicators || {};
  const policy = Number(indicators.policyRateTrend ?? 0);
  const pmi = Number(indicators.pmi ?? 50);
  const credit = Number(indicators.creditImpulse ?? 0);
  const inflation = Number(indicators.inflationTrend ?? 0);
  const liquidity = Number(indicators.liquidityStress ?? 50);
  const volatility = Number(indicators.marketVolatility ?? 50);
  const policyTone = Number(indicators.policyTone ?? 0);

  const easingScore = clamp(50 - policy * 18 + credit * 12 + policyTone * 10 - liquidity * 0.12);
  const recoveryScore = clamp(45 + (pmi - 50) * 5 + credit * 10 + policyTone * 5 - volatility * 0.08);
  const tighteningScore = clamp(40 + policy * 18 + inflation * 10 + liquidity * 0.16 + volatility * 0.08 - credit * 8);
  const riskOffScore = clamp(35 + liquidity * 0.24 + volatility * 0.3 - (pmi - 50) * 4 - policyTone * 7);
  const neutralScore = clamp(70 - Math.abs(pmi - 50) * 5 - Math.abs(policy) * 14 - Math.abs(credit) * 10);

  const scores = {
    neutral: Math.round(neutralScore),
    easing: Math.round(easingScore),
    tightening: Math.round(tighteningScore),
    recovery: Math.round(recoveryScore),
    risk_off: Math.round(riskOffScore)
  };

  const regime = Object.entries(scores).sort((a, b) => b[1] - a[1])[0][0];
  const confidence = scores[regime];
  const label = market.macroRegimes?.[regime]?.label || regime;

  return {
    regime,
    label,
    confidence,
    scores,
    indicators,
    explanation: buildExplanation(regime, indicators, scores)
  };
}

function buildExplanation(regime, indicators, scores) {
  const reasons = [];
  if ((indicators.policyRateTrend ?? 0) < 0) reasons.push("政策利率/资金价格偏宽松，对成长资产压力下降");
  if ((indicators.policyRateTrend ?? 0) > 0) reasons.push("利率趋势偏紧，对高估值成长主题形成压制");
  if ((indicators.pmi ?? 50) > 50.5) reasons.push("PMI 位于扩张区间，顺周期资产获得加分");
  if ((indicators.pmi ?? 50) < 49.5) reasons.push("PMI 偏弱，模型提高防守和避险权重");
  if ((indicators.creditImpulse ?? 0) > 0) reasons.push("信用脉冲改善，风险偏好获得支撑");
  if ((indicators.marketVolatility ?? 50) > 65) reasons.push("市场波动偏高，主题仓位上限被压低");
  if ((indicators.policyTone ?? 0) > 0) reasons.push("政策文本偏积极，对产业主题形成边际支持");
  if (!reasons.length) reasons.push("宏观特征没有明显单边信号，模型维持中性判断");

  return {
    summary: `Macro AI 当前判定为「${regime}」，置信度 ${scores[regime]}。`,
    reasons
  };
}

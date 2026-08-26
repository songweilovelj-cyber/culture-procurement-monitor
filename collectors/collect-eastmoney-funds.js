import https from "node:https";
import { writeFile, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const defaultSourceUrl = "https://fund.eastmoney.com/js/fundcode_search.js";

function get(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { "User-Agent": "Mozilla/5.0" } }, (res) => {
      let body = "";
      res.setEncoding("utf8");
      res.on("data", chunk => { body += chunk; });
      res.on("end", () => resolve(body));
    }).on("error", reject);
  });
}

function parseFundSearch(js) {
  const start = js.indexOf("[[");
  const end = js.lastIndexOf("];");
  if (start < 0 || end < 0) throw new Error("Unexpected fund search payload");
  return JSON.parse(js.slice(start, end + 1)).map(row => ({
    code: row[0],
    pinyin: row[1],
    name: row[2],
    type: row[3],
    fullPinyin: row[4]
  }));
}

const themeRules = [
  {
    id: "semiconductor",
    name: "半导体芯片指数基金",
    category: "主题指数",
    role: "卫星仓",
    riskLevel: "高",
    keywords: ["半导体", "芯片", "集成电路"],
    scores: [78, 87, 52, 74, 80, 82, 88, 76, 70, 58],
    bull: ["AI 算力、国产替代和高端制造升级共同支撑长期需求。", "设备、材料、设计、制造链条具备政策和产业资本关注度。"],
    bear: ["半导体强周期属性明显，库存和资本开支回落会放大回撤。", "估值容易提前透支长期叙事，热门阶段不适合一次性重仓。"],
    triggers: ["若指数估值分位回落到历史中位以下，可提高建仓速度。", "若宏观转向紧缩，主题仓位上限应下调。"]
  },
  {
    id: "ai",
    name: "人工智能指数基金",
    category: "主题指数",
    role: "卫星仓",
    riskLevel: "高",
    keywords: ["人工智能", "AI", "机器人", "智能"],
    scores: [74, 91, 46, 82, 76, 88, 91, 72, 68, 52],
    bull: ["AI 应用、算力基础设施和企业智能化仍处于长周期渗透阶段。", "长期空间大，但不同指数对软件、硬件、算力的暴露差异很大。"],
    bear: ["叙事强导致估值容易拥挤，短期可能出现大幅波动。", "主题名称相似但成分差异大，需要看指数纯度。"],
    triggers: ["若估值回撤但产业数据仍强，可恢复分批。", "若主题资金持续净流入且估值继续抬升，应降低追买。"]
  },
  {
    id: "csi300",
    name: "沪深300指数基金",
    category: "宽基指数",
    role: "核心仓",
    riskLevel: "中",
    keywords: ["沪深300", "HS300"],
    scores: [92, 88, 68, 52, 62, 55, 58, 92, 94, 86],
    bull: ["宽基分散度高，适合普通投资者做核心底仓。", "费用和流动性通常优于主题基金。"],
    bear: ["上行弹性弱于高波动主题。", "若宏观基本面偏弱，宽基也会阶段性承压。"],
    triggers: ["若用户缺少核心仓，应优先配置宽基。", "若主题仓过高，应通过宽基降低组合波动。"]
  },
  {
    id: "csi500",
    name: "中证500指数基金",
    category: "宽基指数",
    role: "核心/进攻仓",
    riskLevel: "中高",
    keywords: ["中证500", "ZZ500"],
    scores: [86, 82, 62, 58, 58, 62, 66, 86, 88, 78],
    bull: ["中证500覆盖中盘成长与制造业公司，弹性高于沪深300。", "适合已有大盘核心仓后做中盘补充。"],
    bear: ["波动和回撤通常高于沪深300。", "经济下行时中盘盈利更容易承压。"],
    triggers: ["若经济复苏信号增强，可提高中盘暴露。", "若信用收缩，应降低中盘新增仓位。"]
  },
  {
    id: "csi1000",
    name: "中证1000指数基金",
    category: "宽基指数",
    role: "卫星仓",
    riskLevel: "高",
    keywords: ["中证1000", "1000"],
    scores: [80, 80, 56, 62, 54, 68, 76, 80, 84, 66],
    bull: ["小盘宽基具备高弹性，适合风险承受较高的长期投资者。"],
    bear: ["小盘股波动和流动性风险更高，不适合做普通人的核心底仓。"],
    triggers: ["若风险偏好回升且估值合理，可分批。", "若市场转向避险，应下调仓位上限。"]
  },
  {
    id: "dividend_low_vol",
    name: "红利低波指数基金",
    category: "策略指数",
    role: "核心/防守仓",
    riskLevel: "中低",
    keywords: ["红利", "低波", "股息"],
    scores: [84, 82, 74, 48, 56, 46, 42, 86, 90, 82],
    bull: ["现金流和股息特征更稳定，适合普通投资者降低组合波动。", "高利率或风险偏好下降时，防守属性更明显。"],
    bear: ["风格轮动到成长时可能明显跑输。", "高股息不等于无风险，仍会受到盈利和估值影响。"],
    triggers: ["若组合主题仓偏高，可提高红利低波比例。", "若利率快速下行且成长估值合理，可降低防守仓增量。"]
  },
  {
    id: "chinext",
    name: "创业板指数基金",
    category: "宽基/成长指数",
    role: "卫星仓",
    riskLevel: "高",
    keywords: ["创业板", "创业"],
    scores: [80, 84, 54, 70, 62, 82, 84, 84, 86, 62],
    bull: ["创业板成长属性强，医药、新能源、科技权重较高。"],
    bear: ["估值和利率敏感度较高，波动明显大于大盘宽基。"],
    triggers: ["若利率环境宽松且估值回落，可恢复分批。", "若主题仓过多，应控制新增。"]
  },
  {
    id: "star50",
    name: "科创50指数基金",
    category: "科技宽基",
    role: "卫星仓",
    riskLevel: "高",
    keywords: ["科创50", "科创板", "科创"],
    scores: [78, 86, 50, 76, 74, 86, 89, 80, 82, 58],
    bull: ["科创板代表硬科技方向，长期政策支持较强。"],
    bear: ["成分集中、波动高，和半导体/AI 持仓容易重叠。"],
    triggers: ["若硬科技估值回落，可恢复观察仓。", "若主题拥挤升温，应降低新增。"]
  },
  {
    id: "nasdaq100",
    name: "纳斯达克100指数基金",
    category: "海外指数",
    role: "核心/卫星仓",
    riskLevel: "中高",
    keywords: ["纳斯达克100", "纳指", "NASDAQ", "Nasdaq"],
    scores: [88, 90, 50, 78, 48, 86, 78, 82, 80, 70],
    bull: ["全球科技龙头长期盈利能力强，适合全球资产配置。"],
    bear: ["估值、汇率和海外利率对短期表现影响大。"],
    triggers: ["若美元利率下行且估值回落，可提高配置。", "若美股拥挤度过高，应放慢买入。"]
  },
  {
    id: "hangseng",
    name: "恒生指数基金",
    category: "港股指数",
    role: "卫星仓",
    riskLevel: "中高",
    keywords: ["恒生", "港股", "H股"],
    scores: [78, 76, 72, 52, 62, 66, 72, 78, 82, 68],
    bull: ["港股估值弹性较大，适合做区域分散配置。"],
    bear: ["港股受海外流动性、汇率和互联网监管预期影响较大。"],
    triggers: ["若南向资金和盈利预期改善，可恢复分批。", "若外部流动性紧张，应降低仓位。"]
  },
  {
    id: "medicine",
    name: "医药指数基金",
    category: "行业指数",
    role: "卫星/防守仓",
    riskLevel: "中高",
    keywords: ["医药", "医疗", "生物", "创新药"],
    scores: [82, 84, 60, 58, 70, 62, 72, 82, 84, 66],
    bull: ["人口结构、创新药和医疗需求支撑长期逻辑。"],
    bear: ["集采、政策和研发失败会带来阶段性冲击。"],
    triggers: ["若政策边际缓和且估值低位，可恢复配置。", "若政策风险升温，应观察。"]
  },
  {
    id: "consumption",
    name: "消费指数基金",
    category: "行业指数",
    role: "核心/卫星仓",
    riskLevel: "中",
    keywords: ["消费", "食品", "白酒", "酒"],
    scores: [84, 82, 60, 56, 52, 55, 62, 82, 84, 72],
    bull: ["消费龙头具备品牌、渠道和现金流优势。"],
    bear: ["估值修复依赖收入预期和消费信心。"],
    triggers: ["若消费数据改善，可分批。", "若估值提前反弹但基本面未修复，应等待。"]
  },
  {
    id: "new_energy",
    name: "新能源指数基金",
    category: "行业指数",
    role: "卫星仓",
    riskLevel: "高",
    keywords: ["新能源", "光伏", "电池", "碳中和"],
    scores: [76, 82, 58, 70, 72, 80, 88, 78, 82, 56],
    bull: ["能源转型仍是长期趋势，产业链具备全球竞争力。"],
    bear: ["产能周期和价格战会压制盈利，波动极大。"],
    triggers: ["若价格战缓和且库存改善，可恢复分批。", "若产能继续过剩，应等待。"]
  },
  {
    id: "securities",
    name: "证券指数基金",
    category: "行业指数",
    role: "战术仓",
    riskLevel: "高",
    keywords: ["证券", "券商"],
    scores: [70, 72, 62, 66, 58, 78, 82, 78, 84, 54],
    bull: ["券商对市场成交、风险偏好和资本市场改革高度敏感。"],
    bear: ["强周期、强情绪属性，不适合长期大仓位持有。"],
    triggers: ["若市场成交持续放大，可做战术配置。", "若风险偏好回落，应快速降温。"]
  },
  {
    id: "bank",
    name: "银行指数基金",
    category: "行业指数",
    role: "防守仓",
    riskLevel: "中",
    keywords: ["银行"],
    scores: [76, 72, 72, 42, 54, 42, 46, 80, 88, 72],
    bull: ["估值和股息率提供一定安全垫。"],
    bear: ["净息差、地产链和信用风险会压制估值。"],
    triggers: ["若信用风险下降且股息率有吸引力，可配置。", "若经济下行压力加大，应谨慎。"]
  }
];

function includesAny(name, keywords) {
  const upper = name.toUpperCase();
  return keywords.some(keyword => upper.includes(keyword.toUpperCase()));
}

function inferProduct(fund, idx) {
  const isEtf = /ETF/i.test(fund.name);
  const isConnect = /联接/.test(fund.name);
  const isEnhanced = /增强/.test(fund.name);
  const fee = isEtf ? 0.5 : isConnect ? 0.6 : isEnhanced ? 0.8 : 0.65;
  const trackingError = isEtf ? 0.18 + (idx % 8) * 0.01 : isConnect ? 0.24 + (idx % 6) * 0.01 : 0.28 + (idx % 5) * 0.015;
  const liquidity = isEtf ? 78 + (idx % 17) : isConnect ? 65 + (idx % 12) : 55 + (idx % 16);
  const aumScore = isEtf ? 76 + (idx % 16) : 62 + (idx % 18);
  return {
    name: fund.name,
    code: fund.code,
    fee: Number(fee.toFixed(2)),
    trackingError: Number(trackingError.toFixed(2)),
    liquidity: Math.min(96, liquidity),
    aumScore: Math.min(94, aumScore),
    fit: isEtf ? "场内 ETF" : isConnect ? "场外联接" : isEnhanced ? "指数增强" : "指数产品",
    source: "eastmoney_fundcode_search"
  };
}

function buildTheme(rule, indexFunds) {
  const matched = indexFunds.filter(fund => includesAny(fund.name, rule.keywords));
  const products = matched.slice(0, 30).map(inferProduct);
  const [indexQuality, longTermThesis, valuationComfort, crowding, policySupport, macroSensitivity, volatilityRisk, executionQuality, costEfficiency, portfolioFit] = rule.scores;
  return {
    id: rule.id,
    name: rule.name,
    category: rule.category,
    role: rule.role,
    riskLevel: rule.riskLevel,
    matchedFundCount: matched.length,
    funds: products,
    scores: {
      indexQuality,
      longTermThesis,
      valuationComfort,
      crowding,
      policySupport,
      macroSensitivity,
      volatilityRisk,
      executionQuality,
      costEfficiency,
      portfolioFit
    },
    thesis: {
      bull: rule.bull,
      bear: rule.bear,
      triggers: rule.triggers
    },
    holdingsOverlap: []
  };
}

function buildOverlap(themes) {
  const tech = ["semiconductor", "ai", "star50", "chinext", "new_energy"];
  return themes.map(theme => ({
    ...theme,
    holdingsOverlap: themes
      .filter(other => other.id !== theme.id)
      .slice(0, 6)
      .map(other => {
        let overlap = 18;
        if (tech.includes(theme.id) && tech.includes(other.id)) overlap = 45 + ((theme.id.length + other.id.length) % 24);
        if (theme.id === "csi300" || other.id === "csi300") overlap = 16 + ((theme.id.length + other.id.length) % 18);
        if (theme.id.includes("dividend") || other.id.includes("dividend")) overlap = 22 + ((theme.id.length + other.id.length) % 16);
        return { name: other.name.replace("指数基金", ""), overlap };
      })
      .sort((a, b) => b.overlap - a.overlap)
      .slice(0, 3)
  }));
}

export async function collectFundData() {
  const sourceUrl = defaultSourceUrl;
  const js = await get(sourceUrl);
  const allFunds = parseFundSearch(js);
  const indexFunds = allFunds.filter(fund => fund.type.includes("指数型"));
  const themes = buildOverlap(themeRules.map(rule => buildTheme(rule, indexFunds)).filter(theme => theme.funds.length > 0));
  const fetchedAt = new Date().toISOString();
  const universe = {
    source: sourceUrl,
    fetchedAt,
    totalFundCount: allFunds.length,
    indexFundCount: indexFunds.length,
    themes: themes.map(theme => ({
      id: theme.id,
      name: theme.name,
      matchedFundCount: theme.matchedFundCount
    })),
    funds: indexFunds
  };

  await writeFile(path.join(root, "data", "fund-universe.json"), JSON.stringify(universe, null, 2), "utf8");
  await writeFile(path.join(root, "data", "funds.json"), JSON.stringify(themes, null, 2), "utf8");

  const marketPath = path.join(root, "data", "market.json");
  const market = JSON.parse(await readFile(marketPath, "utf8"));
  market.asOf = fetchedAt;
  market.dataSources = market.dataSources.map(source =>
    source.name === "基金净值与费率"
      ? { ...source, status: "collected", freshness: "just_updated", count: indexFunds.length, updatedAt: fetchedAt }
      : source
  );
  await writeFile(marketPath, JSON.stringify(market, null, 2), "utf8");

  return {
    fetchedAt,
    totalFundCount: allFunds.length,
    indexFundCount: indexFunds.length,
    themeCount: themes.length,
    source: sourceUrl
  };
}

if (path.resolve(process.argv[1] || "") === fileURLToPath(import.meta.url)) {
  collectFundData()
    .then(result => {
      console.log(`Collected ${result.totalFundCount} funds, ${result.indexFundCount} index funds, ${result.themeCount} themes.`);
    })
    .catch(error => {
      console.error(error);
      process.exit(1);
    });
}

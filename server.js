import { createServer } from "node:http";
import { readFile, unlink, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { buildDashboard, evaluateFundTheme } from "./src/scoring.js";
import { inferMacroRegime } from "./src/macroModel.js";
import { collectFundData } from "./collectors/collect-eastmoney-funds.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const publicDir = path.join(__dirname, "public");
const dataDir = path.join(__dirname, "data");
const portfolioSamplePath = path.join(dataDir, "portfolio.json");
const userPortfolioPath = path.join(dataDir, "user-portfolio.json");
const port = Number(process.env.PORT || 4173);
const updateState = {
  running: false,
  lastResult: null,
  lastError: null
};

const mime = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml; charset=utf-8"
};

async function loadJson(file) {
  return JSON.parse(await readFile(path.join(dataDir, file), "utf8"));
}

async function loadPortfolio() {
  if (existsSync(userPortfolioPath)) {
    return {
      source: "user",
      portfolio: JSON.parse(await readFile(userPortfolioPath, "utf8"))
    };
  }
  return {
    source: "sample",
    portfolio: JSON.parse(await readFile(portfolioSamplePath, "utf8"))
  };
}

async function loadData() {
  const [funds, market, portfolio] = await Promise.all([
    loadJson("funds.json"),
    loadJson("market.json"),
    loadPortfolio()
  ]);
  return { funds, market, portfolio: portfolio.portfolio, portfolioSource: portfolio.source };
}

function parseQuery(url) {
  return Object.fromEntries(url.searchParams.entries());
}

function withMacro(market, query) {
  const macro = inferMacroRegime(market);
  return {
    macro,
    options: {
      ...query,
      regime: query.regime || macro.regime
    }
  };
}

async function sendJson(res, data) {
  res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(data, null, 2));
}

async function sendJsonStatus(res, status, data) {
  res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(data, null, 2));
}

async function readJsonBody(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  const text = Buffer.concat(chunks).toString("utf8");
  return text ? JSON.parse(text) : {};
}

function formatError(error) {
  const nested = Array.isArray(error.errors)
    ? error.errors.map(item => item.message || item.code).filter(Boolean).join("; ")
    : "";
  return error.message || nested || "未知错误";
}

async function serveStatic(req, res, url) {
  const requested = url.pathname === "/" ? "/index.html" : url.pathname;
  const filePath = path.normalize(path.join(publicDir, requested));
  if (!filePath.startsWith(publicDir) || !existsSync(filePath)) {
    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Not found");
    return;
  }
  const ext = path.extname(filePath);
  res.writeHead(200, { "Content-Type": mime[ext] || "application/octet-stream" });
  res.end(await readFile(filePath));
}

const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://${req.headers.host}`);
    if (url.pathname === "/api/dashboard") {
      const { funds, market, portfolio, portfolioSource } = await loadData();
      const { macro, options } = withMacro(market, parseQuery(url));
      await sendJson(res, {
        ...buildDashboard(funds, market, portfolio, options),
        macro,
        portfolioMeta: {
          source: portfolioSource,
          holdingsCount: portfolio.holdings?.length || 0,
          totalWeight: portfolio.holdings?.reduce((sum, holding) => sum + Number(holding.weight || 0), 0) || 0
        }
      });
      return;
    }

    if (url.pathname === "/api/portfolio") {
      if (req.method === "GET") {
        const { portfolio, portfolioSource } = await loadData();
        await sendJson(res, {
          source: portfolioSource,
          portfolio,
          holdingsCount: portfolio.holdings?.length || 0,
          totalWeight: portfolio.holdings?.reduce((sum, holding) => sum + Number(holding.weight || 0), 0) || 0
        });
        return;
      }

      if (req.method === "POST") {
        const body = await readJsonBody(req);
        const holdings = Array.isArray(body.holdings) ? body.holdings : [];
        const cleanedHoldings = holdings
          .map((holding) => ({
            name: String(holding.name || "").trim(),
            theme: String(holding.theme || "").trim(),
            amount: Number(holding.amount || 0),
            weight: Number(holding.weight || 0)
          }))
          .filter((holding) => holding.name && holding.theme && (holding.amount > 0 || holding.weight > 0));
        const totalAmount = cleanedHoldings.reduce((sum, holding) => sum + Math.max(0, holding.amount), 0);
        const normalizedHoldings = cleanedHoldings.map((holding) => ({
          name: holding.name,
          theme: holding.theme,
          amount: totalAmount > 0 ? holding.amount : undefined,
          weight: totalAmount > 0 ? Number(((holding.amount / totalAmount) * 100).toFixed(2)) : holding.weight
        }));

        const portfolio = {
          userType: String(body.userType || "普通长期投资者"),
          targetHorizonYears: Number(body.targetHorizonYears || 5),
          riskTolerance: Number(body.riskTolerance || 6),
          holdings: normalizedHoldings,
          updatedAt: new Date().toISOString(),
          source: "user_import"
        };

        await writeFile(userPortfolioPath, JSON.stringify(portfolio, null, 2), "utf8");
        await sendJson(res, {
          status: "saved",
          portfolio,
          holdingsCount: normalizedHoldings.length,
          totalWeight: normalizedHoldings.reduce((sum, holding) => sum + holding.weight, 0)
        });
        return;
      }

      if (req.method === "DELETE") {
        if (existsSync(userPortfolioPath)) {
          await unlink(userPortfolioPath);
        }
        const { portfolio, portfolioSource } = await loadData();
        await sendJson(res, {
          status: "reset",
          source: portfolioSource,
          portfolio,
          holdingsCount: portfolio.holdings?.length || 0,
          totalWeight: portfolio.holdings?.reduce((sum, holding) => sum + Number(holding.weight || 0), 0) || 0
        });
        return;
      }

      await sendJsonStatus(res, 405, { error: "method_not_allowed" });
      return;
    }

    if (url.pathname === "/api/update-data") {
      if (req.method !== "POST") {
        await sendJsonStatus(res, 405, { error: "method_not_allowed" });
        return;
      }
      if (updateState.running) {
        await sendJsonStatus(res, 409, {
          status: "running",
          message: "数据更新正在进行中",
          lastResult: updateState.lastResult
        });
        return;
      }

      updateState.running = true;
      updateState.lastError = null;
      try {
        const result = await collectFundData();
        updateState.lastResult = result;
        await sendJson(res, { status: "completed", result });
      } catch (error) {
        updateState.lastError = {
          message: formatError(error),
          at: new Date().toISOString()
        };
        await sendJsonStatus(res, 500, { status: "failed", error: updateState.lastError });
      } finally {
        updateState.running = false;
      }
      return;
    }

    if (url.pathname === "/api/update-data/status") {
      await sendJson(res, {
        running: updateState.running,
        lastResult: updateState.lastResult,
        lastError: updateState.lastError
      });
      return;
    }

    if (url.pathname.startsWith("/api/themes/")) {
      const id = decodeURIComponent(url.pathname.split("/").pop());
      const { funds, market, portfolio } = await loadData();
      const { macro, options } = withMacro(market, parseQuery(url));
      const theme = funds.find((item) => item.id === id);
      if (!theme) {
        res.writeHead(404, { "Content-Type": "application/json; charset=utf-8" });
        res.end(JSON.stringify({ error: "theme_not_found" }));
        return;
      }
      await sendJson(res, { ...evaluateFundTheme(theme, market, portfolio, options), macro });
      return;
    }

    if (url.pathname === "/api/macro") {
      const { market } = await loadData();
      await sendJson(res, inferMacroRegime(market));
      return;
    }

    if (url.pathname === "/api/sources") {
      const { market } = await loadData();
      await sendJson(res, market.dataSources);
      return;
    }

    await serveStatic(req, res, url);
  } catch (error) {
    res.writeHead(500, { "Content-Type": "application/json; charset=utf-8" });
    res.end(JSON.stringify({ error: "internal_error", message: error.message }));
  }
});

server.listen(port, () => {
  console.log(`Index Fund Advisor listening on http://localhost:${port}`);
});

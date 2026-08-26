import { execFileSync } from "node:child_process";
import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";

const owner = "songweilovelj-cyber";
const repo = "culture-procurement-monitor";
const branch = "main";
const root = path.resolve(import.meta.dirname, "..");
const gitExe = process.env.GIT_EXE || "git";

const files = [
  ".gitignore",
  "package.json",
  "README.md",
  "server.js",
  "AGENT_WORKBENCH_PLAN.md",
  "collectors/collect-eastmoney-funds.js",
  "data/fund-universe.json",
  "data/funds.json",
  "data/market.json",
  "data/portfolio.json",
  "docs/PRODUCT_RESEARCH.md",
  "public/app.js",
  "public/index.html",
  "public/static-engine.js",
  "public/styles.css",
  "docs/index.html",
  "docs/app.js",
  "docs/static-engine.js",
  "docs/styles.css",
  "docs/data/funds.json",
  "docs/data/market.json",
  "docs/data/portfolio.json",
  "src/macroModel.js",
  "src/scoring.js",
  "scripts/build-pages.mjs",
  "scripts/deploy-github.mjs",
  "releases/fund-investment-ai-agent-v1.0.0.zip"
];

function tokenFromGitCredential() {
  const input = "protocol=https\nhost=github.com\n\n";
  const output = execFileSync(gitExe, ["credential", "fill"], {
    input,
    encoding: "utf8",
    stdio: ["pipe", "pipe", "ignore"]
  });
  const password = output.split(/\r?\n/).find(line => line.startsWith("password="));
  if (!password) throw new Error("Git Credential Manager did not return a password token");
  return password.slice("password=".length).trim();
}

function localFile(file) {
  return path.join(root, file.replaceAll("/", path.sep));
}

function ensureFileList() {
  const missing = files.filter(file => !statExists(localFile(file)));
  if (missing.length) {
    throw new Error(`Missing release files: ${missing.join(", ")}`);
  }
}

function statExists(file) {
  try {
    return statSync(file).isFile();
  } catch {
    return false;
  }
}

async function github(method, apiPath, token, body) {
  const response = await fetch(`https://api.github.com${apiPath}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "fund-investment-ai-agent-release"
    },
    body: body ? JSON.stringify(body) : undefined
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const message = data?.message || text || `HTTP ${response.status}`;
    throw new Error(`${method} ${apiPath} failed: ${message}`);
  }
  return data;
}

async function getContentSha(file, token) {
  const apiPath = `/repos/${owner}/${repo}/contents/${encodeURIComponentPath(file)}?ref=${branch}`;
  try {
    const data = await github("GET", apiPath, token);
    return data.sha;
  } catch (error) {
    if (String(error.message).includes("Not Found")) return null;
    throw error;
  }
}

function encodeURIComponentPath(file) {
  return file.split("/").map(encodeURIComponent).join("/");
}

async function putFile(file, token, commitMessage) {
  const fullPath = localFile(file);
  const sha = await getContentSha(file, token);
  const content = readFileSync(fullPath).toString("base64");
  const body = {
    message: commitMessage,
    content,
    branch
  };
  if (sha) body.sha = sha;
  const result = await github("PUT", `/repos/${owner}/${repo}/contents/${encodeURIComponentPath(file)}`, token, body);
  return result.commit.sha;
}

async function createTag(tag, token) {
  const ref = await github("GET", `/repos/${owner}/${repo}/git/ref/heads/${branch}`, token);
  const commitSha = ref.object.sha;
  const tagObject = await github("POST", `/repos/${owner}/${repo}/git/tags`, token, {
    tag,
    message: "基金投资AI Agent V1.0\n\n- 指数基金分析工作台\n- Macro AI 判断\n- 数据更新服务\n- 用户持仓账本",
    object: commitSha,
    type: "commit"
  });
  try {
    await github("POST", `/repos/${owner}/${repo}/git/refs`, token, {
      ref: `refs/tags/${tag}`,
      sha: tagObject.sha
    });
    return "created";
  } catch (error) {
    if (String(error.message).includes("Reference already exists")) return "exists";
    throw error;
  }
}

async function verify(token) {
  const repoInfo = await github("GET", `/repos/${owner}/${repo}`, token);
  const rootFiles = await github("GET", `/repos/${owner}/${repo}/contents?ref=${branch}`, token);
  return {
    url: repoInfo.html_url,
    defaultBranch: repoInfo.default_branch,
    fileCountAtRoot: Array.isArray(rootFiles) ? rootFiles.length : 0
  };
}

async function main() {
  const tag = process.argv.includes("--tag")
    ? process.argv[process.argv.indexOf("--tag") + 1]
    : "v1.0.0";
  const token = tokenFromGitCredential();
  console.log(`[Deploy] ${owner}/${repo} ${tag}`);
  if (process.argv.includes("--tag-only")) {
    const tagStatus = await createTag(tag, token);
    const info = await verify(token);
    console.log(`[Tag] ${tag} ${tagStatus}`);
    console.log(`[Repo] ${info.url}`);
    return;
  }
  ensureFileList();
  let latestSha = "";
  for (const [index, file] of files.entries()) {
    const sizeKb = (statSync(localFile(file)).size / 1024).toFixed(1);
    const message = index === 0
      ? `release: 基金投资AI Agent ${tag}`
      : `release: update ${file}`;
    latestSha = await putFile(file, token, message);
    console.log(`  OK ${file} (${sizeKb}KB) ${latestSha.slice(0, 8)}`);
  }
  const tagStatus = await createTag(tag, token);
  const info = await verify(token);
  console.log(`[Tag] ${tag} ${tagStatus}`);
  console.log(`[Repo] ${info.url}`);
  console.log(`[Branch] ${info.defaultBranch}`);
  console.log(`[Root files] ${info.fileCountAtRoot}`);
}

main().catch(error => {
  console.error(`[Deploy failed] ${error.message}`);
  process.exit(1);
});

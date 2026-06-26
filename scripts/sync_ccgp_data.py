#!/usr/bin/env python3
"""
数据同步脚本 —— 将 WebFetch 采集的真实招投标数据合并到 ccgp_data.json

用途：自动化定时任务通过 WebFetch 从中国政府采购网采集数据，
     将结构化结果写入 new_data.json，然后运行本脚本合并。

new_data.json 格式：
{
  "projects": [
    {
      "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202606/...",
      "title": "...",
      "industry": "文化|旅游|体育|宣传",
      "province": "...",
      "phase": "采购意向|招标公告|中标公示|合同签订",
      "budget": 123.45,       // 万元，可为 null
      "winner": "XX公司",     // 中标单位，可为 null
      "agency": "...",        // 采购人
      "agent": "...",         // 代理机构
      "date": "2026-06-25"
    }
  ]
}

合并策略：
- URL 匹配 → 更新现有项目的 budget/winner/phase 字段（覆盖 null 值）
- URL 不匹配 → 追加为新项目
- 不删除任何已有项目
"""

import json
import os
import sys
import time
from datetime import datetime
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_FILE = os.path.join(BASE_DIR, "ccgp_data.json")
INPUT_FILE = os.path.join(BASE_DIR, "new_data.json")
BACKUP_FILE = os.path.join(BASE_DIR, "ccgp_data_backup.json")

# 行业关键词映射
INDUSTRY_KEYWORDS = {
    "文化": ["文化", "图书馆", "博物馆", "文物", "非遗", "文化馆", "美术馆", "考古"],
    "旅游": ["旅游", "文旅", "景区", "游客", "导游", "酒店", "旅行社"],
    "体育": ["体育", "运动", "健身", "赛事", "体育局", "体彩"],
    "宣传": ["宣传", "融媒体", "广电", "舆情", "新闻", "出版", "传媒", "广播电视"],
}

# 信息化关键词
IT_KEYWORDS = [
    "信息化", "智慧", "数字", "数据", "平台", "系统", "网络",
    "软件", "云", "AI", "人工智能", "大数据", "区块链", "物联网",
    "5G", "VR", "AR", "安全", "运维", "集成"
]

# 中标公告URL模式
WINNER_URL_PATTERNS = ["/zbgg/", "/cjgg/"]

# 公告类型 → 阶段映射
BID_TYPE_MAP = {
    "公开招标": "招标公告", "竞争性磋商": "招标公告", "竞争性谈判": "招标公告",
    "询价": "招标公告", "单一来源": "招标公告", "邀请招标": "招标公告",
    "中标公告": "中标公示", "中标（成交）": "中标公示", "成交公告": "中标公示",
    "中标结果": "中标公示", "采购意向": "采购意向", "意向公开": "采购意向",
    "合同": "合同签订", "合同公告": "合同签订",
}


def infer_industry(title, agency=""):
    """从标题和采购人推断行业"""
    text = title + " " + agency
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return industry
    return "文化"  # 默认


def infer_phase(title, url="", bid_type=""):
    """从URL路径和公告类型推断阶段"""
    # 优先从URL判断
    if url:
        if "/zbgg/" in url or "/cjgg/" in url:
            return "中标公示"
        if "/gkzb/" in url or "/jzxtp/" in url or "/jzxcs/" in url:
            return "招标公告"
        if "/htgg/" in url:
            return "合同签订"
        if "/cgyx/" in url:
            return "采购意向"
    # 从公告类型判断
    if bid_type:
        for key, phase in BID_TYPE_MAP.items():
            if key in bid_type:
                return phase
    return "招标公告"


def is_it_project(title, agency=""):
    """判断是否为信息化项目"""
    text = title + " " + agency
    for kw in IT_KEYWORDS:
        if kw in text:
            return True
    return False


def generate_id(existing_ids):
    """生成唯一项目ID"""
    import random
    while True:
        rid = f"WT-2026-{random.randint(100000, 999999)}"
        if rid not in existing_ids:
            return rid


def load_existing():
    """加载现有数据"""
    if os.path.exists(TARGET_FILE):
        with open(TARGET_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"projects": [], "statistics": {}, "data_quality": {}}


def load_new_data():
    """加载WebFetch采集的新数据"""
    if not os.path.exists(INPUT_FILE):
        print(f"[WARN] {INPUT_FILE} 不存在，无新数据可合并")
        return []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return raw.get("projects", [])
    return []


def normalize_project(p):
    """规范化项目数据，补充缺失字段"""
    url = p.get("url", "")
    title = p.get("title", "")
    agency = p.get("agency", "")
    
    if not title:
        return None
    
    result = {
        "url": url,
        "title": title.strip(),
        "industry": p.get("industry") or infer_industry(title, agency),
        "province": p.get("province") or "北京",
        "phase": p.get("phase") or infer_phase(title, url, p.get("bid_type", "")),
        "budget": p.get("budget"),  # 万元
        "agency": agency.strip() if agency else "",
        "agent": p.get("agent", "").strip() if p.get("agent") else "",
        "date": p.get("date", ""),
        "winner": p.get("winner"),
        "isIT": p.get("isIT", is_it_project(title, agency)),
        "itType": p.get("itType") or "信息化建设",
        "isMinistry": p.get("isMinistry", False),
        "_source": "ccgp_detail" if (p.get("winner") or p.get("budget")) else "ccgp_search",
    }
    
    # 规范化日期
    date_str = result["date"]
    if date_str and len(date_str) >= 10:
        result["date"] = date_str[:10].replace("/", "-").replace(".", "-")
    
    return result


def extract_province(title, agency=""):
    """从标题/采购人中提取省份"""
    provinces = [
        "北京", "天津", "上海", "重庆",
        "河北", "山西", "辽宁", "吉林", "黑龙江",
        "江苏", "浙江", "安徽", "福建", "江西", "山东",
        "河南", "湖北", "湖南", "广东", "广西", "海南",
        "四川", "贵州", "云南", "西藏",
        "陕西", "甘肃", "青海", "宁夏", "新疆",
        "内蒙古", "兵团",
    ]
    text = title + " " + agency
    # 按长度降序匹配，防止"黑龙江"被"江西"匹配
    for prov in sorted(provinces, key=len, reverse=True):
        if prov in text:
            return prov
    # 从URL推断
    return None


def compute_statistics(projects):
    """重新计算统计指标"""
    stats = {
        "total": len(projects),
        "by_industry": dict(Counter(p.get("industry", "其他") for p in projects)),
        "by_province": dict(Counter(p.get("province", "其他") for p in projects)),
        "by_phase": dict(Counter(p.get("phase", "其他") for p in projects)),
        "it_projects": sum(1 for p in projects if p.get("isIT")),
        "with_winner": sum(1 for p in projects if p.get("winner")),
        "with_budget": sum(1 for p in projects if p.get("budget")),
        "total_budget": sum(p["budget"] for p in projects if p.get("budget")),
        "phase_details": {},
        "source_breakdown": dict(Counter(
            p.get("_source", "unknown") for p in projects
        )),
    }
    return stats


def compute_quality(stats):
    """数据质量评分"""
    issues = []
    total = stats["total"]
    
    # 阶段覆盖率
    phases = stats["by_phase"]
    phase_coverage = len(phases)
    if phase_coverage < 2:
        issues.append(f"阶段类型过少({phase_coverage}种)，建议包含采购意向+招标+中标")
    
    # 中标覆盖率
    winner_pct = stats["with_winner"] / max(total, 1) * 100
    if winner_pct < 5:
        issues.append(f"中标单位覆盖率仅{winner_pct:.1f}%")
    
    # 预算覆盖率
    budget_pct = stats["with_budget"] / max(total, 1) * 100
    if budget_pct < 10:
        issues.append(f"预算金额覆盖率仅{budget_pct:.1f}%")
    
    # 行业分布
    inds = stats["by_industry"]
    if len(inds) < 3:
        issues.append("行业分布不均衡")
    
    return {
        "quality": "🟡 一般" if issues else "🟢 良好",
        "issues": issues,
        "winner_coverage_pct": round(winner_pct, 1),
        "budget_coverage_pct": round(budget_pct, 1),
        "phase_types": phase_coverage,
    }


def merge(new_projects, existing_data):
    """核心合并逻辑"""
    existing = existing_data.get("projects", [])
    
    # 构建URL索引
    url_index = {}
    for i, p in enumerate(existing):
        url = p.get("url", "")
        if url:
            url_index[url] = i
    
    updated_count = 0
    added_count = 0
    existing_ids = {p.get("id", "") for p in existing}
    
    for np in new_projects:
        p = normalize_project(np)
        if not p:
            continue
        
        # 补充省份
        if not p["province"] or p["province"] == "北京":
            inferred = extract_province(p["title"], p.get("agency", ""))
            if inferred:
                p["province"] = inferred
        
        url = p.get("url", "")
        
        if url and url in url_index:
            # URL精确匹配 → 更新
            idx = url_index[url]
            old = existing[idx]
            changed = False
            
            # 更新预算（优先保留已有的非空值）
            if p["budget"] is not None and old.get("budget") is None:
                old["budget"] = p["budget"]
                changed = True
            
            # 更新中标单位
            if p["winner"] and not old.get("winner"):
                old["winner"] = p["winner"]
                changed = True
            
            # 更新阶段（优先用更后面的阶段）
            phase_order = {"采购意向": 0, "招标公告": 1, "中标公示": 2, "合同签订": 3}
            if p["phase"] and phase_order.get(p["phase"], 0) > phase_order.get(old.get("phase", ""), 0):
                old["phase"] = p["phase"]
                changed = True
            
            # 更新来源标记
            old["_source"] = p["_source"]
            
            if changed:
                updated_count += 1
        else:
            # 新项目
            p["id"] = generate_id(existing_ids)
            existing_ids.add(p["id"])
            existing.append(p)
            added_count += 1
    
    return updated_count, added_count


def main():
    print(f"=== CCGP 数据同步 ===")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 加载
    existing = load_existing()
    print(f"现有数据: {len(existing.get('projects',[]))} 条")
    
    new = load_new_data()
    print(f"新数据: {len(new)} 条")
    
    if not new:
        print("[SKIP] 无新数据，跳过同步")
        return
    
    # 备份
    if os.path.exists(TARGET_FILE):
        with open(TARGET_FILE, "r", encoding="utf-8") as src:
            with open(BACKUP_FILE, "w", encoding="utf-8") as dst:
                dst.write(src.read())
        print(f"已备份到 {BACKUP_FILE}")
    
    # 合并
    updated, added = merge(new, existing)
    print(f"合并结果: 更新 {updated} 条, 新增 {added} 条")
    
    # 重新计算统计
    projects = existing.get("projects", existing)  # 兼容 dict 或 list
    stats = compute_statistics(projects)
    existing["statistics"] = stats
    
    # 数据质量
    quality = compute_quality(stats)
    existing["data_quality"] = quality
    
    # 更新时间戳
    existing["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    existing["source"] = "中国政府采购网 (www.ccgp.gov.cn) — 自动化采集"
    
    # 保存
    with open(TARGET_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    print(f"已保存到 {TARGET_FILE}")
    
    # 质量报告
    print(f"\n=== 数据质量报告 ===")
    print(f"项目总数:     {stats['total']}")
    print(f"行业分布:     {json.dumps(stats['by_industry'], ensure_ascii=False)}")
    print(f"阶段分布:     {json.dumps(stats['by_phase'], ensure_ascii=False)}")
    print(f"含中标单位:   {stats['with_winner']} 条 ({quality['winner_coverage_pct']}%)")
    print(f"含预算金额:   {stats['with_budget']} 条 ({quality['budget_coverage_pct']}%)")
    print(f"预算总额:     {stats['total_budget']:,.1f} 万元")
    print(f"信息化项目:   {stats['it_projects']} 条")
    print(f"阶段类型数:   {quality['phase_types']} 种")
    print(f"质量等级:     {quality['quality']}")
    
    if quality["issues"]:
        print(f"⚠ 发现 {len(quality['issues'])} 个问题:")
        for issue in quality["issues"]:
            print(f"  - {issue}")
    
    print(f"\n=== 同步完成 ===")


if __name__ == "__main__":
    main()

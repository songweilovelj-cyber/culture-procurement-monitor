#!/usr/bin/env python3
"""
中国政府采购网 - 低频安全爬虫
============================
特性：
- 每次请求间隔 8-15 秒随机延迟，避免反爬
- 每个关键词只取 1-2 页，减少请求量
- 使用 session 复用连接
- 中标公告单独搜索，确保获取中标单位
- 先跑通小数据集（预计100-200条），后续可增量
"""
import requests
import re
import json
import time
import os
import random
import sys
from urllib.parse import urljoin
from datetime import datetime

# ============ 安全配置 ============
BASE_URL = "http://www.ccgp.gov.cn"
SEARCH_URL = "http://search.ccgp.gov.cn/bxsearch"
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd(), "ccgp_data.json")
START_DATE = "2026:01:01"
END_DATE = datetime.now().strftime("%Y:%m:%d")

# 减少关键词数量，只保留核心
KEYWORD_GROUPS = [
    ("智慧文旅", "旅游"),
    ("文化 数字化", "文化"),
    ("体育 信息化", "体育"),
    ("融媒体 平台", "宣传"),
    ("智慧旅游 系统", "旅游"),
    ("文物 数字化", "文化"),
    ("广电 信息化", "宣传"),
]

# 中标公告单独搜索（公告类型=中标公告）
# 搜索结果页的 bidType 参数: 空=全部, 不同的值对应不同类型
WIN_SEARCHES = [
    ("文化 中标 信息化", "文化"),
    ("旅游 中标 数字化", "旅游"),
    ("融媒体 中标", "宣传"),
    ("智慧文旅 中标", "旅游"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

TIMEOUT = 30
MIN_DELAY = 8      # 最小延迟（秒）
MAX_DELAY = 15     # 最大延迟（秒）
DETAIL_DELAY = (5, 10)  # 详情页延迟
MAX_PAGES = 2      # 每个关键词最多2页
MAX_DETAILS = 30   # 最多获取30个详情页的中标信息
SEEN_URLS = set()  # URL 去重


def safe_sleep(min_sec, max_sec=None):
    """随机延迟，模拟人类浏览"""
    if max_sec is None:
        max_sec = min_sec + 3
    delay = random.uniform(min_sec, max_sec)
    print(f"  [延迟] {delay:.1f} 秒...")
    time.sleep(delay)


def fetch_url(session, url, params=None):
    """安全发送GET请求"""
    try:
        resp = session.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        resp.encoding = 'utf-8'
        if resp.status_code == 200:
            return resp.text
        elif resp.status_code == 403:
            print(f"  [警告] 403 Forbidden - 可能被反爬拦截")
            return None
        elif resp.status_code == 429:
            print(f"  [警告] 429 Too Many Requests - 被限流，等待30秒...")
            time.sleep(30)
            return None
        else:
            print(f"  [警告] HTTP {resp.status_code}")
            return None
    except requests.exceptions.Timeout:
        print(f"  [警告] 请求超时")
        return None
    except Exception as e:
        print(f"  [错误] {e}")
        return None


def extract_province(text):
    """从文本中提取省份"""
    province_list = [
        "北京", "天津", "上海", "重庆",
        "河北", "山西", "内蒙古", "辽宁", "吉林", "黑龙江",
        "江苏", "浙江", "安徽", "福建", "江西", "山东",
        "河南", "湖北", "湖南", "广东", "广西", "海南",
        "四川", "贵州", "云南", "西藏",
        "陕西", "甘肃", "青海", "宁夏", "新疆",
    ]
    for p in province_list:
        if p in text:
            return p
    return "部委"


def extract_phase(phase_text, url_path=""):
    """标准化公告类型"""
    phase_text = phase_text.strip()
    # URL路径也能提示类型
    url_lower = url_path.lower()
    
    if "zbgg" in url_lower or "中标" in url_lower or "成交" in url_lower:
        return "中标公示"
    if "cgyx" in url_lower or "意向" in url_lower:
        return "采购意向"
    if "htgg" in url_lower or "合同" in url_lower:
        return "合同签订"
    
    mapping = {
        "公开招标公告": "招标公告", "公开招标": "招标公告",
        "竞争性磋商公告": "招标公告", "竞争性磋商": "招标公告",
        "竞争性谈判公告": "招标公告", "竞争性谈判": "招标公告",
        "询价公告": "招标公告",
        "单一来源公示": "采购意向", "采购意向": "采购意向",
        "中标公告": "中标公示", "成交公告": "中标公示",
        "成交结果公告": "中标公示", "结果公告": "中标公示",
        "中标（成交）结果公告": "中标公示",
        "更正公告": "招标公告",
        "废标公告": "其他", "终止公告": "其他",
        "合同公告": "合同签订", "资格预审公告": "招标公告",
    }
    for key, val in mapping.items():
        if key in phase_text:
            return val
    return "招标公告"


def extract_budget(text):
    """从文本中提取预算/中标金额（万元）"""
    patterns = [
        (r'预算金额[：:]\s*([\d,]+\.?\d*)\s*万元', True),
        (r'预算金额[：:]\s*([\d,]+\.?\d*)\s*元', False),
        (r'中标[（(]成交[）)]金额[：:]\s*([\d,]+\.?\d*)\s*万元', True),
        (r'中标[（(]成交[）)]金额[：:]\s*([\d,]+\.?\d*)\s*元', False),
        (r'中标金额[：:]\s*([\d,]+\.?\d*)\s*万元', True),
        (r'中标金额[：:]\s*([\d,]+\.?\d*)\s*元', False),
        (r'预算金额[（(]万元[）)][：:]*\s*([\d,]+\.?\d*)', True),
        (r'中标[（(]成交[）)]金额[（(]万元[）)][：:]*\s*([\d,]+\.?\d*)', True),
    ]
    for pat, is_wan in patterns:
        m = re.search(pat, text)
        if m:
            val = float(m.group(1).replace(',', ''))
            return val if is_wan else val / 10000
    return None


def extract_winner(html):
    """从中标详情页提取中标单位"""
    if not html:
        return None
    
    # 清理HTML标签
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    
    patterns = [
        r'中标成交供应商名称[：:]\s*([^\s，。,\.]{2,40}(?:公司|集团|中心|机构|研究所|实验室|事务所|行|社|部|台|局|会|院|馆|处|站|室|大学|学院))',
        r'中标[（(]成交[）)]供应商名称[：:]\s*([^\s，。,\.]{2,40}(?:公司|集团|中心|机构|研究所|实验室|事务所|行|社|部|台|局|会|院|馆|处|站|室|大学|学院))',
        r'供应商名称[：:]\s*([^\s，。,\.]{2,40}(?:公司|集团|中心|机构|研究所|实验室|事务所|行|社|部|台|局|会|院|馆|处|站|室|大学|学院))',
        r'中标供应商[：:]\s*([^\s，。,\.]{2,40}(?:公司|集团|中心|机构|研究所|实验室|事务所|行|社|部|台|局|会|院|馆|处|站|室|大学|学院))',
        r'成交供应商[：:]\s*([^\s，。,\.]{2,40}(?:公司|集团|中心|机构|研究所|实验室|事务所|行|社|部|台|局|会|院|馆|处|站|室|大学|学院))',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            winner = m.group(1).strip()
            # 过滤掉明显不是公司名的
            if len(winner) >= 6 and not winner.startswith("符合") and not winner.startswith("满足"):
                return winner
    return None


def parse_search_results(html, industry, is_win_search=False):
    """解析搜索结果列表页"""
    if not html:
        return []
    
    projects = []
    
    # 找到所有项目条目
    # 每条记录通常在一个 <li> 里，包含链接、日期、公告类型等
    items = re.findall(r'<li[^>]*?>(.*?)</li>', html, re.DOTALL)
    
    for item in items:
        # 找链接
        link_match = re.search(r'<a[^>]*?href=[\"\']([^\"\']*(?:cggg|cgyx|zbgg|htgg|zhongbiao|cjgg)[^\"\']*?)[\"\']([^>]*?)>(.*?)</a>', item, re.DOTALL)
        if not link_match:
            # 尝试其他链接模式
            link_match = re.search(r'<a[^>]*?href=[\"\']([^\"\']+(?:cggg|cgyx)[^\"\']*?)[\"\']([^>]*?)>(.*?)</a>', item, re.DOTALL)
        if not link_match:
            continue
        
        url_path = link_match.group(1)
        title_raw = link_match.group(3)
        
        # 清理标题
        title = re.sub(r'<.*?>', '', title_raw).strip()
        title = re.sub(r'\s+', ' ', title)
        title = title.replace('&nbsp;', ' ').replace('&amp;', '&')
        
        if not title or len(title) < 10:
            continue
        
        # URL去重
        clean_url = url_path.replace('&amp;', '&')
        if clean_url in SEEN_URLS:
            continue
        SEEN_URLS.add(clean_url)
        
        # 构造完整URL
        full_url = clean_url if clean_url.startswith('http') else urljoin(BASE_URL, clean_url)
        
        # 提取公告类型
        phase_text = ""
        phase_match = re.search(r'<strong>(.*?)</strong>', item)
        if phase_match:
            phase_text = phase_match.group(1)
        
        phase = extract_phase(phase_text, clean_url)
        
        # 如果是中标搜索，但结果不是中标，跳过
        if is_win_search and phase != "中标公示":
            continue
        
        # 提取日期
        date_match = re.search(r'(\d{4})[年./-](\d{1,2})[月./-](\d{1,2})', item)
        if date_match:
            date_str = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"
        else:
            date_str = ""
        
        # 提取预算
        budget = extract_budget(item)
        
        # 提取采购人
        buyer = ""
        buyer_match = re.search(r'采购人[：:]\s*([^<\n]{2,40})', item)
        if buyer_match:
            buyer = buyer_match.group(1).strip()
        
        # 提取代理机构
        agent = ""
        agent_match = re.search(r'代理机构[：:]\s*([^<\n]{2,50})', item)
        if agent_match:
            agent = agent_match.group(1).strip()
        
        # 提取省份
        province = extract_province(item)
        if province == "部委":
            province = extract_province(title)
        if province == "部委" and buyer:
            province = extract_province(buyer)
        
        # 是否为信息化项目
        it_keywords = ["信息化", "数字化", "智慧", "数据", "软件", "系统", "网络", "平台",
                       "融媒体", "AI", "人工智能", "区块链", "云", "大数据", "物联网", "5G",
                       "IT", "信息系统", "信息安全", "运维", "门户网站", "APP", "小程序",
                       "数据库", "服务器", "存储", "算力", "算法", "模型"]
        is_it = any(kw in title for kw in it_keywords)
        
        # 行业判断
        industry_kw = {
            "文化": ["文化", "博物馆", "图书馆", "文化馆", "非遗", "文物", "美术馆", "文艺"],
            "旅游": ["旅游", "文旅", "景区", "酒店", "旅行社", "游客", "全域旅游"],
            "体育": ["体育", "运动", "健身", "竞技", "赛事", "体彩", "彩票"],
            "宣传": ["宣传", "融媒体", "广电", "新闻", "传媒", "出版", "舆情", "广播", "电视"],
        }
        detected_industry = industry
        for ind, kws in industry_kw.items():
            if any(kw in title for kw in kws):
                detected_industry = ind
                break
        
        # 信息化类型
        it_type_map = {
            "数字化转型": ["数字化", "转型"],
            "智慧平台": ["智慧平台", "智慧", "智能"],
            "大数据中心": ["大数据", "数据中台", "数据中心"],
            "融媒体平台": ["融媒体", "融媒"],
            "数字化博物馆": ["博物馆", "文物"],
            "智慧体育": ["体育", "运动"],
            "云服务": ["云", "云计算"],
            "数字内容管理": ["内容管理", "CMS", "发布系统"],
            "网络安全": ["安全", "等保", "攻防"],
            "AI应用": ["AI", "人工智能", "智能分析"],
            "网络建设": ["网络", "带宽", "5G"],
            "系统集成": ["集成", "系统建设"],
            "运维服务": ["运维", "维护", "维保"],
        }
        it_type = "信息化建设"
        if is_it:
            for tt, kws in it_type_map.items():
                if any(kw in title for kw in kws):
                    it_type = tt
                    break
        
        # 部委判断
        ministry_keywords = ["中华人民共和国", "国家", "中央", "全国", "部", "局", "总局", "委员会"]
        is_ministry = province == "部委" or any(m in buyer for m in ministry_keywords)
        
        project = {
            "id": f"WT-2026-{abs(hash(clean_url)) % 1000000:06d}",
            "title": title,
            "url": full_url,
            "industry": detected_industry,
            "province": province,
            "phase": phase,
            "budget": budget,
            "agency": buyer,
            "agent": agent,
            "date": date_str,
            "isIT": is_it,
            "itType": it_type if is_it else None,
            "isMinistry": is_ministry,
            "winner": None,
        }
        projects.append(project)
    
    return projects


def search_keyword(session, keyword, industry, is_win=False):
    """搜索一个关键词"""
    all_projects = []
    
    for page in range(1, MAX_PAGES + 1):
        params = {
            "searchtype": "1",
            "page_index": str(page),
            "bidSort": "0",
            "buyerName": "",
            "projectId": "",
            "pinMu": "0",
            "bidType": "0",
            "dbselect": "bidx",
            "kw": keyword,
            "start_time": START_DATE,
            "end_time": END_DATE,
            "timeType": "6",
            "displayZone": "",
            "zoneId": "",
            "pppStatus": "0",
            "agentName": "",
        }
        
        page_type = "中标" if is_win else "全部"
        print(f"  [搜索] 关键词='{keyword}' ({page_type}), 第{page}/{MAX_PAGES}页")
        html = fetch_url(session, SEARCH_URL, params)
        
        if not html:
            print(f"  [跳过] 第{page}页请求失败")
            break
        
        # 检查结果数
        count_match = re.search(r'共找到\s*(\d+)\s*条', html)
        if count_match:
            total = int(count_match.group(1))
            print(f"  [信息] 共 {total} 条结果")
            if total == 0:
                break
        
        projects = parse_search_results(html, industry, is_win)
        
        if not projects:
            print(f"  [结束] 无更多结果")
            break
        
        print(f"  [提取] 第{page}页获取 {len(projects)} 个项目")
        all_projects.extend(projects)
        
        # 关键：随机延迟
        safe_sleep(MIN_DELAY, MAX_DELAY)
    
    return all_projects


def enrich_winners(session, projects):
    """为中标项目获取中标单位 - 低频版本"""
    win_projects = [p for p in projects if p["phase"] == "中标公示" and not p.get("winner")]
    print(f"\n>>> 需要获取中标单位: {len(win_projects)} 个项目")
    
    to_fetch = win_projects[:MAX_DETAILS]  # 最多处理30个
    fetched = 0
    
    for proj in to_fetch:
        if not proj.get("url"):
            continue
        
        print(f"  [详情 {fetched+1}/{len(to_fetch)}] {proj['title'][:45]}...")
        html = fetch_url(session, proj["url"])
        
        if html:
            winner = extract_winner(html)
            if winner:
                proj["winner"] = winner
                print(f"    -> 中标: {winner}")
                fetched += 1
            else:
                print(f"    -> 未提取到中标单位")
        
        safe_sleep(DETAIL_DELAY[0], DETAIL_DELAY[1])
    
    print(f"  成功获取 {fetched} 个中标单位")
    return projects


def main():
    print("=" * 60)
    print("中国政府采购网 - 低频安全爬虫 v2")
    print(f"数据范围: {START_DATE} 至 {END_DATE}")
    print(f"请求间隔: {MIN_DELAY}-{MAX_DELAY} 秒/次")
    print(f"搜索关键词: {len(KEYWORD_GROUPS)} 组常规 + {len(WIN_SEARCHES)} 组中标")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    all_projects = []
    
    # 阶段1: 常规搜索（全部类型）
    print("\n>>> 阶段1: 常规搜索（全部公告类型）")
    for keyword, industry in KEYWORD_GROUPS:
        print(f"\n>> 关键词: '{keyword}' -> {industry}")
        projects = search_keyword(session, keyword, industry, is_win=False)
        print(f">> 获得 {len(projects)} 个项目")
        all_projects.extend(projects)
        # 关键词之间额外延迟
        safe_sleep(MIN_DELAY + 3, MAX_DELAY + 3)
    
    # 阶段2: 中标公告搜索
    print("\n>>> 阶段2: 中标公告专项搜索")
    for keyword, industry in WIN_SEARCHES:
        print(f"\n>> 中标搜索: '{keyword}' -> {industry}")
        projects = search_keyword(session, keyword, industry, is_win=True)
        print(f">> 获得 {len(projects)} 个中标项目")
        all_projects.extend(projects)
        safe_sleep(MIN_DELAY + 3, MAX_DELAY + 3)
    
    # 去重
    unique_projects = {p["url"]: p for p in all_projects}.values()
    unique_projects = sorted(unique_projects, key=lambda x: x.get("date", ""), reverse=True)
    
    print(f"\n{'=' * 60}")
    print(f"去重后共 {len(unique_projects)} 个项目")
    
    # 阶段3: 获取中标单位
    unique_projects = enrich_winners(session, list(unique_projects))
    
    # 统计
    stats = {
        "total": len(unique_projects),
        "by_industry": {},
        "by_province": {},
        "by_phase": {},
        "it_projects": 0,
        "with_winner": 0,
        "with_budget": 0,
        "total_budget": 0,
    }
    for p in unique_projects:
        ind = p["industry"]
        stats["by_industry"][ind] = stats["by_industry"].get(ind, 0) + 1
        prov = p["province"]
        stats["by_province"][prov] = stats["by_province"].get(prov, 0) + 1
        ph = p["phase"]
        stats["by_phase"][ph] = stats["by_phase"].get(ph, 0) + 1
        if p["isIT"]:
            stats["it_projects"] += 1
        if p.get("winner"):
            stats["with_winner"] += 1
        if p.get("budget") and p["budget"] > 0:
            stats["with_budget"] += 1
            stats["total_budget"] += p["budget"]
    
    # 保存数据
    output = {
        "generated_at": datetime.now().isoformat(),
        "data_range": {
            "start": START_DATE.replace(":", "-"),
            "end": END_DATE.replace(":", "-")
        },
        "statistics": stats,
        "projects": unique_projects,
    }
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"数据已保存: {DATA_FILE}")
    print(f"总项目数: {stats['total']}")
    print(f"  - 文化: {stats['by_industry'].get('文化', 0)}")
    print(f"  - 旅游: {stats['by_industry'].get('旅游', 0)}")
    print(f"  - 体育: {stats['by_industry'].get('体育', 0)}")
    print(f"  - 宣传: {stats['by_industry'].get('宣传', 0)}")
    print(f"  - 信息化项目: {stats['it_projects']}")
    print(f"  - 含中标单位: {stats['with_winner']}")
    print(f"  - 含预算金额: {stats['with_budget']}")
    print(f"  - 省份覆盖: {len(stats['by_province'])} 个")
    print(f"阶段分布: {json.dumps(stats['by_phase'], ensure_ascii=False)}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

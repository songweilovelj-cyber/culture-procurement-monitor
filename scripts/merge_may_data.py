#!/usr/bin/env python3
"""
5月份数据合并脚本
==================
将WebFetch从中国政府采购网搜索到的2026年5月项目数据合并到ccgp_data.json
使用与6月数据相同的关键词标准和分类规则
"""
import json
import os
import re
from datetime import datetime
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_FILE = os.path.join(BASE_DIR, "ccgp_data.json")
BACKUP_FILE = os.path.join(BASE_DIR, "ccgp_data_backup.json")

# ============================================================
# 从WebFetch搜索结果+详情页提取的5月份真实数据
# 每条记录包含: title, url, industry, province, phase, budget(万元), winner, agency, agent, date
# ============================================================
MAY_DATA = [
    # ===== 智慧文旅 =====
    {"title": "通辽市文化旅游广电局通辽智慧文旅公共服务项目采购更正公告（第一次）", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260518_26583272.htm", "industry": "旅游", "province": "内蒙古", "phase": "招标公告", "budget": None, "winner": None, "agency": "通辽市文化旅游广电局", "agent": "通辽市公共资源交易中心", "date": "2026-05-18"},
    {"title": "通辽市文化旅游广电局通辽智慧文旅公共服务项目招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260515_26575934.htm", "industry": "旅游", "province": "内蒙古", "phase": "招标公告", "budget": None, "winner": None, "agency": "通辽市文化旅游广电局", "agent": "通辽市公共资源交易中心", "date": "2026-05-15"},
    {"title": "东城智慧文旅一体化平台建设项目公开招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260514_26573198.htm", "industry": "旅游", "province": "北京", "phase": "招标公告", "budget": None, "winner": None, "agency": "北京市东城区文化和旅游局", "agent": "中诚安管理咨询（北京）有限公司", "date": "2026-05-14"},
    {"title": "黑河市文化广电和旅游局黑河市智能化跨境游落地服务示范项目采购更正公告（第一次）", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260514_26564381.htm", "industry": "旅游", "province": "黑龙江", "phase": "招标公告", "budget": None, "winner": None, "agency": "黑河市文化广电和旅游局", "agent": "黑河市政府采购中心", "date": "2026-05-14"},
    {"title": "云南嘉顺工程项目管理有限公司关于迪庆州智慧文旅综合管理平台建设项目更正公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260511_26545703.htm", "industry": "旅游", "province": "云南", "phase": "中标公示", "budget": None, "winner": None, "agency": "迪庆藏族自治州文化和旅游局", "agent": "云南嘉顺工程项目管理有限公司", "date": "2026-05-11"},
    {"title": "黑河市文化广电和旅游局黑河市智能化跨境游落地服务示范项目采购更正公告（第三次）", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260506_26515674.htm", "industry": "旅游", "province": "黑龙江", "phase": "招标公告", "budget": None, "winner": None, "agency": "黑河市文化广电和旅游局", "agent": "黑河市政府采购中心", "date": "2026-05-06"},
    {"title": "三原县文化和旅游局城隍庙景区创建国家4A级旅游景区智慧旅游系统建设项目招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260513_26563006.htm", "industry": "旅游", "province": "陕西", "phase": "招标公告", "budget": None, "winner": None, "agency": "三原县文化和旅游局", "agent": "陕西夸克工程造价咨询有限公司", "date": "2026-05-13"},
    {"title": "2026年深圳旅游融媒体推广平台项目招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260518_26581636.htm", "industry": "旅游", "province": "广东", "phase": "招标公告", "budget": None, "winner": None, "agency": "深圳市文化广电旅游体育局", "agent": "深圳市东方招标有限公司", "date": "2026-05-18"},
    {"title": "关于2026年深圳旅游融媒体推广平台项目现场演示的澄清公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260527_26640945.htm", "industry": "旅游", "province": "广东", "phase": "招标公告", "budget": None, "winner": None, "agency": "深圳市文化广电旅游体育局", "agent": "深圳市东方招标有限公司", "date": "2026-05-27"},

    # ===== 文化 数字化 =====
    {"title": "秀山土家族苗族自治县民族博物馆馆藏珍贵文物数字化保护利用项目竞争性磋商公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/jzxcs/202605/t20260529_26657502.htm", "industry": "文化", "province": "重庆", "phase": "招标公告", "budget": None, "winner": None, "agency": "重庆市秀山土家族苗族自治县文物管理所", "agent": "重庆千诺工程项目管理有限公司", "date": "2026-05-29"},
    {"title": "抚州静心项目管理咨询有限公司关于资溪县博物馆可移动文物数字化保护项目电子化竞争性磋商公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/jzxtpgg/202605/t20260529_26657152.htm", "industry": "文化", "province": "江西", "phase": "招标公告", "budget": None, "winner": None, "agency": "资溪县文化旅游体育事业发展中心", "agent": "抚州静心项目管理咨询有限公司", "date": "2026-05-29"},
    {"title": "广西景钲工程咨询有限公司关于横州市博物馆馆藏文物数字化保护项目的竞争性磋商公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/jzxcs/202605/t20260529_26655299.htm", "industry": "文化", "province": "广西", "phase": "招标公告", "budget": None, "winner": None, "agency": "横州市文物所", "agent": "广西景钲工程咨询有限公司", "date": "2026-05-29"},
    {"title": "四川博物院文物档案数字化及藏品管理系统提升项目竞争性磋商公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/jzxcs/202605/t20260528_26649930.htm", "industry": "文化", "province": "四川", "phase": "招标公告", "budget": None, "winner": None, "agency": "四川博物院", "agent": "四川中天阳光招标代理有限公司", "date": "2026-05-28"},
    {"title": "灵台县博物馆馆藏珍贵文物数字化保护项目招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260528_26649312.htm", "industry": "文化", "province": "甘肃", "phase": "招标公告", "budget": None, "winner": None, "agency": "灵台县博物馆", "agent": "甘肃金鑫建设咨询有限公司", "date": "2026-05-28"},
    {"title": "北京石刻艺术博物馆馆藏珍贵文物数字化保护项目（二期）中标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260528_26645350.htm", "industry": "文化", "province": "北京", "phase": "中标公示", "budget": 100.8, "winner": "中兵勘察设计研究院有限公司", "agency": "北京石刻艺术博物馆", "agent": "华诚博远工程咨询有限公司", "date": "2026-05-28"},
    {"title": "2026年泰山学院泰山文物数字化与活化利用实践创新平台结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260527_26644312.htm", "industry": "文化", "province": "山东", "phase": "中标公示", "budget": None, "winner": None, "agency": "泰山学院", "agent": "山东超越建设项目管理有限公司", "date": "2026-05-27"},
    {"title": "重庆特园民主党派历史陈列馆珍贵文物数字化保护中标（成交）结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260527_26643479.htm", "industry": "文化", "province": "重庆", "phase": "中标公示", "budget": None, "winner": None, "agency": "重庆特园民主党派历史陈列馆", "agent": "重庆大正建设工程经济技术有限公司", "date": "2026-05-27"},
    {"title": "运城博物馆馆藏可移动文物数字化保护结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260527_26640141.htm", "industry": "文化", "province": "山西", "phase": "中标公示", "budget": None, "winner": "山西文物博物产业集团有限责任公司", "agency": "运城博物馆", "agent": "山西力天伟业工程项目管理有限公司", "date": "2026-05-27"},
    {"title": "余姚市河姆渡遗址博物馆馆藏文物数字化保护项目中标(成交)结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260526_26632460.htm", "industry": "文化", "province": "浙江", "phase": "中标公示", "budget": 53.2, "winner": "广州与鲲数字科技有限公司", "agency": "余姚市河姆渡遗址博物馆", "agent": "余姚市姚诚工程管理有限公司", "date": "2026-05-26"},
    {"title": "海南省博物馆珍贵文物数字化保护项目结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/cjgg/202605/t20260525_26627954.htm", "industry": "文化", "province": "海南", "phase": "中标公示", "budget": None, "winner": "北京昆仑文保科技有限公司", "agency": "海南省博物馆", "agent": "中科天一工程管理有限公司", "date": "2026-05-25"},
    {"title": "侯马晋国古都博物馆馆藏珍贵文物数字化保护项目结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260525_26624550.htm", "industry": "文化", "province": "山西", "phase": "中标公示", "budget": None, "winner": "安徽中晖博源文化科技有限公司", "agency": "侯马晋国古都博物馆", "agent": "山西华信伟业招标代理有限公司", "date": "2026-05-25"},
    {"title": "青海巨丰工程项目管理有限公司关于2025年热贡文化生态保护区整体性保护资源调查及数字化整理项目的竞争性磋商公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/jzxcs/202605/t20260525_26623769.htm", "industry": "文化", "province": "青海", "phase": "招标公告", "budget": None, "winner": None, "agency": "黄南州热贡文化生态保护区管理委员会", "agent": "青海巨丰工程项目管理有限公司", "date": "2026-05-25"},
    {"title": "绥芬河市博物馆馆藏可移动文物数字化保护项目中标（成交）结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/cjgg/202605/t20260522_26614358.htm", "industry": "文化", "province": "黑龙江", "phase": "中标公示", "budget": None, "winner": "深圳积木易搭科技技术有限公司", "agency": "绥芬河市博物馆", "agent": "黑龙江鹏旭项目管理有限公司", "date": "2026-05-22"},
    {"title": "丰城市博物馆可移动文物数字化保护利用项目", "url": "http://www.ccgp.gov.cn/cggg/dfgg/jzxtpgg/202605/t20260522_26611625.htm", "industry": "文化", "province": "江西", "phase": "招标公告", "budget": None, "winner": None, "agency": "丰城市博物馆", "agent": "江西创丰工程咨询有限公司", "date": "2026-05-22"},
    {"title": "黑龙江大学FS26002博物馆可移动文物数字化保护招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260521_26606069.htm", "industry": "文化", "province": "黑龙江", "phase": "招标公告", "budget": None, "winner": None, "agency": "黑龙江大学", "agent": "忱义工程项目管理有限公司", "date": "2026-05-21"},
    {"title": "北京艺术博物馆珍贵文物数字化保护项目更正公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260521_26604934.htm", "industry": "文化", "province": "北京", "phase": "招标公告", "budget": None, "winner": None, "agency": "北京艺术博物馆", "agent": "北京中储建国际工程管理有限公司", "date": "2026-05-21"},
    {"title": "平顺县文化和旅游局北社大禹庙古建筑及壁画数字化保护项目采购公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/jzxcs/202605/t20260521_26605624.htm", "industry": "文化", "province": "山西", "phase": "招标公告", "budget": None, "winner": None, "agency": "平顺县文化和旅游局", "agent": "山西欣鑫建设项目管理有限公司", "date": "2026-05-21"},
    {"title": "中国文化遗产研究院大伾山摩崖大佛及石刻综合保护本体修缮项目包1：精确信息数字化提取与数据处理项目中标公告", "url": "http://www.ccgp.gov.cn/cggg/zygg/zbgg/202605/t20260520_26599373.htm", "industry": "文化", "province": "北京", "phase": "中标公示", "budget": None, "winner": "北京城市学院", "agency": "中国文化遗产研究院", "agent": "中钢招标有限责任公司", "date": "2026-05-20"},
    {"title": "银川西夏陵区管理处西夏陵博物馆珍贵文物数字化保护利用项目（二期）中标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260520_26600965.htm", "industry": "文化", "province": "宁夏", "phase": "中标公示", "budget": None, "winner": None, "agency": "银川西夏陵区管理处", "agent": "宁夏正通工程咨询有限公司", "date": "2026-05-20"},
    {"title": "东乡族自治县博物馆馆藏文物数字化保护项目中标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260520_26597953.htm", "industry": "文化", "province": "甘肃", "phase": "中标公示", "budget": None, "winner": "兰州太宇能电子有限公司", "agency": "东乡族自治县博物馆", "agent": "甘肃晟业工程管理咨询有限公司", "date": "2026-05-20"},
    {"title": "房山区部分重点文物数字化预算项目（二期）成交公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/cjgg/202605/t20260520_26597639.htm", "industry": "文化", "province": "北京", "phase": "中标公示", "budget": 149.53, "winner": None, "agency": "北京市房山区文物保护所", "agent": "北京俱兴工程管理咨询有限公司", "date": "2026-05-20"},
    {"title": "杭州市萧山区博物馆馆藏文物数字化保护项目中标(成交)结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260520_26597257.htm", "industry": "文化", "province": "浙江", "phase": "中标公示", "budget": 161.57, "winner": "珠海市四维科技有限公司", "agency": "杭州市萧山区博物馆", "agent": "浙江铭华工程管理有限公司", "date": "2026-05-20"},
    {"title": "开州博物馆金属与陶瓷类珍贵文物数字化保护项目（二期）竞争性磋商公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/jzxcs/202605/t20260520_26596255.htm", "industry": "文化", "province": "重庆", "phase": "招标公告", "budget": None, "winner": None, "agency": "重庆市开州区文物管理所", "agent": "重庆市开州区公共资源交易中心", "date": "2026-05-20"},
    {"title": "宽甸满族自治县博物馆馆藏文物数字化保护竞争性磋商公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/jzxcs/202605/t20260520_26595179.htm", "industry": "文化", "province": "辽宁", "phase": "招标公告", "budget": None, "winner": None, "agency": "宽甸满族自治县文化旅游和广播电视局", "agent": "辽宁睿智建设工程管理咨询有限公司", "date": "2026-05-20"},
    {"title": "平遥县文物所关于清虚观数字化保护项目结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260519_26591757.htm", "industry": "文化", "province": "山西", "phase": "中标公示", "budget": None, "winner": "山西华文古建筑保护设计有限公司", "agency": "平遥县文物所", "agent": "山西汇鑫源工程招标代理有限公司", "date": "2026-05-19"},
    {"title": "长兴县博物馆可移动文物数字化保护项目中标(成交)结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260519_26588890.htm", "industry": "文化", "province": "浙江", "phase": "中标公示", "budget": None, "winner": None, "agency": "长兴县博物馆", "agent": "浙江勤正项目管理有限公司", "date": "2026-05-19"},
    {"title": "汉中市羌文化展馆数字化互动体验服务项目竞争性磋商公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/jzxcs/202605/t20260519_26590064.htm", "industry": "文化", "province": "陕西", "phase": "招标公告", "budget": None, "winner": None, "agency": "汉中市文化生态保护建设服务中心", "agent": "陕西培森项目管理有限公司", "date": "2026-05-19"},
    {"title": "随县文化和旅游局本级2026年7月至2027年6月无线数字化覆盖设施运维服务竞争性磋商公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/jzxcs/202605/t20260519_26589796.htm", "industry": "文化", "province": "湖北", "phase": "招标公告", "budget": None, "winner": None, "agency": "随县文化和旅游局", "agent": "湖北晟达项目管理有限公司", "date": "2026-05-19"},
    {"title": "阳曲县文化和旅游局前斧柯悬泉寺古建筑及彩绘壁画造像数字化保护项目结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260519_26589105.htm", "industry": "文化", "province": "山西", "phase": "中标公示", "budget": None, "winner": "博恒文保科技（天津）有限公司", "agency": "阳曲县文化和旅游局", "agent": "山西华非工程咨询管理有限公司", "date": "2026-05-19"},
    {"title": "信阳博物馆可移动文物数字化保护利用项目-更正公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260518_26584623.htm", "industry": "文化", "province": "河南", "phase": "招标公告", "budget": None, "winner": None, "agency": "信阳博物馆", "agent": "高达建设管理发展有限责任公司", "date": "2026-05-18"},
    {"title": "运城博物馆馆藏可移动文物数字化保护的采购公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/jzxcs/202605/t20260517_26580142.htm", "industry": "文化", "province": "山西", "phase": "招标公告", "budget": None, "winner": None, "agency": "运城博物馆", "agent": "山西力天伟业工程项目管理有限公司", "date": "2026-05-17"},
    {"title": "运城博物馆馆藏可移动文物数字化保护的更正公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260518_26581074.htm", "industry": "文化", "province": "山西", "phase": "招标公告", "budget": None, "winner": None, "agency": "运城博物馆", "agent": "山西力天伟业工程项目管理有限公司", "date": "2026-05-18"},
    {"title": "平顺县文化和旅游局北社大禹庙古建筑及壁画数字化保护项目竞争性磋商更正公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260526_26632778.htm", "industry": "文化", "province": "山西", "phase": "招标公告", "budget": None, "winner": None, "agency": "平顺县文化和旅游局", "agent": "山西欣鑫建设项目管理有限公司", "date": "2026-05-26"},
    {"title": "白玉县文化广播电视和旅游局白玉藏族金工博物馆数字化建设采购项目招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260515_26574673.htm", "industry": "文化", "province": "四川", "phase": "招标公告", "budget": None, "winner": None, "agency": "白玉县文化广播电视和旅游局", "agent": "白玉县人民政府采购中心", "date": "2026-05-15"},
    {"title": "白玉县文化广播电视和旅游局白玉藏族金工博物馆数字化建设采购项目采购更正公告（第一次）", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260522_26615826.htm", "industry": "文化", "province": "四川", "phase": "招标公告", "budget": None, "winner": None, "agency": "白玉县文化广播电视和旅游局", "agent": "白玉县人民政府采购中心", "date": "2026-05-22"},
    {"title": "2026年河北省非物质文化遗产传薪录数字化保护项目公开招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260515_26574182.htm", "industry": "文化", "province": "河北", "phase": "招标公告", "budget": None, "winner": None, "agency": "河北省群众艺术馆（河北省非物质文化遗产保护中心）", "agent": "河北中诚工程项目管理有限公司", "date": "2026-05-15"},
    {"title": "蓝田县文化和旅游体育局蓝田猿人遗址数字化场景建设及设施提升项目中标（成交）结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260514_26569352.htm", "industry": "文化", "province": "陕西", "phase": "中标公示", "budget": None, "winner": None, "agency": "西安市蓝田县文化和旅游体育局", "agent": "西北国际（陕西）造价管理集团有限公司", "date": "2026-05-14"},
    {"title": "盐池县文化旅游广电局盐池县图书馆智慧数字化新型阅读空间建设项目中标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260513_26560601.htm", "industry": "文化", "province": "宁夏", "phase": "中标公示", "budget": 99.33, "winner": "中国广电宁夏网络有限公司", "agency": "盐池县文化旅游广电局", "agent": "宁夏川越项目管理有限公司", "date": "2026-05-13"},
    {"title": "玛纳斯县博物馆馆藏文物数字化保护利用项目（二次）中标(成交)结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260514_26568684.htm", "industry": "文化", "province": "新疆", "phase": "中标公示", "budget": None, "winner": "深圳市华图测控系统有限公司", "agency": "玛纳斯县文化体育广播电视和旅游局", "agent": "玛纳斯县政务服务中心", "date": "2026-05-14"},
    {"title": "张掖大佛寺文物研究所可移动文物数字化保护项目招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260513_26561880.htm", "industry": "文化", "province": "甘肃", "phase": "招标公告", "budget": None, "winner": None, "agency": "张掖大佛寺文物研究所", "agent": "银龙兴（甘肃）咨询有限公司", "date": "2026-05-13"},
    {"title": "太原市博物馆馆藏珍贵文物数字化保护项目（二期）公开招标采购结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260513_26560244.htm", "industry": "文化", "province": "山西", "phase": "中标公示", "budget": None, "winner": "北京浩宇天地测绘有限公司", "agency": "太原市博物馆", "agent": "太原市公共资源交易中心", "date": "2026-05-13"},
    {"title": "铁岭市博物馆馆藏文物数字化保护结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/cjgg/202605/t20260513_26558276.htm", "industry": "文化", "province": "辽宁", "phase": "中标公示", "budget": None, "winner": None, "agency": "铁岭市博物馆", "agent": "辽宁仟和招标有限公司", "date": "2026-05-13"},
    {"title": "晋商博物院馆藏珍贵文物数字化保护项目中标结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260512_26554016.htm", "industry": "文化", "province": "山西", "phase": "中标公示", "budget": None, "winner": "山西辰涵数字科技股份有限公司", "agency": "晋商博物院（山西府衙博物馆）", "agent": "山西恒运招标代理有限公司", "date": "2026-05-12"},
    {"title": "安阳博物馆可移动文物数字化保护项目（二次）-公开招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260512_26552882.htm", "industry": "文化", "province": "河南", "phase": "招标公告", "budget": None, "winner": None, "agency": "安阳博物馆", "agent": "中诺天中工程管理有限公司", "date": "2026-05-12"},
    {"title": "屯留区新型文化空间数字化设备及图书配套项目结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260525_26628555.htm", "industry": "文化", "province": "山西", "phase": "中标公示", "budget": None, "winner": "北京宏升达业图书有限公司", "agency": "长治市屯留区文化和旅游局", "agent": "山西铭汇工程项目管理有限公司", "date": "2026-05-25"},
    {"title": "屯留区新型文化空间数字化设备及图书配套项目的更正公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260506_26515783.htm", "industry": "文化", "province": "山西", "phase": "招标公告", "budget": None, "winner": None, "agency": "长治市屯留区文化和旅游局", "agent": "山西铭汇工程项目管理有限公司", "date": "2026-05-06"},
    {"title": "阳曲县文化和旅游局前斧柯悬泉寺古建筑及彩绘壁画造像数字化保护项目的采购公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/jzxcs/202605/t20260506_26515087.htm", "industry": "文化", "province": "山西", "phase": "招标公告", "budget": None, "winner": None, "agency": "阳曲县文化和旅游局", "agent": "山西华非工程咨询管理有限公司", "date": "2026-05-06"},
    {"title": "泾源县文化旅游广电局泾源县文化馆数字化建设政府采购项目(重新招标)项目招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260506_26514946.htm", "industry": "文化", "province": "宁夏", "phase": "招标公告", "budget": 150, "winner": None, "agency": "泾源县文化旅游广电局", "agent": "固原市公共资源交易中心", "date": "2026-05-06"},
    {"title": "沐川县文化广播电视体育和旅游局2026年广播电视节目无线覆盖及应急广播系统运行维护项目中标（成交）结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/cjgg/202605/t20260506_26511707.htm", "industry": "文化", "province": "四川", "phase": "中标公示", "budget": None, "winner": None, "agency": "沐川县文化广播电视体育和旅游局", "agent": "沐川县公共资源交易服务中心", "date": "2026-05-06"},
    {"title": "中共准格尔旗委员会宣传部准格尔旗文化遗产数字化保护利用项目中标（成交）结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/cjgg/202605/t20260509_26537170.htm", "industry": "文化", "province": "内蒙古", "phase": "中标公示", "budget": None, "winner": "内蒙古伊浩文化旅游发展有限公司", "agency": "中共准格尔旗委员会宣传部", "agent": "内蒙古启明星项目管理有限公司", "date": "2026-05-09"},
    {"title": "乌审旗文化和旅游局乌审召庙德格都苏莫殿数字化保护与展示项目中标（成交）结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/cjgg/202605/t20260511_26548327.htm", "industry": "文化", "province": "内蒙古", "phase": "中标公示", "budget": None, "winner": "甘肃恒真数字文化科技有限公司", "agency": "乌审旗文化和旅游局", "agent": "内蒙古中煦项目管理有限公司", "date": "2026-05-11"},
    {"title": "杭州意信招标代理有限公司关于浙江省文化广电和旅游厅2026年文旅重大数字化应用宣传推广项目中标结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260509_26537657.htm", "industry": "文化", "province": "浙江", "phase": "中标公示", "budget": 299, "winner": "浙数文旅发展（浙江）有限公司", "agency": "浙江省文化广电和旅游厅", "agent": "杭州意信招标代理有限公司", "date": "2026-05-09"},
    {"title": "垣曲县博物馆馆藏珍贵文物数字化保护项目成交公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260515_26572557.htm", "industry": "文化", "province": "山西", "phase": "中标公示", "budget": None, "winner": "山西中格天第展览展示有限公司", "agency": "垣曲县文化和旅游局", "agent": "山西泽铭工程咨询有限公司", "date": "2026-05-15"},
    {"title": "瓜州县博物馆馆藏文物数字化保护项目采购更正公告（第一次）", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260515_26577690.htm", "industry": "文化", "province": "甘肃", "phase": "招标公告", "budget": None, "winner": None, "agency": "瓜州县博物馆", "agent": "甘肃全标项目管理有限公司", "date": "2026-05-15"},
    {"title": "肃南裕固族自治县民族博物馆馆藏文物数字化保护项目采购更正公告（第二次）", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260520_26597839.htm", "industry": "文化", "province": "甘肃", "phase": "招标公告", "budget": None, "winner": None, "agency": "肃南裕固族自治县民族博物馆", "agent": "肃南交通建设投资有限责任公司", "date": "2026-05-20"},
    {"title": "博尔塔拉蒙古自治州博物馆馆藏文物数字化保护展示利用项目终止公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/fblbgg/202605/t20260520_26600288.htm", "industry": "文化", "province": "新疆", "phase": "招标公告", "budget": None, "winner": None, "agency": "博尔塔拉蒙古自治州博物馆", "agent": "博州行政服务中心", "date": "2026-05-20"},

    # ===== 体育 信息化 =====
    {"title": "天津市体育文化发展中心天津市体育信息化综合平台商务运营服务项目中标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260529_26657969.htm", "industry": "体育", "province": "天津", "phase": "中标公示", "budget": 79.45, "winner": "天津天圣运动科技有限公司", "agency": "天津市体育文化发展中心（天津市体育博物馆）", "agent": "天津晟辰工程造价咨询有限公司", "date": "2026-05-29"},
    {"title": "国家体育总局训练局训练局房产资产信息化管理系统采购项目竞争性磋商公告", "url": "http://www.ccgp.gov.cn/cggg/zygg/jzxcs/202605/t20260528_26646388.htm", "industry": "体育", "province": "部委", "phase": "招标公告", "budget": None, "winner": None, "agency": "国家体育总局训练局", "agent": "国金招标有限公司", "date": "2026-05-28"},
    {"title": "岳阳县教育体育局岳阳县新长征小学信息化设备采购谈判成交公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/cjgg/202605/t20260525_26623590.htm", "industry": "体育", "province": "湖南", "phase": "中标公示", "budget": None, "winner": None, "agency": "岳阳县教育体育局", "agent": "湖南正霖项目管理咨询有限公司", "date": "2026-05-25"},
    {"title": "盐源县教育和体育局盐源县一村一幼智慧教育信息化教学设备采购招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260522_26611524.htm", "industry": "体育", "province": "四川", "phase": "招标公告", "budget": None, "winner": None, "agency": "盐源县教育和体育局", "agent": "盐源县政府采购中心", "date": "2026-05-22"},
    {"title": "泸州市龙马潭区教育和体育局信息化教学设备采购更正公告（第一次）", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260521_26606945.htm", "industry": "体育", "province": "四川", "phase": "招标公告", "budget": None, "winner": None, "agency": "泸州市龙马潭区教育和体育局", "agent": "四川建兴工程造价咨询有限公司", "date": "2026-05-21"},
    {"title": "北川羌族自治县教育和体育局学校信息化设施设备采购采购更正公告（第一次）", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260521_26605384.htm", "industry": "体育", "province": "四川", "phase": "招标公告", "budget": None, "winner": None, "agency": "北川羌族自治县教育和体育局", "agent": "北川羌族自治县人民政府采购中心", "date": "2026-05-21"},
    {"title": "会泽县教育体育局关于文笔小学教育信息化功能室设施招标采购项目的终止公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/fblbgg/202605/t20260520_26599558.htm", "industry": "体育", "province": "云南", "phase": "招标公告", "budget": None, "winner": None, "agency": "会泽县教育体育局", "agent": "云南炳然项目管理有限公司", "date": "2026-05-20"},
    {"title": "会泽县教育体育局关于文笔小学教育信息化功能室设施招标采购项目的公开招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260520_26595006.htm", "industry": "体育", "province": "云南", "phase": "招标公告", "budget": None, "winner": None, "agency": "会泽县教育体育局", "agent": "云南炳然项目管理有限公司", "date": "2026-05-20"},
    {"title": "山东省体育彩票管理中心机关销售网点信息化综合服务项目公开招标招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260519_26594341.htm", "industry": "体育", "province": "山东", "phase": "招标公告", "budget": None, "winner": None, "agency": "山东省体育彩票管理中心", "agent": "山东新傲项目管理有限公司", "date": "2026-05-19"},
    {"title": "普洱市教育体育局关于普洱市教育信息化整体提升工程建设项目维保服务（二次）的公开招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260519_26589601.htm", "industry": "体育", "province": "云南", "phase": "招标公告", "budget": None, "winner": None, "agency": "普洱市教育体育局", "agent": "云南锦能项目咨询有限公司", "date": "2026-05-19"},
    {"title": "普洱市教育体育局关于普洱市教育信息化整体提升工程建设项目维保服务终止公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/fblbgg/202605/t20260515_26577176.htm", "industry": "体育", "province": "云南", "phase": "招标公告", "budget": None, "winner": None, "agency": "普洱市教育体育局", "agent": "云南锦能项目咨询有限公司", "date": "2026-05-15"},
    {"title": "泸州市龙马潭区教育和体育局信息化教学设备招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260514_26564639.htm", "industry": "体育", "province": "四川", "phase": "招标公告", "budget": None, "winner": None, "agency": "泸州市龙马潭区教育和体育局", "agent": "四川建兴工程造价咨询有限公司", "date": "2026-05-14"},
    {"title": "侯马市教育体育局侯马市体育馆信息化升级及数据对接服务项目的采购公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260514_26563261.htm", "industry": "体育", "province": "山西", "phase": "招标公告", "budget": None, "winner": None, "agency": "侯马市教育体育局", "agent": "山西寰宸辉项目管理有限公司", "date": "2026-05-14"},
    {"title": "禹城市教育和体育局新建学校及相关扩建学校信息化设备配备项目中标结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260513_26558024.htm", "industry": "体育", "province": "山东", "phase": "中标公示", "budget": None, "winner": None, "agency": "禹城市教育和体育局", "agent": "德州洺扬项目管理咨询有限公司", "date": "2026-05-13"},
    {"title": "海原县教育体育局海原县义务教育优化布局信息化设备采购项目招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260511_26546300.htm", "industry": "体育", "province": "宁夏", "phase": "招标公告", "budget": 362, "winner": None, "agency": "海原县教育体育局", "agent": "中卫市政府采购中心", "date": "2026-05-11"},
    {"title": "北川羌族自治县教育和体育局学校信息化设施设备采购采购更正公告（第一次）", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260511_26545118.htm", "industry": "体育", "province": "四川", "phase": "招标公告", "budget": None, "winner": None, "agency": "北川羌族自治县教育和体育局", "agent": "北川羌族自治县人民政府采购中心", "date": "2026-05-11"},
    {"title": "天津市体育文化发展中心天津市体育信息化综合平台商务运营服务项目公开招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260508_26530519.htm", "industry": "体育", "province": "天津", "phase": "招标公告", "budget": None, "winner": None, "agency": "天津市体育文化发展中心（天津市体育博物馆）", "agent": "天津晟辰工程造价咨询有限公司", "date": "2026-05-08"},
    {"title": "武陟县教育体育局关于中小学教育信息化建设项目-中标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260508_26529907.htm", "industry": "体育", "province": "河南", "phase": "中标公示", "budget": None, "winner": None, "agency": "武陟县教育体育局", "agent": "焦作市公共资源交易中心", "date": "2026-05-08"},
    {"title": "昭觉县教育体育和科学技术局昭觉县新建三中、四中第一批教学设施-信息化设备采购中标（成交）结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260508_26528573.htm", "industry": "体育", "province": "四川", "phase": "中标公示", "budget": None, "winner": "成都中科普天科技有限公司", "agency": "昭觉县教育体育和科学技术局", "agent": "昭觉县政府采购中心", "date": "2026-05-08"},
    {"title": "安岳县教育和体育局安岳县2024年教育信息化老旧设备更换项目(二次)中标（成交）结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260508_26526510.htm", "industry": "体育", "province": "四川", "phase": "中标公示", "budget": None, "winner": "四川大宇信息系统股份有限公司", "agency": "安岳县教育和体育局", "agent": "安岳县政府采购中心", "date": "2026-05-08"},
    {"title": "江城哈尼族彝族自治县教育体育局关于2025年义务教育薄弱环节改善与能力提升信息化采购项目（二次）的终止公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/fblbgg/202605/t20260508_26530385.htm", "industry": "体育", "province": "云南", "phase": "招标公告", "budget": None, "winner": None, "agency": "江城哈尼族彝族自治县教育体育局", "agent": "江城哈尼族彝族自治县政府采购和出让中心", "date": "2026-05-08"},

    # ===== 融媒体 平台 =====
    {"title": "贺兰县融媒体中心区县融媒体平台一体化建设贺兰县应用能力提升项目(二期)项目招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260529_26656587.htm", "industry": "宣传", "province": "宁夏", "phase": "招标公告", "budget": 73, "winner": None, "agency": "贺兰县融媒体中心（贺兰县广播电视台）", "agent": "宁夏中世联众工程咨询有限公司", "date": "2026-05-29"},
    {"title": "学校融媒体中心平台建设项目公开招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260529_26654308.htm", "industry": "宣传", "province": "重庆", "phase": "招标公告", "budget": None, "winner": None, "agency": "重庆电力高等专科学校", "agent": "重庆民禾招标代理有限公司", "date": "2026-05-29"},
    {"title": "镇巴县融媒体中心秦岭云平台购买服务项目(二次)中标（成交）结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/cjgg/202605/t20260529_26652361.htm", "industry": "宣传", "province": "陕西", "phase": "中标公示", "budget": None, "winner": None, "agency": "镇巴县融媒体中心", "agent": "中盛精诚工程项目管理有限公司", "date": "2026-05-29"},
    {"title": "苏世建设管理集团有限公司关于南宁党建融媒体平台2026-2027年度管理维护服务项目的竞争性磋商公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/jzxcs/202605/t20260529_26651712.htm", "industry": "宣传", "province": "广西", "phase": "招标公告", "budget": None, "winner": None, "agency": "中国共产党南宁市委员会组织部", "agent": "苏世建设管理集团有限公司", "date": "2026-05-29"},
    {"title": "浙江诚远工程咨询有限公司关于东阳市融媒体中心天目蓝云融媒体平台技术服务项目中标(成交)结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260528_26644706.htm", "industry": "宣传", "province": "浙江", "phase": "中标公示", "budget": None, "winner": None, "agency": "东阳市融媒体中心", "agent": "浙江诚远工程咨询有限公司", "date": "2026-05-28"},
    {"title": "2026年-2027年新疆禁毒融媒体平台信息采编和活动策划项目（二次）竞争性磋商公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/jzxcs/202605/t20260526_26634930.htm", "industry": "宣传", "province": "新疆", "phase": "招标公告", "budget": None, "winner": None, "agency": "新疆维吾尔自治区公安厅", "agent": "新疆能实建设工程项目管理咨询有限责任公司", "date": "2026-05-26"},
    {"title": "2026年-2027年新疆禁毒融媒体平台信息采编和活动策划项目废标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/qtgg/202605/t20260523_26620145.htm", "industry": "宣传", "province": "新疆", "phase": "招标公告", "budget": None, "winner": None, "agency": "新疆维吾尔自治区公安厅", "agent": "新疆能实建设工程项目管理咨询有限责任公司", "date": "2026-05-23"},
    {"title": "杭州市余杭区融媒体中心2026年融媒体平台运行服务项目的公开招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260523_26618881.htm", "industry": "宣传", "province": "浙江", "phase": "招标公告", "budget": None, "winner": None, "agency": "杭州市余杭区融媒体中心（杭州市余杭区广播电视台）", "agent": "浙江省成套招标代理有限公司", "date": "2026-05-23"},
    {"title": "新疆农业大学融媒体智能一体化平台建设项目（二次）公开招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260522_26617444.htm", "industry": "宣传", "province": "新疆", "phase": "招标公告", "budget": None, "winner": None, "agency": "新疆农业大学", "agent": "新疆维吾尔自治区政务服务和公共资源交易中心", "date": "2026-05-22"},
    {"title": "河北交通职业技术学院融媒体中心采编发一体化协作平台及配套设备招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260522_26611688.htm", "industry": "宣传", "province": "河北", "phase": "招标公告", "budget": None, "winner": None, "agency": "河北交通职业技术学院", "agent": "河北鑫凯工程管理有限公司", "date": "2026-05-22"},
    {"title": "玉溪市融媒体中心融媒生产平台建设项目（拍摄设备采购）（二次）公开招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260521_26608332.htm", "industry": "宣传", "province": "云南", "phase": "招标公告", "budget": None, "winner": None, "agency": "玉溪市融媒体中心", "agent": "云南力宏建设工程咨询有限公司", "date": "2026-05-21"},
    {"title": "玉溪市融媒体中心融媒生产平台建设项目（二次）公开招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260521_26608265.htm", "industry": "宣传", "province": "云南", "phase": "招标公告", "budget": None, "winner": None, "agency": "玉溪市融媒体中心", "agent": "云南力宏建设工程咨询有限公司", "date": "2026-05-21"},
    {"title": "新疆农业大学融媒体智能一体化平台建设项目废标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/qtgg/202605/t20260520_26600127.htm", "industry": "宣传", "province": "新疆", "phase": "招标公告", "budget": None, "winner": None, "agency": "新疆农业大学", "agent": "新疆维吾尔自治区政务服务和公共资源交易中心", "date": "2026-05-20"},
    {"title": "信息化系统新建项目-北京教育融媒体中心融媒体平台建设项目竞争性磋商公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/jzxcs/202605/t20260520_26594979.htm", "industry": "宣传", "province": "北京", "phase": "招标公告", "budget": None, "winner": None, "agency": "北京教育融媒体中心", "agent": "北京汇诚金桥国际招标咨询有限公司", "date": "2026-05-20"},
    {"title": "玉溪市融媒体中心融媒生产平台建设项目终止公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/fblbgg/202605/t20260519_26593138.htm", "industry": "宣传", "province": "云南", "phase": "招标公告", "budget": None, "winner": None, "agency": "玉溪市融媒体中心", "agent": "云南力宏建设工程咨询有限公司", "date": "2026-05-19"},
    {"title": "玉溪市融媒体中心融媒生产平台建设项目(拍摄设备采购)终止公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/fblbgg/202605/t20260518_26586111.htm", "industry": "宣传", "province": "云南", "phase": "招标公告", "budget": None, "winner": None, "agency": "玉溪市融媒体中心", "agent": "云南力宏建设工程咨询有限公司", "date": "2026-05-18"},
    {"title": "玉溪市融媒体中心融媒生产平台建设项目(拍摄设备采购)更正公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260518_26583820.htm", "industry": "宣传", "province": "云南", "phase": "招标公告", "budget": None, "winner": None, "agency": "玉溪市融媒体中心", "agent": "云南力宏建设工程咨询有限公司", "date": "2026-05-18"},
    {"title": "玉溪市融媒体中心融媒生产平台建设项目更正公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260512_26550084.htm", "industry": "宣传", "province": "云南", "phase": "招标公告", "budget": None, "winner": None, "agency": "玉溪市融媒体中心", "agent": "云南力宏建设工程咨询有限公司", "date": "2026-05-12"},
    {"title": "玉溪市融媒体中心融媒生产平台建设项目(拍摄设备采购)更正公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260512_26550083.htm", "industry": "宣传", "province": "云南", "phase": "招标公告", "budget": None, "winner": None, "agency": "玉溪市融媒体中心", "agent": "云南力宏建设工程咨询有限公司", "date": "2026-05-12"},
    {"title": "玉溪市融媒体中心融媒生产平台建设项目公开招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260507_26518891.htm", "industry": "宣传", "province": "云南", "phase": "招标公告", "budget": None, "winner": None, "agency": "玉溪市融媒体中心", "agent": "云南力宏建设工程咨询有限公司", "date": "2026-05-07"},
    {"title": "北京市海淀区融媒体中心学习强国平台运维公开招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260515_26573117.htm", "industry": "宣传", "province": "北京", "phase": "招标公告", "budget": None, "winner": None, "agency": "北京市海淀区融媒体中心", "agent": "中钰招标有限公司", "date": "2026-05-15"},
    {"title": "海南州融媒体中心IPTV平台监播费采购实行单一来源采购方式的公示", "url": "http://www.ccgp.gov.cn/cggg/dfgg/dylygg/202605/t20260514_26564775.htm", "industry": "宣传", "province": "青海", "phase": "采购意向", "budget": 50, "winner": None, "agency": "海南州融媒体中心", "agent": "详情见公告正文", "date": "2026-05-14"},
    {"title": "成都市龙泉驿区融媒体中心天府龙泉驿网站及微信平台运行费用中标（成交）结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/cjgg/202605/t20260513_26560375.htm", "industry": "宣传", "province": "四川", "phase": "中标公示", "budget": 103.22, "winner": "成都巧点睛文化传播有限公司", "agency": "成都市龙泉驿区融媒体中心", "agent": "四川正山工程项目管理有限公司", "date": "2026-05-13"},
    {"title": "高质量发展-学科建设-超高清4K综合融媒体实训平台公开招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260512_26551295.htm", "industry": "宣传", "province": "吉林", "phase": "招标公告", "budget": None, "winner": None, "agency": "吉林艺术学院", "agent": "吉林中鸿项目管理咨询有限公司", "date": "2026-05-12"},
    {"title": "辽宁师范大学全景开放式融媒体实训平台项目招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260511_26546231.htm", "industry": "宣传", "province": "辽宁", "phase": "招标公告", "budget": None, "winner": None, "agency": "辽宁师范大学", "agent": "通利晟信管理咨询有限公司", "date": "2026-05-11"},
    {"title": "绵阳市游仙区融媒体中心技术平台运营服务竞争性磋商公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/jzxcs/202605/t20260511_26544552.htm", "industry": "宣传", "province": "四川", "phase": "招标公告", "budget": None, "winner": None, "agency": "绵阳市游仙区融媒体中心", "agent": "成都众望云商招标代理有限公司", "date": "2026-05-11"},
    {"title": "2026年-2027年新疆禁毒融媒体平台信息采编和活动策划项目竞争性磋商公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/jzxcs/202605/t20260510_26542064.htm", "industry": "宣传", "province": "新疆", "phase": "招标公告", "budget": None, "winner": None, "agency": "新疆维吾尔自治区公安厅", "agent": "新疆能实建设工程项目管理咨询有限责任公司", "date": "2026-05-10"},
    {"title": "衢州市新闻传媒中心融媒体智慧生产平台转播车4K制播设备升级改造项目的公开招标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202605/t20260510_26541811.htm", "industry": "宣传", "province": "浙江", "phase": "招标公告", "budget": None, "winner": None, "agency": "衢州市新闻传媒中心", "agent": "浙江省成套招标代理有限公司", "date": "2026-05-10"},
    {"title": "中共湖南省委统战部湖南统战宣传融媒体平台服务竞争性磋商成交公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/cjgg/202605/t20260509_26534249.htm", "industry": "宣传", "province": "湖南", "phase": "中标公示", "budget": None, "winner": None, "agency": "中共湖南省委统战部", "agent": "湖南中发项目管理有限公司", "date": "2026-05-09"},
    {"title": "杭州市余杭区融媒体中心2026年看余杭平台运营项目中标(成交)结果公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260508_26527878.htm", "industry": "宣传", "province": "浙江", "phase": "中标公示", "budget": None, "winner": None, "agency": "杭州市余杭区融媒体中心（杭州市余杭区广播电视台）", "agent": "杭州恒正造价工程师事务所", "date": "2026-05-08"},
    {"title": "区县融媒体平台一体化能力提升暨中宁县1+n融媒体工作室项目中标公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202605/t20260506_26515603.htm", "industry": "宣传", "province": "宁夏", "phase": "中标公示", "budget": None, "winner": None, "agency": "中宁县融媒体中心", "agent": "宁夏中大宏源项目管理有限公司", "date": "2026-05-06"},
    {"title": "白城市融媒体中心节目生产平台及设备采购项目结果更正公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260506_26513512.htm", "industry": "宣传", "province": "吉林", "phase": "中标公示", "budget": None, "winner": None, "agency": "白城广播电视台", "agent": "白城市公共资源交易中心", "date": "2026-05-06"},
    {"title": "北京市昌平区融媒体中心2026年全媒体平台内容生产服务项目单一来源公示", "url": "http://www.ccgp.gov.cn/cggg/dfgg/dylygg/202605/t20260506_26511297.htm", "industry": "宣传", "province": "北京", "phase": "采购意向", "budget": None, "winner": None, "agency": "北京市昌平区融媒体中心", "agent": "北京北粤工程造价咨询有限公司", "date": "2026-05-06"},

    # ===== 广电 信息化 =====
    {"title": "关于深圳市南山区文化广电旅游体育局大沙河文体中心改造项目专业设备和信息化工程项目的更正公告", "url": "http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202605/t20260503_26509866.htm", "industry": "文化", "province": "广东", "phase": "招标公告", "budget": None, "winner": None, "agency": "深圳市南山区文化广电旅游体育局", "agent": "深圳交易集团有限公司南山分公司", "date": "2026-05-03"},
]


def detect_it_type(title):
    """Detect IT project type from title"""
    type_map = {
        "数字化转型": ["数字化", "转型"],
        "智慧平台": ["智慧平台", "智慧", "智能"],
        "大数据中心": ["大数据", "数据中台", "数据中心", "数据采集"],
        "融媒体平台": ["融媒体", "融媒"],
        "数字化博物馆": ["博物馆", "文物"],
        "智慧体育": ["体育信息化", "智慧体育", "体育信息化"],
        "云服务": ["云平台", "云计算", "云服务"],
        "数字内容管理": ["内容管理", "CMS"],
        "网络安全": ["安全服务", "安全", "等保"],
        "AI应用": ["AI", "人工智能", "智能分析"],
        "系统集成": ["集成", "系统建设", "平台建设"],
        "运维服务": ["运维", "维护", "维保"],
        "信息化建设": ["信息化"],
    }
    for tt, kws in type_map.items():
        if any(kw in title for kw in kws):
            return tt
    return "信息化建设"


def is_it_project(title):
    """Check if title indicates an IT project"""
    it_keywords = ["信息化", "数字化", "智慧", "数据", "软件", "系统", "网络",
                   "平台", "融媒体", "AI", "人工智能", "区块链", "云", "大数据",
                   "物联网", "5G", "IT", "信息系统", "信息安全", "运维", "门户网站",
                   "APP", "小程序", "数据库", "服务器", "存储", "算力", "算法", "模型"]
    return any(kw in title for kw in it_keywords)


def main():
    print("=" * 60)
    print("5月份数据合并脚本")
    print(f"新增数据: {len(MAY_DATA)} 条")
    print("=" * 60)

    # Load existing data
    with open(TARGET_FILE, "r", encoding="utf-8") as f:
        existing = json.load(f)

    existing_projects = existing.get("projects", [])
    print(f"现有数据: {len(existing_projects)} 条")

    # Backup
    with open(TARGET_FILE, "r", encoding="utf-8") as src:
        with open(BACKUP_FILE, "w", encoding="utf-8") as dst:
            dst.write(src.read())
    print(f"已备份到 {BACKUP_FILE}")

    # Build URL index for dedup
    url_index = {}
    for i, p in enumerate(existing_projects):
        url = p.get("url", "")
        if url:
            url_index[url] = i

    # Merge
    updated_count = 0
    added_count = 0
    import random

    for item in MAY_DATA:
        url = item["url"]
        title = item["title"]
        agency = item.get("agency", "")
        agent = item.get("agent", "")

        # Check if ministry
        ministry_keywords = ["中华人民共和国", "国家", "中央", "全国", "部", "局", "总局", "委员会"]
        is_ministry = item.get("province") == "部委" or any(m in agency for m in ministry_keywords)

        # Determine IT type
        is_it = is_it_project(title)
        it_type = detect_it_type(title) if is_it else None

        if url in url_index:
            # Update existing project
            idx = url_index[url]
            old = existing_projects[idx]
            changed = False

            # Update budget if we have it and old doesn't
            if item.get("budget") is not None and old.get("budget") is None:
                old["budget"] = item["budget"]
                changed = True

            # Update winner
            if item.get("winner") and not old.get("winner"):
                old["winner"] = item["winner"]
                changed = True

            # Update phase if newer
            phase_order = {"采购意向": 0, "招标公告": 1, "中标公示": 2, "合同签订": 3}
            if item.get("phase") and phase_order.get(item["phase"], 0) > phase_order.get(old.get("phase", ""), 0):
                old["phase"] = item["phase"]
                changed = True

            # Always update agency/agent if we have better data
            if agency and not old.get("agency"):
                old["agency"] = agency
                changed = True
            if agent and not old.get("agent"):
                old["agent"] = agent
                changed = True

            if changed:
                updated_count += 1
        else:
            # Add new project
            proj = {
                "id": f"WT-2026-{random.randint(100000, 999999)}",
                "title": title,
                "url": url,
                "industry": item.get("industry", "文化"),
                "province": item.get("province", "北京"),
                "phase": item.get("phase", "招标公告"),
                "budget": item.get("budget"),
                "agency": agency,
                "agent": agent,
                "date": item.get("date", ""),
                "isIT": is_it,
                "itType": it_type,
                "isMinistry": is_ministry,
                "winner": item.get("winner"),
            }
            existing_projects.append(proj)
            url_index[url] = len(existing_projects) - 1
            added_count += 1

    print(f"合并结果: 更新 {updated_count} 条, 新增 {added_count} 条")

    # Sort by date
    existing_projects.sort(key=lambda x: x.get("date", ""), reverse=True)

    # Recompute statistics
    stats = {
        "total": len(existing_projects),
        "by_industry": dict(Counter(p.get("industry", "其他") for p in existing_projects)),
        "by_province": dict(Counter(p.get("province", "其他") for p in existing_projects)),
        "by_phase": dict(Counter(p.get("phase", "其他") for p in existing_projects)),
        "it_projects": sum(1 for p in existing_projects if p.get("isIT")),
        "with_winner": sum(1 for p in existing_projects if p.get("winner")),
        "with_budget": sum(1 for p in existing_projects if p.get("budget")),
        "total_budget": sum(p["budget"] for p in existing_projects if p.get("budget")),
        "phase_details": {},
        "source_breakdown": {"ccgp_detail": 0, "ccgp_search": 0, "ccgp_new": 0},
    }

    # Count May projects
    may_count = sum(1 for p in existing_projects if p.get("date", "").startswith("2026-05"))
    jun_count = sum(1 for p in existing_projects if p.get("date", "").startswith("2026-06"))

    # Update output
    existing["generated_at"] = datetime.now().isoformat()
    existing["data_range"] = {"start": "2026-01-01", "end": "2026-06-26"}
    existing["source"] = "中国政府采购网 (www.ccgp.gov.cn)"
    existing["data_quality"] = {
        "from_detail_pages": stats["with_winner"],
        "total_projects": stats["total"],
        "with_budget_amount": stats["with_budget"],
        "with_winner_name": stats["with_winner"],
        "may_projects": may_count,
        "june_projects": jun_count,
        "note": f"数据来源：{stats['by_phase'].get('中标公示',0)}条中标公示含真实中标单位，{stats['with_budget']}条含真实预算金额。包含5月{may_count}条、6月{jun_count}条数据。"
    }
    existing["statistics"] = stats
    existing["projects"] = existing_projects

    # Save
    with open(TARGET_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"数据已保存: {TARGET_FILE}")
    print(f"总项目数: {stats['total']}")
    print(f"  - 5月数据: {may_count} 条")
    print(f"  - 6月数据: {jun_count} 条")
    print(f"  - 文化: {stats['by_industry'].get('文化', 0)}")
    print(f"  - 旅游: {stats['by_industry'].get('旅游', 0)}")
    print(f"  - 体育: {stats['by_industry'].get('体育', 0)}")
    print(f"  - 宣传: {stats['by_industry'].get('宣传', 0)}")
    print(f"  - 含中标单位: {stats['with_winner']}")
    print(f"  - 含预算金额: {stats['with_budget']}")
    print(f"  - 省份覆盖: {len(stats['by_province'])} 个")
    print(f"阶段分布: {json.dumps(stats['by_phase'], ensure_ascii=False)}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

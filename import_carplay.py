"""将 CarPlay 测试用例 Excel 导入数据库（优化版）"""

import asyncio
import re

import pandas as pd

from app.database import async_session, engine, Base
from app.models.test_case import TestCase, PriorityEnum, CaseStatusEnum


def parse_numbered_lines(text: str) -> list[str]:
    """按 '1.xxx 2.xxx' 格式拆分步骤"""
    if not text:
        return []
    # 按数字序号拆分
    parts = re.split(r'(?:^|\s)(\d+)\.', text.strip())
    result = []
    i = 1
    while i < len(parts):
        num = parts[i]
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        result.append(content)
        i += 2
    return result if result else [text.strip()]


async def import_carplay():
    # 清空旧数据重建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    df = pd.read_excel(r"D:\王鸿渺\用例管理\有线无线CarPlay测试用例.xlsx")

    cases = []
    current_section = ""
    func_cache = {}  # 缓存功能点中文名

    for i in range(df.shape[0]):
        row = df.iloc[i]
        case_no_raw = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""

        # 检测分段标题
        if "有线" in case_no_raw and "CarPlay" in case_no_raw:
            current_section = "有线CarPlay"
            continue
        if "无线" in case_no_raw and "CarPlay" in case_no_raw:
            current_section = "无线CarPlay"
            continue

        if not case_no_raw or case_no_raw == "nan":
            continue

        # 读取各字段
        test_type_cn = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else "实车测试"
        function_cn = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else func_cache.get(case_no_raw, "")
        func_point_en = str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else ""
        precondition_cn = str(row.iloc[6]).strip() if pd.notna(row.iloc[6]) else ""
        precondition_en = str(row.iloc[7]).strip() if pd.notna(row.iloc[7]) else ""
        activities_cn = str(row.iloc[8]).strip() if pd.notna(row.iloc[8]) else ""
        activities_en = str(row.iloc[9]).strip() if pd.notna(row.iloc[9]) else ""
        expected_cn = str(row.iloc[10]).strip() if pd.notna(row.iloc[10]) else ""
        expected_en = str(row.iloc[11]).strip() if pd.notna(row.iloc[11]) else ""

        # 功能点映射
        func_map = {
            "Connection": "连接",
            "Music": "音乐",
            "Navigation": "导航",
            "Phone": "电话",
        }
        func_cn = func_map.get(func_point_en, function_cn)
        if func_cn:
            func_cache[case_no_raw] = func_cn

        # 模块名
        module = f"{current_section} - {func_cn}"

        # 解析步骤（中文为主，英文补充）
        cn_steps = parse_numbered_lines(activities_cn)
        en_steps = parse_numbered_lines(activities_en)
        cn_expects = parse_numbered_lines(expected_cn)
        en_expects = parse_numbered_lines(expected_en)

        steps = []
        max_len = max(len(cn_steps), len(en_steps), len(cn_expects), len(en_expects))
        for j in range(max_len):
            action = cn_steps[j] if j < len(cn_steps) else (en_steps[j] if j < len(en_steps) else "")
            expected = cn_expects[j] if j < len(cn_expects) else (en_expects[j] if j < len(en_expects) else "")
            steps.append({
                "seq": j + 1,
                "action": action,
                "expected": expected,
            })

        # 标题
        title = f"[{case_no_raw}] {func_cn} — {cn_steps[0] if cn_steps else activities_cn[:60]}"

        # 优先级
        priority = {
            "Connection": PriorityEnum.P0,
            "Music": PriorityEnum.P1,
            "Navigation": PriorityEnum.P1,
            "Phone": PriorityEnum.P1,
        }.get(func_point_en, PriorityEnum.P2)

        # 标签
        tags = [current_section, func_point_en, test_type_cn]
        if "P0" in priority.value:
            tags.append("smoke")

        # 前置条件
        precondition = precondition_cn
        if precondition_en and precondition_en != precondition_cn:
            precondition = f"{precondition_cn}\n{precondition_en}"

        cases.append({
            "title": title,
            "module": module,
            "priority": priority,
            "status": CaseStatusEnum.ACTIVE,
            "precondition": precondition,
            "steps": steps,
            "tags": tags,
        })

    # 写入数据库
    async with async_session() as db:
        for data in cases:
            case = TestCase(**data)
            db.add(case)
        await db.commit()

    print(f"成功导入 {len(cases)} 条 CarPlay 测试用例：")
    for c in cases:
        print(f"  [{c['priority'].value}] {c['title']}")
        print(f"      模块: {c['module']}  标签: {c['tags']}")
        for s in c["steps"]:
            act = s["action"][:60]
            exp = s["expected"][:60]
            print(f"      步骤{s['seq']}: {act} → {exp}")
        print()


if __name__ == "__main__":
    asyncio.run(import_carplay())

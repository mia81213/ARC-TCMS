"""种子数据脚本 —— 插入示例数据用于开发测试"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session, init_db
from app.models.test_case import TestCase, PriorityEnum, CaseStatusEnum
from app.models.test_plan import TestPlan, PlanStatusEnum
from app.models.test_plan_item import TestPlanItem, ExecutionStatusEnum


SAMPLE_CASES = [
    {
        "title": "用户登录 — 正确账号密码",
        "module": "登录模块",
        "priority": PriorityEnum.P0,
        "status": CaseStatusEnum.ACTIVE,
        "precondition": "已注册测试账号 test@example.com / Test1234",
        "steps": [
            {"seq": 1, "action": "打开登录页面", "expected": "显示登录表单"},
            {"seq": 2, "action": "输入邮箱 test@example.com", "expected": "邮箱输入框显示输入内容"},
            {"seq": 3, "action": "输入密码 Test1234", "expected": "密码以密文显示"},
            {"seq": 4, "action": "点击「登录」按钮", "expected": "登录成功，跳转到首页，显示用户名"},
        ],
        "tags": ["smoke", "P0"],
    },
    {
        "title": "用户登录 — 错误密码",
        "module": "登录模块",
        "priority": PriorityEnum.P1,
        "status": CaseStatusEnum.ACTIVE,
        "precondition": "已注册测试账号 test@example.com",
        "steps": [
            {"seq": 1, "action": "打开登录页面", "expected": "显示登录表单"},
            {"seq": 2, "action": "输入邮箱 test@example.com 和错误密码", "expected": ""},
            {"seq": 3, "action": "点击「登录」按钮", "expected": "提示「邮箱或密码错误」，不跳转"},
        ],
        "tags": ["regression"],
    },
    {
        "title": "用户登录 — 空表单提交",
        "module": "登录模块",
        "priority": PriorityEnum.P2,
        "status": CaseStatusEnum.ACTIVE,
        "precondition": "",
        "steps": [
            {"seq": 1, "action": "打开登录页面", "expected": "显示登录表单"},
            {"seq": 2, "action": "不输入任何内容，直接点击「登录」", "expected": "显示字段必填校验提示"},
        ],
        "tags": ["validation"],
    },
    {
        "title": "商品搜索 — 关键词搜索",
        "module": "搜索模块",
        "priority": PriorityEnum.P1,
        "status": CaseStatusEnum.ACTIVE,
        "precondition": "数据库中有至少10个商品",
        "steps": [
            {"seq": 1, "action": "在搜索框输入「手机」", "expected": "自动补全下拉框出现"},
            {"seq": 2, "action": "按回车键搜索", "expected": "跳转到搜索结果页，显示匹配商品列表"},
            {"seq": 3, "action": "检查结果数量", "expected": "结果数量 > 0，且与关键词相关"},
        ],
        "tags": ["search", "regression"],
    },
    {
        "title": "商品搜索 — 无结果搜索",
        "module": "搜索模块",
        "priority": PriorityEnum.P3,
        "status": CaseStatusEnum.ACTIVE,
        "precondition": "",
        "steps": [
            {"seq": 1, "action": "在搜索框输入不存在的商品名「zzzxxxx」", "expected": ""},
            {"seq": 2, "action": "按回车键搜索", "expected": "显示「未找到相关商品」的空状态页面"},
        ],
        "tags": ["search"],
    },
    {
        "title": "购物车 — 添加商品",
        "module": "购物车模块",
        "priority": PriorityEnum.P0,
        "status": CaseStatusEnum.ACTIVE,
        "precondition": "已登录，商品详情页可访问",
        "steps": [
            {"seq": 1, "action": "进入商品详情页", "expected": "显示商品信息、价格、库存"},
            {"seq": 2, "action": "点击「加入购物车」按钮", "expected": "提示「已加入购物车」，购物车图标数字+1"},
        ],
        "tags": ["smoke", "P0"],
    },
    {
        "title": "购物车 — 删除商品",
        "module": "购物车模块",
        "priority": PriorityEnum.P1,
        "status": CaseStatusEnum.ACTIVE,
        "precondition": "购物车中已有商品",
        "steps": [
            {"seq": 1, "action": "进入购物车页面", "expected": "显示已添加的商品列表"},
            {"seq": 2, "action": "点击某商品的「删除」按钮", "expected": "弹出确认对话框"},
            {"seq": 3, "action": "点击确认", "expected": "该商品从列表中移除，总价更新"},
        ],
        "tags": ["regression"],
    },
    {
        "title": "订单提交 — 完整流程",
        "module": "订单模块",
        "priority": PriorityEnum.P0,
        "status": CaseStatusEnum.DRAFT,
        "precondition": "已登录，购物车中有商品，已设置收货地址",
        "steps": [
            {"seq": 1, "action": "从购物车点击「去结算」", "expected": "进入确认订单页面"},
            {"seq": 2, "action": "确认收货地址、商品、数量、金额", "expected": "信息正确显示"},
            {"seq": 3, "action": "选择支付方式（微信支付）", "expected": "支付方式被选中"},
            {"seq": 4, "action": "点击「提交订单」", "expected": "弹出支付确认，支付后跳转到订单成功页"},
        ],
        "tags": ["smoke", "P0", "e2e"],
    },
]


async def seed(drop_first: bool = False):
    """插入种子数据"""
    await init_db()

    async with async_session() as db:
        if drop_first:
            # 清空数据
            from app.database import Base, engine
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            await init_db()

        # 检查是否已有数据
        result = await db.execute(select(TestCase).limit(1))
        if result.scalar_one_or_none():
            print("数据库已有数据，跳过种子数据插入")
            return

        # 插入测试用例
        cases = []
        for data in SAMPLE_CASES:
            case = TestCase(**data)
            db.add(case)
            cases.append(case)
        await db.flush()
        print(f"已插入 {len(cases)} 条测试用例")

        # 插入测试计划
        plan1 = TestPlan(
            name="v2.0 回归测试",
            description="v2.0 版本发布前的回归测试计划",
            status=PlanStatusEnum.IN_PROGRESS,
        )
        plan2 = TestPlan(
            name="核心功能冒烟测试",
            description="每次构建后的必测用例",
            status=PlanStatusEnum.DRAFT,
        )
        db.add_all([plan1, plan2])
        await db.flush()
        print(f"已插入 2 个测试计划")

        # 将用例分配到计划
        items = []
        # 计划1：添加前6个用例
        for case in cases[:6]:
            items.append(TestPlanItem(test_plan_id=plan1.id, test_case_id=case.id))
        # 计划2：添加P0用例
        for case in cases:
            if case.priority == PriorityEnum.P0:
                items.append(TestPlanItem(test_plan_id=plan2.id, test_case_id=case.id))

        # 模拟部分执行结果
        if items:
            items[0].execution_status = ExecutionStatusEnum.PASSED
            items[0].executed_by = "张三"
            items[0].actual_result = "符合预期"
            items[0].notes = "首次测试通过"
            items[1].execution_status = ExecutionStatusEnum.FAILED
            items[1].executed_by = "张三"
            items[1].actual_result = "密码错误时未显示错误提示"
            items[1].notes = "需要修复bug"

        db.add_all(items)
        await db.flush()
        print(f"已插入 {len(items)} 条计划-用例关联")

        await db.commit()
        print("种子数据插入完成！")


if __name__ == "__main__":
    asyncio.run(seed(drop_first=True))

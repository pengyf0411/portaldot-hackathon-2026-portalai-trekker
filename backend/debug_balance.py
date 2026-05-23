"""
debug_balance.py — 诊断余额查询问题

直接连接本地节点，打印 Alice 账户的原始数据，帮助定位余额显示为 0 的原因。
运行方式: python debug_balance.py
"""

import os
from dotenv import load_dotenv
from substrateinterface import SubstrateInterface

load_dotenv()

# Alice 在 Substrate dev 模式下的固定地址（ss58_format=42）
ALICE = "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY"

WS_URL = os.getenv("PORTALDOT_WS_URL", "ws://127.0.0.1:9944")

PORTALDOT_TYPES = {
    "AccountInfo": {
        "type": "struct",
        "type_mapping": [
            ["nonce", "u32"],
            ["consumers", "u32"],
            ["providers", "u32"],
            ["sufficients", "u32"],
            ["data", "AccountData"],
        ],
    },
    "AccountData": {
        "type": "struct",
        "type_mapping": [
            ["free", "u128"],
            ["reserved", "u128"],
            ["miscFrozen", "u128"],
            ["feeFrozen", "u128"],
        ],
    },
    "Weight": "u64",
    "LookupSource": "AccountId",
    "Address": "AccountId",
}

print(f"连接节点: {WS_URL}")
print(f"查询地址: {ALICE}")
print("-" * 60)

# ── 测试1: 使用自定义类型（当前代码逻辑）──────────────────────
print("\n[测试1] 使用自定义 PORTALDOT_TYPES:")
try:
    sub1 = SubstrateInterface(
        url=WS_URL,
        ss58_format=42,
        type_registry={"types": PORTALDOT_TYPES},
    )
    result1 = sub1.query("System", "Account", [ALICE])
    print(f"  result.value = {result1.value}")
    data1 = result1.value.get("data", {})
    free1 = data1.get("free", "KEY_NOT_FOUND")
    print(f"  data['free'] = {free1}")
    if isinstance(free1, int):
        for dec in [10, 12, 14, 15, 18]:
            print(f"    / 10^{dec} = {free1 / 10**dec:.6f}")
    sub1.close()
except Exception as e:
    print(f"  ❌ 错误: {e}")

# ── 测试2: 不使用自定义类型（让库自动解码）──────────────────────
print("\n[测试2] 不使用自定义类型（自动解码）:")
try:
    sub2 = SubstrateInterface(url=WS_URL, ss58_format=42)
    result2 = sub2.query("System", "Account", [ALICE])
    print(f"  result.value = {result2.value}")
    data2 = result2.value.get("data", {})
    free2 = data2.get("free", "KEY_NOT_FOUND")
    print(f"  data['free'] = {free2}")
    if isinstance(free2, int):
        for dec in [10, 12, 14, 15, 18]:
            print(f"    / 10^{dec} = {free2 / 10**dec:.6f}")
    sub2.close()
except Exception as e:
    print(f"  ❌ 错误: {e}")

# ── 测试3: 查询链上 token 元数据（decimal 精度）──────────────────
print("\n[测试3] 查询链上 Token 精度:")
try:
    sub3 = SubstrateInterface(url=WS_URL, ss58_format=42)
    props = sub3.rpc_request("system_properties", [])
    print(f"  system_properties = {props.get('result', {})}")
    sub3.close()
except Exception as e:
    print(f"  ❌ 错误: {e}")

print("\n" + "-" * 60)
print("诊断完成。请将上面输出内容提供给助手。")

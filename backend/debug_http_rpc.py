"""测试 Substrate 节点是否支持 HTTP JSON-RPC 批量请求"""
import requests, json, time

RPC_URL = "http://127.0.0.1:9933"

# 测试1: 单个请求
t0 = time.time()
r = requests.post(RPC_URL, json={"id": 1, "jsonrpc": "2.0", "method": "chain_getHeader", "params": []}, timeout=5)
print(f"HTTP 单次请求: {(time.time()-t0)*1000:.0f}ms, status={r.status_code}")
if r.status_code == 200:
    print(f"  result: {r.json()}")
    
    # 测试2: 批量请求 (一次发 10 个 chain_getBlockHash)
    batch = [{"id": i, "jsonrpc": "2.0", "method": "chain_getBlockHash", "params": [i]} for i in range(1, 11)]
    t1 = time.time()
    rb = requests.post(RPC_URL, json=batch, timeout=10)
    print(f"\nHTTP 批量请求(10个): {(time.time()-t1)*1000:.0f}ms, status={rb.status_code}")
    if rb.status_code == 200:
        results = rb.json()
        print(f"  responses: {len(results)}")
        print(f"  first hash: {results[0]['result']}")
else:
    print("HTTP RPC 不可用，节点可能只开了 WS")

# NoneType 错误修复：重试耗尽返回 None

## 问题描述

Web UI 执行任务时出现含义不明的错误：

```
任务执行失败: 'NoneType' object has no attribute 'status_code'
```

该报错**不是**真正的原因，它只是掩盖了真实的网络错误。

## 根本原因

`ani2openlist/utils/retry.py` 的重试装饰器在**重试次数耗尽后返回 `None`**：

```python
# 修改前
else:
    logger.error(cls.ERROR_MSG.format(e))
    return None          # ← 吞掉了真实异常
```

而 `ani2openlist/utils/http.py` 的所有调用方都假设拿到的是 `httpx.Response`：

```python
resp = await RequestUtils.get(f"https://{rss_domain}/ani-download.xml")
if resp.status_code != 200:       # ← resp 为 None 时崩溃
```

于是**任何**网络故障（超时、DNS 失败、连接被拒、代理故障）都会被转换成
同一句 `'NoneType' object has no attribute 'status_code'`。

### 触发链路

1. `RequestUtils.get/post` → `HTTPClient._async_request`
2. 装饰器捕获异常并重试 3 次，全部失败后 `return None`
3. 调用方访问 `resp.status_code` → `AttributeError`

### 影响范围

所有经由 `RequestUtils` / `OpenlistClient` 的请求都会受影响：

| 位置 | 说明 |
|------|------|
| `ani2openlist.py:187` | 季度模式遍历目录 |
| `ani2openlist.py:292` | RSS 订阅拉取 |
| `openlist/client.py` | 令牌刷新、用户信息、文件列表、存储器增改 |

另外，原来的装饰器只捕获 `TimeoutException`，而 `ConnectError`、`ProxyError`
等 `TransportError` 子类**根本不会被重试**，会直接抛出。

## 修复方案

### 1. ✅ 重试耗尽后向上抛出异常

```python
# 修改后
else:
    logger.error(cls.ERROR_MSG.format(e))
    # 重试耗尽后向上抛出异常，避免返回 None 导致调用方
    # 出现 "'NoneType' object has no attribute ..." 之类的二次错误
    raise
```

同步版本 `sync_retry` 与异步版本 `async_retry` 均已修正。

### 2. ✅ 扩大重试的异常范围

由 `TimeoutException` 改为 `TransportError`（`TimeoutException`、
`ConnectError`、`ProxyError` 等的共同父类）：

```python
@Retry.async_retry(TransportError, tries=3, delay=1, backoff=2)
async def _async_request(self, method: str, url: str, **kwargs) -> Response:
```

### 3. ✅ 修正类型标注

移除所有 `Response | None` 标注，改为 `Response`，让类型检查器能够
发现这类问题（原标注把"可能返回 None"当成正常契约，掩盖了缺陷）。

### 4. ✅ 校验 `tries` 参数

```python
if tries < 1:
    raise ValueError(f"最大重试次数必须大于等于 1，当前为：{tries}")
```

避免 `tries=0` 时 `while` 循环体不执行、函数隐式返回 `None`，重新引入同类问题。

## 已修改的文件

```
✅ ani2openlist/utils/retry.py   - 重试耗尽后 raise；校验 tries；修正类型标注
✅ ani2openlist/utils/http.py    - 捕获 TransportError；修正返回类型标注
✅ tests/test_http_retry.py      - 新增 10 个回归测试
✅ .gitignore                    - 锚定 test_* 规则，避免 tests/ 下新测试被忽略
```

## 修复效果

**修复前**：任何网络故障都报同一条无意义的 `NoneType` 错误。

**修复后**：抛出真实异常，可直接定位问题：

```
>>> 修复生效：抛出真实异常 -> TimeoutException HTTP 请求超时：timed out
```

## 测试验证

```bash
python -m pytest tests/ -v
# 13 passed
```

覆盖的回归场景：

- 重试耗尽后抛出异常（同步 / 异步）
- 中途成功后正常返回结果，不会误抛
- `tries < 1` 时抛出 `ValueError`
- 真实网络错误抛出 `ConnectError` / `TimeoutException`，而非 `AttributeError`
- 成功路径仍返回可用 `Response`，`status_code` 可正常访问

## 相关链接

- [httpx 异常层级](https://www.python-httpx.org/exceptions/)

---

**修复完成时间**: 2026年9月27日
**修复版本**: v1.1.2
**影响范围**: 所有 HTTP 请求的错误处理路径
**状态**: ✅ 已修复并测试

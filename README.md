# Alconna Notation

以 [`HOCON`](https://github.com/chimpler/pyhocon) 为基础的序列化/反序列化工具，用于转换 `Alconna`。

## 示例

```python
import arclet.alconna.notation as alcon

# 从字符串解析
alc = alcon.loads(
"""\
command = test
args {
    foo = str
    bar = int
}
options = [
    {
        name = --spam
        aliases = [-s]
        default = true
        action = store_false
    }
    {
        name = --eggs
        aliases = [-e]
        args {
            count = int
        }
        default = 0
    }
]
"""

assert alc.parse("test abc 123 -s").query("foo") == "abc"
```

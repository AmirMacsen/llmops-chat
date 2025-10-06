### injector 依赖注入

```shell
pip install injector
```

```python
import injector


class A:
    pass

# 注入B交给全局管理
# 自动实例化
@injector.inject
class B:
    def __init__(self, a: A):
        self.a = a
        self.b = 1

injector = injector.Injector()
b_injector = injector.get(B)
print(b_injector)
print(b_injector.b)
```
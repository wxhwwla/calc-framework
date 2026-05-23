# 插件目录（可选）

将扩展配置放在本目录下，应用启动时会自动加载。

## 敌人参数示例

创建 `enemies/my_boss.json`：

```json
{
  "id": "my_boss",
  "名称": "自定义首领",
  "enemy_defense": 500.0,
  "enemy_resistance": 0.2
}
```

也支持 `enemies/*.yaml`（需安装 `pyyaml`）。

加载逻辑见 `data/plugin_registry.py`；后续版本将把插件敌人接入 GUI 敌方参数面板。

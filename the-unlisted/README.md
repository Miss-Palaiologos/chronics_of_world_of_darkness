# 不在册者

一部基于 Vampire: The Masquerade V5 世界观的现代之夜编年史，包含剧本数据、局势推演引擎、Markdown 生成器和本地 GUI。

## 开始使用

```powershell
$env:PYTHONPATH='src'
$py='..\.venv\Scripts\python.exe'

& $py -m the_unlisted.cli check
& $py -m the_unlisted.cli render
& $py -m the_unlisted.cli verify
& $py -m the_unlisted.cli run --profile normal --seed 5
& $py -m the_unlisted.cli gui
```

直接运行脚本也支持：`python src\the_unlisted\cli.py gui`。

完整使用说明见 [`docs/index.md`](docs/index.md)；当前派系、规则和六幕结构见 [`docs/system.md`](docs/system.md)。

运行 `render` 后会生成 [`docs/dashboard.html`](docs/dashboard.html)，可直接作为静态局势看板打开。

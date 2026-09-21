# 李寄斩蛇 · 原始资料审阅实例

本仓库是公开故事实例，不包含审阅台系统代码。系统代码及后续系统迭代在 [story-review-desk](https://github.com/goosmanlei/story-review-desk)；精确版本固定于 [config/instance.json](config/instance.json) 的 `review_desk_commit`。本仓库当前只处理资料审阅；漫剧改编不在 V1 范围。

## 资料与出处

实例目前有三份可独立审阅的文本，全部正文和元数据在 [export/materials.json](export/materials.json)：

1. 《搜神记》卷十九通行整理本原文：完整收录李寄一则，[维基文库来源](https://zh.wikisource.org/zh-hans/%E6%90%9C%E7%A5%9E%E8%A8%98/%E7%AC%AC19%E5%8D%B7)。
2. 《钦定四库全书》本《搜神记》卷十九：保留转录原字及异文，[维基文库来源](https://zh.wikisource.org/wiki/%E6%90%9C%E7%A5%9E%E8%A8%98_%28%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC%29/%E5%8D%B719)。它和通行本的“东域／东越”“斫／研”“拜其父／指其父”等差异可对照；不把繁简转换或同文转载计作另一份资料。
3. 本项目独立写作的完整白话直译与词语说明：译注是现代整理材料，不是第三个古籍底本，也不是漫剧改编。

[版本对照图](export/assets/edition-comparison.svg)由本项目据前两页原文制作并附来源，非古籍书影。图不计入三份资料。采集日期、版本类型、原文与整理说明在每份资料中明确标注。现存《搜神记》文本为后世辑本，版本字句仍可讨论。

## 从公开仓库启动

需要 Python 3.9+。克隆两个仓库，把审阅台切到本实例锁定提交：

```bash
git clone https://github.com/goosmanlei/story-review-desk.git
git clone https://github.com/goosmanlei/SnakeSlayingRecord.git
cd story-review-desk
git checkout 55dec71a2f17e4960bbe4cc6600755fdd9b55950
PYTHONPATH=. python3 -m review_desk --instance ../SnakeSlayingRecord restore
PYTHONPATH=. python3 -m review_desk --instance ../SnakeSlayingRecord serve --port 8765
```

打开 `http://127.0.0.1:8765/`。已有 `.runtime/review.sqlite3` 时跳过 `restore`，直接启动；服务器只监听本机。`OPENAI_API_KEY` 仅在本机环境中设置，用于可选 AI 润色；未配置时其他审阅功能不受影响。润色只传送圈选内容和当前草稿，建议先预览、手动采用后才会改变草稿。

## Codex 读取与公开同步

本机源数据以 `.runtime/review.sqlite3` 为运行权威；公开仓库的 `export/` 是可恢复的快照。Codex 可从系统仓库运行以下命令读取评论及其原文关联：

```bash
PYTHONPATH=. python3 -m review_desk --instance ../SnakeSlayingRecord comments
```

添加资料时准备 JSON 数组并运行 `import-sources /path/to/sources.json`；字段与 API 契约见[系统说明](https://github.com/goosmanlei/story-review-desk#数据访问与公开同步)。每次评论或资料变化后，从系统仓库执行 `PYTHONPATH=. python3 -m review_desk --instance ../SnakeSlayingRecord export`，再进入故事仓库执行：

```bash
git add config/instance.json export/materials.json export/comments.json export/manifest.json export/assets
git commit -m "Sync story review data"
git push origin main
```

公开推送前须审阅评论内容；推送意味着评论也会公开。素材、资料、评论和审计事件均在快照中，运行凭据与 SQLite 本机库不入仓。以后创作稿进入实例时，必须扩展同一导出、清单校验、公开同步与恢复协议，不能仅留在本地运行库。

验收记录见 [VERIFICATION.md](VERIFICATION.md)。

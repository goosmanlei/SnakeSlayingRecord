# 旧原件说明与后续母版认可的时态歧义

当前观察不能判为虚假认可。准确阿蘅原件`e522f05e989232e8323608cc74addd94b5e542c15c2d69692109c5fdd3e78ecb`和WAV`a7d678681c2e490de0a7dc8aca163131f68e196ceda703dc9c9282418c589272`后来确有用户母版认可；界面同时显示生成时“不是已认可母版”的原始描述，未说明两者发生顺序，造成阅读歧义。

- 原ASSET创建于`2026-10-02T17:21:57+00:00`，其不可变description和verification明确为Codex当时文件/字幕核对、未听辨、待用户认可。
- `production/full-generation/master-approvals.json`记录用户在`2026-10-03T02:48:09.393616+00:00`回复“1.认可／2.不补”，包含同对象、准确revision和原件SHA。认可范围是本身份基准母版及对应派生/同声线复用，明确不代表镜头采用。`KNOWLEDGE.md:49`也指向该来源。
- `production/song-stage/inputs/aheng-accepted-voice.json`同时保留旧ASSET与后来JUDGMENT：`review-master-fg3-aheng-voice-01`，revision`144216df3855deb325e7663a78a5a43dbce23e1d43a0498193b726236f1a5305`，创建于`2026-10-03T02:50:16+00:00`，actor=user、verdict=accepted，target及SHA与母版原件完全相同。原始生成说明没有被后续认可篡改，历史保留本身正确。
- 实际`R2-D2-wet-voice-reference.png`的原件弹窗仍只展示旧description，而后面的复用方案说已认可；读者不易分辨历史时态。这一显示歧义登记为P2供根判断，不改故事、原件、历史或认可。

本批仅核对保存的来源文件，没有查询当前DB，因此不额外声称当前库没有后续撤销。若作最小UI处理，应复用准确审阅结论并区分“生成时原始说明”和后续判断；不能改写旧ASSET、把旧verification当当前结论或补造认可。完整证据见[JSON](historical-acceptance-copy-finding.json)。

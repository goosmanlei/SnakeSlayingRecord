# SKILL管理与数据模型：发布前调查

本次授权为定义和发布任务，不执行系统改造、不恢复持续Review。最新用户要求覆盖0010旧三Tab/编辑入口定位。2026-10-12核对0010账本completed，0009 running，0011 published且仅依赖0009；无在途任务承担本次目标。45个历史草稿均已发布，无未发布重叠草稿。

## 准确当前现场

主仓 `dc8c5403e52c2fe784d556dd5d462f34c835d773`，审阅台及配置引用 `09b6935eb4e012c934cb24539a04a17ca00ff353`；双仓工作目录干净。该身份是调查基线，执行从届时最新主干开始。

根会话使用已连接Chrome亲自打开3000正式服务：观看系统构想图，进入系统管理/工作方法，点击视频方案、打开references/current-production.md，随后进入编号前缀。全部只读。

- 工作方法仍呈现方法、共用资料、工作环节3Tab、业务分类、使用范围、长方法目录；视频方案第10版有4个自身文件，切到current-production.md仍共用整包第10版及第1～10版列表；编辑正文、维护执行配置、新建方法和下载均在页面。
- 编号前缀表实际仍显示AE“设计版本独立”、MV“沿用方案版本号”、MC“同一素材版本内”，页尾仍解释V/C局部版本/候选。与已经实施的当前制作模型冲突，不仅是代码中的旧文本。
- 系统构想当前是上层人/影视创作/AI，下层审阅台承托数据模型与基础流程。暖纸底、淡绿基础块、细线箭头和原生字图，视觉主次清楚。

## 文件历史差异与保护点

辅助调查只读正式库与当前源码，未冒充浏览器验证：`review_desk/methods.py`按整个GUIDANCE对象保存方法/资源修订，payload.files为整包字典；评论按方法/资料对象+整包修订+文件路径+摘录定位，执行固定完整方法/资料和绑定摘要。

video-plan整包v1～v10，SKILL.md仅在1/2/4/5/6/7变化；3/8未改包内文件，9/10仅改references/current-production.md。audiovisual-scene的templates/reading.json自整包v5加入后一直未变。这两例说明不能把整包号直接标成文件号，文件变化需独立建立历史并映射旧准确引用。

Review的方法自身SKILL.md只是入口；完整正文、project-context和system-vision位于creative-system-review-texts准确投影。视频模板/案例来自手册和影视知识资源。取消顶层“共用资料”分类须将所需文件按原关系接入阅读，不能删除引用或复制可编辑正文。准确历史引用例外于普通点击默认最新；管理阅读不自动改执行绑定。

证据/实现入口：`production/working-methods-navigation/VERIFICATION.md`、`production/managed-methods.md`、`production/professional-methods.md`；审阅台 `review_desk/methods.py`、`review_desk/method_document.py`、`review_desk/static/methods.js`、`review_desk/business_codes.py`。源码支持契约判断，最终效果须执行者真实页面验收。

## 流程节点的实际方法映射

正式只读核对12种工作绑定、15个当前在用SKILL。每行左侧是面向人的流程能力，右侧是已有方法稳定身份的末段；不为图新增工作类型。

| 流程能力 | 已有方法 |
| --- | --- |
| 故事结构 | story-structure |
| 小说创作 | novel-writing |
| 影视剧本 | screenplay-scene |
| 视听设计 | audiovisual-scene |
| 实体、状态、素材抽取 | material-assessment |
| 图像方案 | image-plan |
| 声音方案 | voice-song-plan |
| 视频方案 | video-plan |
| 字层方案 | text-layer |
| 其他素材方案 | media-plan |
| 生成准备 | generation-preflight |
| 结果检查与返修 | result-review |
| 独立读者 | reader-review |
| 意见表达 | comment-polish-clear |
| 创作协作Review | creative-system-review |

采编与方向、剪辑成片当前无独立受管SKILL，不画成已实现按钮。生成与制作是流程动作，不把预检方法标成执行过真实生成。旧comment-polish未绑定，历史精确访问保留。节点映射必须适配新实例的真实注册/绑定，不能将本剧固定清单变成通用审阅台硬编码。

## 两张图沿用的迭代方法

已定向查0023原会话的用户反馈，不加载完整旧聊天：先要求整页一图，再指出文字多、死板、重点不明；尝试结构后明确数据模型与基础流程共同支撑协作；再弱化上层、调布局配色权重，最后使纸色与系统兼容。因此本任务继承“先内容关系、再可操作小样、再减字/权重、最后真实多宽度实读”的过程，不照抄旧图形状，也不继承当时图像生成授权。

执行者可直接使用的受管入口：`production/vision-collaboration/VERIFICATION.md`、`production/approach-workflow/VERIFICATION.md`、`planning/approach-workflow-graphics/approach-research.md`。后者已有迭代表，无需依赖发布者私有会话。源为`production/system-vision.md`，展示组件在desk的approach相关模块。模型依据见 `production/current-candidates/README.md`、`production/unique-origin/README.md`、`production/professional-methods.md`。

## 发布前可操作样例及边界

根会话在独立本机静态样例实际点击视频节点/文件，打开版本比较，确认默认上一版对最新版，再切左侧比较版；关闭后切另一单版本文件，比较按钮置灰、文件目录和正文选择相符。样例使用明确标注的示意正文，不连接业务库，不生成真实评论或方法版本。它验证左流程→右文件→正文/独立比较能完成工作、比较与版本选择能明显分区；并不证明正式文件历史、完整流程图、源投影/旧评论或窄屏已实现。

任务正文给出完整改后关系、选择与验收，执行不依赖该临时样例。实际实现须用video-plan多文件与源投影Review两个准确样例覆盖真实数据差异，完成完整图和迁移、正式生效、导出恢复后才算交付。

## 查重与隔离

0010既有准确阅读/评论/条件及导出能力保留复用，本次替换它的人机组织方案。0009/0011负责方法实质与全剧数据，不接管本次文件版本契约和管理页；可开发并行，正式方法及数据库增量写入串行，兼容其执行时最新成果。不将cycle-06已完成的独立复验恢复成待办。发布会话不调用do/run/mrun、不集成或部署。

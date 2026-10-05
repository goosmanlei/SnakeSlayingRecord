# Schema 6 本任务基准导出与空实例恢复核验计划

审查者 `/root/reset_supervisor`。本轮只读调查和编写计划，**没有执行下述代码、导出、恢复、测试、浏览器或负载**。守卫 check 成功：armed、监督锁有效、心跳 14.17 秒、supervision_confirmed=true、无错误。

建议只补一次真实基准的导出 → 空实例恢复 → 再导出，复用已过的 67 项聚焦测试。前置任务的全量恢复耗时 397.746 秒，不能以 180 秒代表合理预算；建议根安排不与性能测量、浏览器操作重叠的最多 900 秒窗口，阶段记录时间，超时停止并保留现场，不自动重跑。此为恢复正确性核验，不作为性能 A/B。

## 现场事实与易漏边界

来源为本任务 `run-baseline.json`、`preview/export/manifest.json` 和 `preview/export/objects.json`，以及系统候选的 `bundle.py`、`material_storage.py`、`material_archives.py`、相关测试和故事 `generation_publication.py`。准确基准快照 SHA-256：`5c6d00ee6efa7506201bbef46ffd69bde49f7300c4697fe66036e87ace7ed4f0`。

- 45 sources、271 comments、300 comment_events、6,236 objects、10,160 revisions、72,650 dependencies、17 configuration_events。
- 78,889 内容节点、2,312 定义、30 alias、2,547 定义版本、1,855 归档目录行。`material_aliases` 必须比较 alias_id、material_id 和原始 evidence，不能只看数量；历史 MATERIAL/REQUIREMENT 关联不可被当前 canonical_id 替换。
- 清单包含 1,307 个素材文件和 6 个元数据文件，另有 manifest 自身，合计 1,314 个受管输出文件。preview/assets 实际还有 91 个未列入清单文件；本计划不把它们预复制到恢复实例，避免“本来就有文件”掩盖遗漏。
- 1,855 归档中，837 个位于 export/assets，1,018 个位于 production。后者靠 objects.json 内的 material_archive_files 目录和 material-content.json 恢复，不在普通 assets 清单中。恢复实例的 production 目录必须最初不存在，验证其从目录重建及每份原字节的已登记 SHA/长度。
- bundle 遍历**全部修订**收集 components，包含历史原件；不可改成仅 current_records，也不能用素材列表 API 代替原件完整性核对。真实媒体文件的物理哈希不应变化；归档 JSON 的物理容器哈希与历史原文逻辑哈希是两种值，二者都要核对。
- 故事私有 generation_publications 的 2 行属于本机发布幂等回执，自旧格式就不在通用 bundle 契约。本轮应保留原快照并确认未动，单列“未由通用导出恢复”，不能称任意 SQLite 私有表全部恢复。已有说明见 production/generation-workspaces.md、production/ui-material-model/data-validation.md。
- `export` 可能规范化旧 metadata 容器，并写入 material_archive_files；因此只能在新克隆上运行，不得直接给 immutable 快照、preview 或 functional 调用 export。最终比较既看源克隆导出前后，也看恢复结果；不能仅比较两份已共同发生错误的新导出。
- **源克隆不需要复制 1,018 个 production 历史归档实体文件。** 当前 `bundle.export` 不调用 `archives.collect`，当前 `material_archives.py` 也没有此函数。导出依次调用只读 SQL 的 sources/comments/events/objects/revisions、round/plan/storage dump；production 归档只作为 material_archive_files 的 path/container 行输出。实际文件读取仅发生于 export/assets 的 component 校验/容器编码、SOURCE/结构/Favicon 素材及关系布局。component 的原文解析经 archives.resolver 从源克隆的完整 SQLite 内容图读取，不会转去 production 路径。`material_model.verify` 的归档循环也按 container 解码，不读取目录实体；它由 restore 调用，而不是 export。计划在源 export 前后断言 source/production 不存在，在 restore 前断言 empty/production 不存在，恢复后才逐个验证实际重建路径。
- **22 张公共业务表和 sqlite_sequence 分开判定。** 旧证据所谓“23 表”包含 sqlite_sequence；后者没有被 bundle 序列化，空库 restore 通过显式 event ID 插入生成计数器。源库若删除过最高 ID，原高水位可大于 max(id)，不能把原计数器逐字节相等作为一般业务恢复契约。此基准只读实查 comment_events 为 300 行、ID 8…307、seq=307；configuration_events 为 17 行、ID 1…20、seq=20。计划单列这两项，验证恢复计数器等于导入最大 ID，并记录与原计数器是否相等；不靠写入新评论验证。源克隆自身的导出前后比较仍包含全部表、私有回执和 sqlite_sequence，要求完全不变。

## 与 PERF002 的关系及已有覆盖

PERF002 的公开 expand 出口按每个位置复制可变 JSON 树；内部缓存仅供递归重用。restore_content 校验定义、restore 的历史 payload 校验、archive read_scope 的活跃事务 resolver、素材模型 verify 都会调用这条路径。`bundle.restore` 最后已调用 material_model.verify，无需重复再运行一次 CLI verify。

`AO-PERF-002-focused-tests.log` 已记录共享子树不同位置/不同调用、旧/新 recipe、损坏内容重试、原始 JSON 字节、嵌套 JSON 归档与空恢复、SQLite spill 时同事务原件解析通过。故本轮不再重跑整套；实际快照补验增加一次真实定义返回值的本地修改隔离，随后全量物理表、准确逻辑 payload、原件与再导出比较。只修改内存返回对象，不创建任何业务判断。

## 根可执行的单次有界核验

以下命令从**故事任务 worktree 根目录**执行。它只创建新的 `.runtime/autonomous-optimization/schema6-roundtrip-reset-01`；若目录已存在立即失败，不能覆盖旧证据。188 行内嵌 Python 已通过 ast.parse 静态语法检查，代码未执行。执行前由根确认独占窗口；守卫到期仍优先停止。运行期间每个阶段输出一行，根可保持进度沟通。

```sh
PYTHONPATH=.runtime/autonomous-optimization/system-worktree python3 - <<'PY'
import hashlib, json, os, signal, sqlite3, subprocess, sys, time
from pathlib import Path
from review_desk import material_archives as archives, material_storage as storage, production
from review_desk.store import Store, canonical

task = Path.cwd().resolve()
base = task / '.runtime/autonomous-optimization'
system = base / 'system-worktree'
frozen = base / 'preview/.runtime/generation-base.sqlite3'
original = base / 'preview/export'
run = base / 'schema6-roundtrip-reset-01'
run.mkdir(exist_ok=False)
started = time.monotonic()
receipt = {'format':'schema6-roundtrip-audit-v1','stages':[],'formal_writes':False}
expected = '5c6d00ee6efa7506201bbef46ffd69bde49f7300c4697fe66036e87ace7ed4f0'
def remaining():
    value = 900 - (time.monotonic() - started)
    if value <= 0: raise TimeoutError('900 second isolated validation budget reached')
    return value
def stage(name):
    remaining(); receipt['stages'].append({'name':name,'elapsed':time.monotonic()-started})
    print(json.dumps(receipt['stages'][-1]),flush=True)
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            remaining(); h.update(block)
    return h.hexdigest()
def copy_file(src,dst):
    assert src.is_file() and not src.is_symlink(), str(src)
    dst.parent.mkdir(parents=True,exist_ok=True)
    # macOS APFS copy-on-write copy, never a hard link or a symlink.
    subprocess.run(['/bin/cp','-c',str(src),str(dst)],check=True,timeout=remaining())
def source_code():
    return {str(p.relative_to(system)):sha(p) for p in (system/'review_desk').rglob('*')
            if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.js','.css','.html'}}
def cli(instance,command):
    stage(command+' '+instance.name)
    env=os.environ.copy();env['PYTHONPATH']=str(system)
    with (run/(instance.name+'-'+command+'.log')).open('w') as log:
        child=subprocess.Popen([sys.executable,'-m','review_desk','--instance',str(instance),command],
            cwd=system,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            rc=child.wait(timeout=remaining())
            if rc: raise RuntimeError(f'{command} exited {rc}; see log')
        except BaseException:
            if child.poll() is None:
                os.killpg(child.pid,signal.SIGTERM)
                try: child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid,signal.SIGKILL);child.wait()
            raise
def ro(path):
    db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True);db.execute('PRAGMA query_only=ON');return db
def table_rows(db,table):
    # Full raw physical rows, including encoded revision envelopes and evidence JSON.
    rows=db.execute('SELECT * FROM "'+table.replace('"','""')+'"').fetchall()
    return sorted(canonical(list(row)) for row in rows)
def rows_hash(rows):
    h=hashlib.sha256()
    for row in rows:h.update(row.encode());h.update(b'\n')
    return h.hexdigest()
def physical_snapshot(path):
    db=ro(path)
    try:
        names=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name NOT LIKE 'sqlite_%' OR name='sqlite_sequence') ORDER BY name")]
        result={}
        for name in names:
            remaining();rows=table_rows(db,name)
            result[name]={'rows':len(rows),'sha256':rows_hash(rows)}
        return result
    finally:db.close()
try:
    stage('preflight')
    guard=subprocess.run([sys.executable,'scripts/autonomous_optimization_guard.py','check'],
        cwd=task,capture_output=True,text=True,timeout=remaining())
    g=json.loads(guard.stdout);assert guard.returncode==0 and g['phase']=='armed' and g['watcher']['supervision_confirmed']
    receipt['guard']={'phase':g['phase'],'supervision_confirmed':True}  # no lease data
    assert sha(frozen)==expected
    code=source_code();receipt['system_head']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=system,text=True).strip()
    receipt['source_code_sha256']=code;receipt['snapshot_sha256']=expected
    manifest=json.loads((original/'manifest.json').read_text());assert manifest['schema_version']==6
    src,dst=run/'source',run/'empty'
    copy_file(frozen,src/'.runtime/review.sqlite3')
    assert not (dst/'.runtime/review.sqlite3').exists() and not (dst/'production').exists()
    frozen_rows=physical_snapshot(frozen);source_initial=physical_snapshot(src/'.runtime/review.sqlite3')
    receipt['source_initial_all_tables']=source_initial
    assert source_initial==frozen_rows,'copied source rows differ before any candidate reads'
    for instance in (src,dst):copy_file(base/'preview/config/instance.json',instance/'config/instance.json')
    layout=base/'preview/config/entity-relationship-layout.json'
    if layout.exists():copy_file(layout,src/'config/entity-relationship-layout.json')
    # Copy only manifest-listed assets; never seed restored production archives.
    for name,expected_hash in manifest['files'].items():
        if name.startswith('assets/'):
            copy_file(original/name,src/'export'/name)
            assert sha(src/'export'/name)==expected_hash,name
    stage('real cached definition mutation isolation')
    store=Store(src/'.runtime/review.sqlite3')
    try:
        key=store.db.execute('SELECT definition_id FROM material_definition_versions ORDER BY material_id,number LIMIT 1').fetchone()[0]
        with production.read_scope(store):
            first=storage.expand(store,key);clean=canonical(first);second=storage.expand(store,key)
            def mutate(value):
                if isinstance(value,dict):
                    for child in value.values():
                        if mutate(child):return True
                    value['__local_isolation_probe__']='not saved';return True
                if isinstance(value,list):value.append({'__local_isolation_probe__':'not saved'});return True
                return False
            assert mutate(first)
            assert canonical(second)==clean and canonical(storage.expand(store,key))==clean
        assert not hasattr(store,'_production_reads')
        receipt['actual_definition_isolation']={'definition_id':key,'passed':True}
    finally:store.close()
    source_before_export=physical_snapshot(src/'.runtime/review.sqlite3')
    assert source_before_export==source_initial,'candidate read/mutation isolation changed stored rows'
    assert not (src/'production').exists(),'source production archives were unexpectedly seeded'
    receipt['source_before_export_all_tables']=source_before_export
    cli(src,'export')
    source_after_export=physical_snapshot(src/'.runtime/review.sqlite3')
    receipt['source_after_export_all_tables']=source_after_export
    assert source_after_export==source_before_export,'source export changed one or more stored tables'
    assert not (src/'production').exists(),'export unexpectedly wrote source production archives'
    fresh=json.loads((src/'export/manifest.json').read_text())
    assert fresh==manifest,'source export differs from frozen public baseline; inspect before proceeding'
    for name in ['manifest.json',*fresh['files']]:copy_file(src/'export'/name,dst/'export'/name)
    assert not (dst/'.runtime/review.sqlite3').exists() and not (dst/'production').exists()
    cli(dst,'restore')
    stage('raw tables and exact logical history')
    before,after=ro(frozen),ro(dst/'.runtime/review.sqlite3')
    try:
        names={r[0] for r in before.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        restored={r[0] for r in after.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        assert names-{'generation_publications'}==restored
        receipt['tables']={}
        for name in sorted(restored):
            remaining();left,right=table_rows(before,name),table_rows(after,name);assert left==right,name
            receipt['tables'][name]={'rows':len(left),'sha256':rows_hash(left)}
        receipt['outside_public_contract']={'generation_publications':len(table_rows(before,'generation_publications'))}
        old_seq=dict(before.execute('SELECT name,seq FROM sqlite_sequence'))
        new_seq=dict(after.execute('SELECT name,seq FROM sqlite_sequence'))
        event_max={name:after.execute('SELECT max(id) FROM '+name).fetchone()[0] for name in ('comment_events','configuration_events')}
        assert new_seq==event_max,'fresh restore event sequence differs from imported maximum ID'
        receipt['event_sequence_counters']={'source':old_seq,'restored':new_seq,'imported_max_id':event_max,
            'equal_for_this_snapshot':old_seq==new_seq,'contract':'reconstructed SQLite counters; not serialized bundle rows'}
        for db in (before,after):
            assert db.execute('PRAGMA integrity_check').fetchall()==[('ok',)]
            assert db.execute('PRAGMA foreign_key_check').fetchall()==[]
    finally:before.close();after.close()
    left,right=Store(src/'.runtime/review.sqlite3'),Store(dst/'.runtime/review.sqlite3')
    try:
        with production.read_scope(left),production.read_scope(right):
            logical={row['id']:row['payload'] for row in left.db.execute('SELECT id,payload FROM revisions')}
            count=0
            for row in right.db.execute('SELECT id,payload FROM revisions'):
                remaining();assert logical.pop(row['id'])==row['payload'],row['id'];count+=1
            assert not logical;receipt['exact_logical_revision_payloads']=count
        # Use restored DB's active resolver to exercise PERF002, including historical recipes.
        with archives.read_scope(right):
            count=0
            for row in right.db.execute('SELECT path,container FROM material_archive_files ORDER BY path'):
                remaining();document=json.loads(row['container']);path=dst/row['path']
                assert path.resolve().is_relative_to(dst.resolve()) and path.is_file() and not path.is_symlink()
                raw=archives.read_bytes(path)
                assert len(raw)==document['bytes'] and hashlib.sha256(raw).hexdigest()==document['sha256'],row['path']
                count+=1
            receipt['historic_archive_original_hashes']=count
    finally:left.close();right.close()
    restored_before_export=physical_snapshot(dst/'.runtime/review.sqlite3')
    receipt['restored_before_export_all_tables']=restored_before_export
    cli(dst,'export')
    restored_after_export=physical_snapshot(dst/'.runtime/review.sqlite3')
    receipt['restored_after_export_all_tables']=restored_after_export
    assert restored_after_export==restored_before_export,'restored export changed stored rows'
    stage('deterministic bundle and source preservation')
    again=json.loads((dst/'export/manifest.json').read_text());assert again==fresh
    for name in ['manifest.json',*fresh['files']]:assert sha(src/'export'/name)==sha(dst/'export'/name),name
    receipt['deterministic_export_files']=len(fresh['files'])+1
    assert physical_snapshot(src/'.runtime/review.sqlite3')==source_initial,'source clone changed during later verification'
    assert sha(frozen)==expected and source_code()==code
    receipt['passed']=True
except BaseException as exc:
    receipt['passed']=False;receipt['error']=type(exc).__name__+': '+str(exc)
    raise
finally:
    receipt['elapsed_seconds']=time.monotonic()-started
    (run/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'passed':receipt.get('passed'),'receipt':str(run/'receipt.json'),'elapsed_seconds':receipt['elapsed_seconds']},ensure_ascii=False),flush=True)
PY
```

补充判断：若 source export 与基准 manifest 不相同，先看物理元数据规范化差异，不能绕过断言直接通过；若候选或输入在运行时变化，保留失败现场并重新界定验证输入。成功 receipt 只证明此快照与此代码指纹的恢复，不能证明正式活库被发布，也不能证明 UI 验收。

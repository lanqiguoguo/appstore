#!/usr/bin/env python3
"""从上游 apps/ 与自定义 custom/apps/ 生成 1Panel v1 协议产物。

目录约定（app_repo 含 /main 分支段）：
  apps/<key>/…                 上游应用（merge 自 1Panel-dev/appstore，勿手改）
  custom/apps/<key>/…          自定义应用；同 key 时整体替换上游应用
  data.yaml                    全局标签定义（来自上游，可追加私有标签）
产物（每个渠道一套，目录名同时用作索引内绝对 URL 的首段）：
  <channel>/1panel.json.version.txt      整数时间戳，变化触发面板同步
  <channel>/1panel.json.zip              根级直含 1panel.json
  <channel>/1panel/<key>/logo.png        图标
  <channel>/1panel/<key>/<ver>/docker-compose.yml
  <channel>/1panel/<key>/<ver>/<key>-<ver>.tar.gz   版本包随仓库提交，raw 直出

dev/ 对应面板 mode=dev 渠道，stable/ 对应 mode=stable 稳定渠道。面板只会按
mode 目录重新派生下载地址，但图标用的是索引内嵌的绝对地址，因此各渠道索引
必须引用自身目录——不能用简单镜像复制，否则 stable 面板会持续请求 dev。

本脚本不调用任何外部命令；提交回推由 .github/workflows/publish.yml 完成。
"""

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tarfile
import time
import zipfile
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
UPSTREAM_DIR = REPO / "apps"
CUSTOM_DIR = REPO / "custom" / "apps"
DATA_YAML = REPO / "data.yaml"

RAW_BASE = "https://raw.githubusercontent.com/lanqiguoguo/appstore/main"
CHANNELS = ("dev", "stable")
OUT_DIRS = {channel: REPO / channel for channel in CHANNELS}

VERSION_NAME_RE = re.compile(r"^\d+(\.\d+)*$")

warnings: list[str] = []
errors: list[str] = []


def warn(msg: str):
    warnings.append(msg)
    print("[警告] " + msg)


def error(msg: str):
    errors.append(msg)
    print("[错误] " + msg)


def load_yaml(path: Path):
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        text = f.read()
    try:
        return yaml.safe_load(text) or {}
    except yaml.YAMLError as e:
        # 上游个别文件含 Tab 缩进（如 jupyter-notebook），按 4 空格展开后重试
        if "\t" in text:
            warn(str(path.relative_to(REPO)) + ": 含 Tab 缩进，已自动容忍")
            return yaml.safe_load(text.replace("\t", "    ")) or {}
        raise


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dir_fingerprint(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(root)).encode())
            h.update(sha256_file(p).encode())
    return h.hexdigest()


def fingerprint_ts(root: Path) -> int:
    """由目录内容指纹派生的稳定整数时间戳。"""
    return int(dir_fingerprint(root)[:8], 16)


def normalize_property(key: str, raw: dict) -> dict:
    """补齐 dto.AppProperty 要求的字段；注意 Required 的 JSON tag 是大写 R。"""
    prop = {
        "name": key, "type": "app", "tags": [], "shortDescZh": "", "shortDescEn": "",
        "description": {}, "key": key, "Required": [], "crossVersionUpdate": False,
        "limit": 0, "recommend": 0, "website": "", "github": "", "document": "",
        "version": 0, "gpuSupport": False,
    }
    prop.update(raw or {})
    prop["key"] = key
    if not prop["name"]:
        prop["name"] = key
    return prop


def tree_snapshot(root: Path) -> dict:
    snap = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            snap[str(p.relative_to(root))] = sha256_file(p)
    return snap


def load_global_tags() -> dict:
    """data.yaml 的全局标签表：key -> {name, sort, locales}。"""
    meta = load_yaml(DATA_YAML)
    table = {}
    for t in (meta.get("additionalProperties") or {}).get("tags") or []:
        table[t.get("key")] = t
    if not table:
        error("data.yaml 中没有标签定义")
    return table


def collect_app_dirs() -> dict:
    """双根收集：custom/apps 同 key 整体覆盖 apps/。"""
    dirs = {}
    for root, origin in ((UPSTREAM_DIR, "上游"), (CUSTOM_DIR, "自定义")):
        if not root.is_dir():
            continue
        for d in sorted(root.iterdir()):
            if d.is_dir():
                if d.name in dirs and origin == "自定义":
                    warn(f"{d.name}: 自定义版本覆盖上游应用")
                dirs[d.name] = d
    return dirs


def build_app(key: str, app_dir: Path, channel: str):
    logo_path = app_dir / "logo.png"
    meta_path = app_dir / "data.yml"
    if not logo_path.exists():
        error(key + ": 缺少 logo.png，面板同步时下载图标失败会中断整个索引同步")
        return None, []
    if not meta_path.exists():
        error(key + ": 缺少 data.yml")
        return None, []

    meta = load_yaml(meta_path)
    prop = normalize_property(key, meta.get("additionalProperties"))
    if prop.get("version"):
        warn(key + ": additionalProperties.version 会成为最低面板版本门禁，已强制置 0")
        prop["version"] = 0

    read_me = ""
    readme_path = app_dir / "README.md"
    if readme_path.exists():
        read_me = readme_path.read_text(encoding="utf-8")

    versions, packages = [], []
    app_ts = fingerprint_ts(app_dir)
    for ver_dir in sorted(p for p in app_dir.iterdir() if p.is_dir()):
        ver = ver_dir.name
        compose = ver_dir / "docker-compose.yml"
        if not compose.exists():
            if (ver_dir / "data.yml").exists():
                warn(key + "/" + ver + ": 缺少 docker-compose.yml，该版本将被跳过")
            continue
        if not VERSION_NAME_RE.match(ver):
            warn(key + "/" + ver + ": 非纯数字分段版本名，升级比较将失效（latest 永不提示升级），建议改为真实版本号")

        fields = (load_yaml(ver_dir / "data.yml").get("additionalProperties") or {}).get("formFields") or []
        versions.append({
            "name": ver,
            "lastModified": fingerprint_ts(ver_dir),
            "downloadUrl": RAW_BASE + "/" + channel + "/1panel/" + key + "/" + ver + "/" + key + "-" + ver + ".tar.gz",
            "downloadCallBackUrl": "",
            "additionalProperties": {"formFields": fields, "supportVersion": 0},
        })
        packages.append((ver, ver_dir))

    if not versions:
        error(key + ": 没有任何包含 docker-compose.yml 的版本目录")
        return None, []

    define = {
        "icon": RAW_BASE + "/" + channel + "/1panel/" + key + "/logo.png",
        "name": prop["name"],
        "readMe": read_me,
        "lastModified": app_ts,
        "additionalProperties": prop,
        "versions": versions,
    }
    return define, packages


def pack_tar(out: Path, key: str, ver: str, ver_dir: Path):
    """确定性打包：gzip 头与 tar 成员 mtime 固定为 0，
    否则跨机构建字节不同会破坏产物快照幂等比较。"""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        for src in sorted(ver_dir.rglob("*")):
            if not src.is_file():
                continue
            info = tarfile.TarInfo(name=str(Path(key) / ver / src.relative_to(ver_dir)))
            info.size = src.stat().st_size
            info.mtime = 0
            info.mode = 0o755 if os.access(src, os.X_OK) else 0o644
            with open(src, "rb") as f:
                tf.addfile(info, f)
    out.write_bytes(gzip.compress(buf.getvalue(), mtime=0))


def build_channel(channel: str, global_tags: dict) -> bool:
    out_dir = OUT_DIRS[channel]

    stage = REPO / ".build-stage"
    shutil.rmtree(stage, ignore_errors=True)
    (stage / "1panel").mkdir(parents=True)

    apps, package_count = [], 0
    used_tag_keys = set()
    for key, app_dir in sorted(collect_app_dirs().items()):
        try:
            define, packages = build_app(key, app_dir, channel)
        except Exception as e:  # 单个应用元数据异常只跳过自身，不中断全量构建
            error(key + ": 解析失败，已跳过（" + type(e).__name__ + ": " + str(e)[:120] + "）")
            continue
        if define is None:
            continue
        unknown = [t for t in define["additionalProperties"]["tags"] if t not in global_tags]
        if unknown:
            error(key + ": 引用了 data.yaml 未定义的标签 " + repr(unknown) + "，请改用已定义键或往 data.yaml 追加")
            continue
        apps.append(define)
        used_tag_keys.update(define["additionalProperties"]["tags"])
        logo_dst = stage / "1panel" / key / "logo.png"
        logo_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(app_dir / "logo.png", logo_dst)

        for ver, ver_dir in packages:
            ver_dst = stage / "1panel" / key / ver
            ver_dst.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ver_dir / "docker-compose.yml", ver_dst / "docker-compose.yml")
            pack_tar(ver_dst / (key + "-" + ver + ".tar.gz"), key, ver, ver_dir)
            package_count += 1

    # 标签全量取自 data.yaml（与官方一致，前端按 sort 排序展示筛选按钮）
    defined = [(t.get("sort", 0), k, t) for k, t in global_tags.items()]
    tags = [{"key": k, "name": t.get("name", k), "sort": s, "locales": t.get("locales", {})}
            for s, k, t in sorted(defined)]
    index_last_modified = max((a["lastModified"] for a in apps), default=0)
    index = {
        "valid": True,
        "violations": [],
        "lastModified": index_last_modified,
        "additionalProperties": {"tags": tags, "version": ""},
        "apps": apps,
    }
    index_bytes = json.dumps(index, ensure_ascii=False, indent=2).encode()
    (stage / "1panel.json").write_bytes(index_bytes)
    # 固定 zip 内部时间戳：否则每次构建字节不同，幂等检测在 CI 上永远失效
    zinfo = zipfile.ZipInfo("1panel.json", date_time=(1980, 1, 1, 0, 0, 0))
    zinfo.compress_type = zipfile.ZIP_DEFLATED
    zinfo.external_attr = 0o644 << 16
    with zipfile.ZipFile(stage / "1panel.json.zip", "w") as zf:
        zf.writestr(zinfo, index_bytes)

    old_snap = tree_snapshot(out_dir)
    old_snap.pop("1panel.json.version.txt", None)
    new_snap = tree_snapshot(stage)
    new_snap.pop("1panel.json.version.txt", None)
    if out_dir.exists() and old_snap == new_snap:
        shutil.rmtree(stage)
        print("[%s] 内容无变化，version.txt 保持不变" % channel)
        return True

    shutil.rmtree(out_dir, ignore_errors=True)
    stage.rename(out_dir)
    ts_file = out_dir / "1panel.json.version.txt"
    ts_file.write_text(str(int(time.time())))
    print("[%s] 已生成 %d 个应用、%d 个版本包" % (channel, len(apps), package_count))
    return verify(out_dir)


def verify(root: Path) -> bool:
    ok = True
    with zipfile.ZipFile(root / "1panel.json.zip") as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        if names != ["1panel.json"]:
            error(str(root) + ": zip 布局非法：" + repr(names) + "，必须仅含根级 1panel.json")
            ok = False
    index = json.loads((root / "1panel.json").read_text())
    seen_assets = set()
    for app in index["apps"]:
        key = app["additionalProperties"]["key"]
        logo = root / "1panel" / key / "logo.png"
        if not logo.exists():
            error(f"{root.name}/1panel 下缺少 {key}/logo.png")
            ok = False
        for v in app["versions"]:
            ver = v["name"]
            ver_dir = root / "1panel" / key / ver
            compose = ver_dir / "docker-compose.yml"
            if not compose.exists():
                error(f"{root.name}/{key}/{ver}: 缺少 docker-compose.yml，详情页会报错")
                ok = False
            asset_name = key + "-" + ver + ".tar.gz"
            seen_assets.add(str(Path("1panel") / key / ver / asset_name))
            pkg = ver_dir / asset_name
            if not pkg.exists():
                error(key + "/" + ver + ": 缺少版本包 " + str(pkg.relative_to(root)))
                ok = False
                continue
            prefix = key + "/" + ver + "/"
            with tarfile.open(pkg) as tf:
                bad = [m for m in tf.getnames() if not m.startswith(prefix)]
            if bad:
                error(asset_name + ": 包内顶层不是 " + prefix + "：" + repr(bad[:3]))
                ok = False
    for p in sorted(root.rglob("*.tar.gz")):
        rel = str(p.relative_to(root))
        if rel not in seen_assets:
            warn(rel + ": 索引未引用的孤立版本包")
    print("[%s] 自检通过" % root.name if ok else "[%s] 自检失败" % root.name)
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true",
                        help="仅校验现有各渠道产物，不重新生成")
    args = parser.parse_args()

    if args.verify_only:
        ok = True
        for channel in CHANNELS:
            if not OUT_DIRS[channel].is_dir():
                error(channel + ": 产物目录不存在")
                ok = False
                continue
            ok = verify(OUT_DIRS[channel]) and ok
        sys.exit(0 if ok else 1)

    if not UPSTREAM_DIR.is_dir():
        error("找不到 apps/ 目录（上游内容未合并？）")
        sys.exit(1)

    global_tags = load_global_tags()
    if errors:
        sys.exit(1)

    ok_all = True
    for channel in CHANNELS:
        print("=== 构建 %s/ ===" % channel)
        ok_all = build_channel(channel, global_tags) and ok_all

    if not ok_all:
        sys.exit(1)
    if warnings:
        print()
        print("共 %d 条警告，详见上方" % len(warnings))


if __name__ == "__main__":
    main()

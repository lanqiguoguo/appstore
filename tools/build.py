#!/usr/bin/env python3
"""从 apps/ 作者目录生成 1Panel v1 协议产物。

面板拉取路径约定（mode=dev，app_repo 含 /main 分支段）：
  dev/1panel.json.version.txt            整数时间戳，变化触发面板同步
  dev/1panel.json.zip                    根级直含 1panel.json（面板解压后直读）
  dev/1panel/<key>/logo.png              图标（索引以 raw 绝对 URL 引用）
  dev/1panel/<key>/<ver>/docker-compose.yml
  dev/1panel/<key>/<ver>/<key>-<ver>.tar.gz   版本包随仓库提交，raw 直出

所有产物只依赖 raw 单域名，不经过 github.com。
本脚本不调用任何外部命令；提交回推由 .github/workflows/publish.yml 完成。

lastModified 说明：不依赖 git 历史，改用应用目录内容的稳定指纹派生，
保证跨机器构建结果一致，且内容变化时随之变化。
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
APPS_DIR = REPO / "apps"
DEV_DIR = REPO / "dev"

RAW_BASE = "https://raw.githubusercontent.com/lanqiguoguo/appstore/main"

VERSION_NAME_RE = re.compile(r"^\d+(\.\d+)*$")

# 面板渲染标签名只用 locales（不回退到 key），必须为每种语言提供非空文案
LOCALE_FIELDS = ("en", "ja", "ms", "pt-br", "ru", "zh-hant", "zh", "ko")
TAG_LOCALES = {
    "Tool": {"en": "Tool", "ja": "ツール", "ms": "Alat", "pt-br": "Ferramenta",
             "ru": "Инструмент", "zh-hant": "工具", "zh": "工具", "ko": "도구"},
    "Local": {"en": "Local", "ja": "ローカル", "ms": "Tempatan", "pt-br": "Local",
              "ru": "Локальный", "zh-hant": "本地", "zh": "本地", "ko": "로컬"},
    "Server": {"en": "Server", "ja": "サーバー", "ms": "Pelayan", "pt-br": "Servidor",
               "ru": "Сервер", "zh-hant": "伺服器", "zh": "服务器", "ko": "서버"},
    "AI": {k: "AI" for k in LOCALE_FIELDS},
}

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
        return yaml.safe_load(f) or {}


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


def build_app(key: str, app_dir: Path):
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
            "downloadUrl": RAW_BASE + "/dev/1panel/" + key + "/" + ver + "/" + key + "-" + ver + ".tar.gz",
            "downloadCallBackUrl": "",
            "additionalProperties": {"formFields": fields, "supportVersion": 0},
        })
        packages.append((ver, ver_dir))

    if not versions:
        error(key + ": 没有任何包含 docker-compose.yml 的版本目录")
        return None, []

    define = {
        "icon": RAW_BASE + "/dev/1panel/" + key + "/logo.png",
        "name": prop["name"],
        "readMe": read_me,
        "lastModified": app_ts,
        "additionalProperties": prop,
        "versions": versions,
    }
    return define, packages


def pack_tar(out: Path, key: str, ver: str, ver_dir: Path):
    """确定性打包：gzip 头与 tar 成员 mtime 固定为 0，
    否则跨机构建字节不同会破坏 dev/ 快照幂等比较。"""
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


def build() -> bool:
    if not APPS_DIR.exists():
        error("找不到 apps/ 目录")
        return False

    stage = REPO / ".build-stage"
    shutil.rmtree(stage, ignore_errors=True)
    (stage / "1panel").mkdir(parents=True)

    apps, tag_keys = [], []
    package_count = 0
    for app_dir in sorted(APPS_DIR.iterdir()):
        if not app_dir.is_dir():
            continue
        key = app_dir.name
        define, packages = build_app(key, app_dir)
        if define is None:
            continue
        apps.append(define)
        tag_keys.extend(define["additionalProperties"]["tags"])
        logo_dst = stage / "1panel" / key / "logo.png"
        logo_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(app_dir / "logo.png", logo_dst)

        for ver, ver_dir in packages:
            ver_dst = stage / "1panel" / key / ver
            ver_dst.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ver_dir / "docker-compose.yml", ver_dst / "docker-compose.yml")
            pack_tar(ver_dst / (key + "-" + ver + ".tar.gz"), key, ver, ver_dir)
            package_count += 1

    tags = [{"key": t, "name": t, "sort": i, "locales": TAG_LOCALES.get(t, {k: t for k in LOCALE_FIELDS})}
            for i, t in enumerate(sorted(set(tag_keys)))]
    # 索引级 lastModified 取各应用时间戳最大值：保证同内容构建字节一致（幂等），
    # 面板判断商店是否更新只依赖 1panel.json.version.txt，与此字段无关
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

    old_snap = tree_snapshot(DEV_DIR)
    old_snap.pop("1panel.json.version.txt", None)
    new_snap = tree_snapshot(stage)
    new_snap.pop("1panel.json.version.txt", None)
    if DEV_DIR.exists() and old_snap == new_snap:
        shutil.rmtree(stage)
        print("内容无变化，version.txt 保持不变")
        return True

    shutil.rmtree(DEV_DIR, ignore_errors=True)
    stage.rename(DEV_DIR)
    ts_file = DEV_DIR / "1panel.json.version.txt"
    ts_file.write_text(str(int(time.time())))
    print("已生成 %d 个应用、%d 个版本包" % (len(apps), package_count))
    return verify()


def verify() -> bool:
    ok = True
    with zipfile.ZipFile(DEV_DIR / "1panel.json.zip") as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        if names != ["1panel.json"]:
            error("zip 布局非法：" + repr(names) + "，必须仅含根级 1panel.json")
            ok = False
    index = json.loads((DEV_DIR / "1panel.json").read_text())
    seen_assets = set()
    for app in index["apps"]:
        key = app["additionalProperties"]["key"]
        logo = DEV_DIR / "1panel" / key / "logo.png"
        if not logo.exists():
            error(key + ": dev/1panel 下缺少 logo.png")
            ok = False
        for v in app["versions"]:
            ver = v["name"]
            ver_dir = DEV_DIR / "1panel" / key / ver
            compose = ver_dir / "docker-compose.yml"
            if not compose.exists():
                error(key + "/" + ver + ": dev 下缺少 docker-compose.yml，详情页会报错")
                ok = False
            asset_name = key + "-" + ver + ".tar.gz"
            seen_assets.add(str(Path("1panel") / key / ver / asset_name))
            pkg = ver_dir / asset_name
            if not pkg.exists():
                error(key + "/" + ver + ": 缺少版本包 " + str(pkg.relative_to(DEV_DIR)))
                ok = False
                continue
            prefix = key + "/" + ver + "/"
            with tarfile.open(pkg) as tf:
                bad = [m for m in tf.getnames() if not m.startswith(prefix)]
            if bad:
                error(asset_name + ": 包内顶层不是 " + prefix + "：" + repr(bad[:3]))
                ok = False
    for p in sorted(DEV_DIR.rglob("*.tar.gz")):
        rel = str(p.relative_to(DEV_DIR))
        if rel not in seen_assets:
            warn(rel + ": 索引未引用的孤立版本包")
    print("自检通过" if ok else "自检失败")
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true",
                        help="仅校验现有 dev/，不重新生成")
    args = parser.parse_args()

    if args.verify_only:
        sys.exit(0 if verify() else 1)

    if not build():
        sys.exit(1)
    if warnings:
        print()
        print("共 %d 条警告，详见上方" % len(warnings))


if __name__ == "__main__":
    main()

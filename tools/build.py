#!/usr/bin/env python3
"""从 apps/ 作者目录生成 1Panel v1 协议产物。

面板拉取路径约定（mode=dev）：
  dev/1panel.json.version.txt            整数时间戳，变化触发面板同步
  dev/1panel.json.zip                    根级直含 1panel.json（面板解压后直读）
  dev/1panel/<key>/logo.png              图标（索引以 raw 绝对 URL 引用）
  dev/1panel/<key>/<ver>/docker-compose.yml
  dist/<key>-<ver>.tar.gz                版本包，包内顶层必须是 <key>/<ver>/，经 Release 发布

本脚本不调用任何外部命令，只做文件生成与校验；
提交回推与 Release 上传由 .github/workflows/publish.yml 完成，
手动发布的命令见 README「发布」一节。

lastModified 说明：不依赖 git 历史，改用应用目录内容的稳定指纹派生，
保证跨机器构建结果一致，且内容变化时随之变化。
"""

import argparse
import hashlib
import json
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
DIST_DIR = REPO / "dist"

RAW_BASE = "https://raw.githubusercontent.com/lanqiguoguo/appstore/main"
RELEASE_URL_BASE = "https://github.com/lanqiguoguo/appstore/releases/download/packages"

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
            "downloadUrl": RELEASE_URL_BASE + "/" + key + "-" + ver + ".tar.gz",
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


def pack_tar(key: str, ver: str, ver_dir: Path) -> Path:
    DIST_DIR.mkdir(exist_ok=True)
    manifest_path = DIST_DIR / ".sources.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    src_state = {str(p.relative_to(ver_dir)): sha256_file(p)
                 for p in sorted(ver_dir.rglob("*")) if p.is_file()}
    entry_key = key + "-" + ver
    out = DIST_DIR / (entry_key + ".tar.gz")
    if manifest.get(entry_key) == src_state and out.exists():
        return out

    with tarfile.open(out, "w:gz") as tf:
        for p in sorted(ver_dir.rglob("*")):
            if p.is_file():
                tf.add(p, arcname=str(Path(key) / ver / p.relative_to(ver_dir)))
    manifest[entry_key] = src_state
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    return out


def build() -> bool:
    if not APPS_DIR.exists():
        error("找不到 apps/ 目录")
        return False

    stage = REPO / ".build-stage"
    shutil.rmtree(stage, ignore_errors=True)
    (stage / "1panel").mkdir(parents=True)

    apps, all_packages, tag_keys = [], [], []
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
            compose_dst = stage / "1panel" / key / ver / "docker-compose.yml"
            compose_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ver_dir / "docker-compose.yml", compose_dst)
            all_packages.append(pack_tar(key, ver, ver_dir))

    tags = [{"key": t, "name": t, "sort": i, "locales": {}}
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
    with zipfile.ZipFile(stage / "1panel.json.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("1panel.json", index_bytes)

    old_snap = tree_snapshot(DEV_DIR)
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
    print("已生成 %d 个应用、%d 个版本包" % (len(apps), len(all_packages)))
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
            compose = DEV_DIR / "1panel" / key / ver / "docker-compose.yml"
            if not compose.exists():
                error(key + "/" + ver + ": dev 下缺少 docker-compose.yml，详情页会报错")
                ok = False
            asset_name = key + "-" + ver + ".tar.gz"
            seen_assets.add(asset_name)
            pkg = DIST_DIR / asset_name
            if not pkg.exists():
                error(key + "/" + ver + ": 缺少版本包 dist/" + asset_name)
                ok = False
                continue
            prefix = key + "/" + ver + "/"
            with tarfile.open(pkg) as tf:
                bad = [m for m in tf.getnames() if not m.startswith(prefix)]
            if bad:
                error(asset_name + ": 包内顶层不是 " + prefix + "：" + repr(bad[:3]))
                ok = False
    for pkg in sorted(DIST_DIR.glob("*.tar.gz")):
        if pkg.name not in seen_assets:
            warn("dist/" + pkg.name + ": 索引未引用的孤立版本包，发布时应清理")
    print("自检通过" if ok else "自检失败")
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true",
                        help="仅校验现有 dev/ 与 dist/，不重新生成")
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

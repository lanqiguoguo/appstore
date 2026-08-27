# 自定义应用商店维护说明

本仓库基于上游 [1Panel-dev/appstore](https://github.com/1Panel-dev/appstore)（dev 分支）构建私有应用商店，供自建 1Panel 面板使用。

## 目录职责

| 路径 | 归属 | 说明 |
|---|---|---|
| `apps/` | 上游 | merge 进来的官方应用，**请勿手改**（改了会和后续同步冲突） |
| `custom/apps/<key>/` | 本仓库 | 自定义应用；同 key 时**整体替换**上游应用（如 openresty） |
| `data.yaml` | 上游 | 全局标签定义（17 个键，含 11 语言文案）；新增私有标签在此追加 |
| `tools/build.py` | 本仓库 | 生成 `dev/` 与 `stable/` 协议产物（面板实际读取的内容） |
| `dev/`, `stable/` | CI 自动生成 | 每个渠道一份：索引 zip、version.txt、各应用 logo/compose/tar.gz；索引内的绝对 URL 指向该渠道自身目录，**勿用 rsync 等方式互相镜像**（图标地址是内嵌的，镜像会让 stable 面板持续请求 dev） |

## 应用格式（与上游一致）

```
custom/apps/<key>/
├── data.yml            # additionalProperties 元数据
├── logo.png            # 必须
├── README.md           # 详情页展示
└── <版本目录>/docker-compose.yml (+ data.yml 表单、scripts、配置)
```

约束：标签 key 必须存在于 `data.yaml`（未知 key 构建直接报错）；版本目录名建议纯数字分段（如 3.6.1），`latest` 可安装但永不提示升级。

## 同步与发布（全自动）

修改 `custom/apps/**` 后 push 到 main 即可：

1. CI 自动 `merge upstream/dev` 拉取上游最新应用
2. 自动重新生成 `dev/` 与 `stable/` 并回推仓库
3. 面板约 5 分钟内出现同步红点（切换渠道后需在面板手动点一次"应用商店"同步，DB 里的下载地址才会刷新）

手动触发入口：Actions 页的 Sync Upstream & Publish AppStore → Run workflow。
本地调试：`pip install pyyaml && python3 tools/build.py`。

## 面板指向

`app_repo: https://raw.githubusercontent.com/lanqiguoguo/appstore/main`（mode 保持 dev）。
稳定渠道面板（`/opt/1panel/conf/init.yaml` 里 `mode: stable` 或稳定版安装包）无需改 app_repo：同一仓库按 `{app_repo}/stable/...` 出数据，dev/stable 各渠道索引只引用自身目录。

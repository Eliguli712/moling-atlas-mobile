# 南齐世界地图 v20

[打开 GitHub Pages](https://eliguli712.github.io/moling-atlas-mobile/) · [对应镜像](https://moling-atlas-mobile.eliguli712.chatgpt.site)

当前为 262 城总览。重排 65 城的 81 条环线；东北北魏恢复原界；默认希腊文；简化菜单首位支持球形。新增 20 城、60 条地铁规划、20 条交通走廊、东西琼州跨海桥、日本八道、海南与台湾分区、57 组 ΑΟΖ 和 29 座拜占庭机场。

详细说明见 [版本说明](docs/README_v20.md)。[数据核查](docs/revision-v20.json) 与 [线路检查](docs/ring-layout-v20.json) 随版本保存。

## 构建

```sh
python3 scripts/mirror_public.py
```

构建读取 `asset-manifest.json`，下载该版本的 45 项资料，逐项检查字节数与 SHA-256，生成 `site/` 并由 GitHub Actions 发布。相对路径支持本项目的 `/moling-atlas-mobile/` 前缀。所有地图、城市数据、离线下载内容都由 GitHub Pages 独立提供给访问者。

`tools/*v20*` 保存本次修改源码。地形重建需要用户提供的 v19 ZIP 及原有 DEM 缓存；公开网页构建只需标准 Python。`source-html/index.html.gz` 保留为原 v14 基准档案，v20 构建以版本清单为准。

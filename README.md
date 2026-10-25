# 南齐世界互动地图 v20

[打开 GitHub Pages](https://eliguli712.github.io/moling-atlas-mobile/) · [对应镜像](https://moling-atlas-mobile.eliguli712.chatgpt.site/)

65 城的 81 条环线按地形、城址与道路重排；北魏东北恢复原始轮廓与营州郡县。默认希腊文名称，简化菜单提供球形入口，刷新前合成完整清晰帧。

新增 20 城与 60 条地铁规划、20 条跨城和跨海走廊、29 座拜占庭机场。日本八道与畿内、海南台湾 13 个城域及部族分区、琼州海峡东西两桥、55 个沿海政权的 Αποκλειστική Οικονομική Ζώνη（ΑΟΖ）示意已整合。宏观政权名称与线路两端名称均可显示。

后世八道作为地理参照；新增交通、城域、部族分区和经济海域属于架空规划。完整说明和资料来源见 [docs/README_v20.md](docs/README_v20.md)。

## 部署

GitHub Actions 执行 `python scripts/mirror_public.py`，从镜像下载 `asset-manifest.json` 固定的 47 个文件，逐项核验 SHA-256；HTML 从同样通过校验的离线 ZIP 提取。旧版原始 HTML 归档保留在 `source-html/`。

世界叠图依各城保留的局部投影逆算经纬度，检查记录见 [docs/world-coordinates-v20.json](docs/world-coordinates-v20.json)。修正数据使用 `v20r2_` 文件名及独立离线缓存版本。

生成工具在 `tools/`；最终处理顺序为 `fix_global_coordinates_v20.py` → `finalize_labels_cache_v20.py` → `package_v20.py`。站内下载菜单提供完整 ZIP 和单 HTML 版。

## 渤海湾与东北接缝修订

渤海湾海域按底图海岸接触段重分，移除契丹、库莫奚的误属海域；16 处东北接缝接入相邻部族的低强度活动带。北魏恢复后的原始轮廓保持原样，海域重叠检查通过。报告见 [docs/bohai-frontier-v20.json](docs/bohai-frontier-v20.json)。主资料使用 `v20r3_d.js`，离线缓存已升级。

# 南齐世界互动地图 v21

[互动地图](https://eliguli712.github.io/moling-atlas-mobile/) · [静态矢量图册](https://eliguli712.github.io/moling-atlas-mobile/static.html) · [镜像](https://moling-atlas-mobile.eliguli712.chatgpt.site/)

本版修复静态页面，提供五幅同步矢量地图与全部 262 城交通表；静态版无需脚本。平面与城市视图按设备像素和完整视窗覆盖复用底图，文字、站点和轨道实时绘制，放大时重新生成足够清晰的底图。支持 WebGL2 的设备使用 GPU 采样地形，其他设备使用 Canvas 回退。

- 辽东西岸纵贯主线约 436 km，东麓纵贯辅线约 478 km；和龙—辽东货运联络约 262 km，卑沙—鸭绿江—平壤货运约 472 km。按保留等高线的高程、坡度及陆地通行约束布线，共享换乘与接轨点。
- 台湾保留两条地铁、四条地面电车走廊，共 41 站，站距约 1.05–1.2 km；环岛常规铁路和环岛公路闭合，东岸公路采用保守的普通公路标准。
- 海南、台湾海岸分别采用 671／406 个参考轮廓点；内部 6／7 个诸峒、诸社活动区按山脉与河谷通行代价划分，共享边界、完整覆盖陆地。
- 建康加入玄武湖／后湖，采用六朝水域概化轮廓。拜占庭机场在区域放大后显示，名称进一步放大后出现，宏观视图保持清楚。
- 保留 65 城、81 条地形环线、交州交通、海南跨海桥、日本八道与畿内、29 座拜占庭机场及 Αποκλειστική Οικονομική Ζώνη（ΑΟΖ）图层。北魏原始东北边界及渤海湾海域修订保持原样，默认希腊文标签。

直接定位：[#liaodong](https://eliguli712.github.io/moling-atlas-mobile/#liaodong)、[#taiwan](https://eliguli712.github.io/moling-atlas-mobile/#taiwan)、[#xuanwu](https://eliguli712.github.io/moling-atlas-mobile/#xuanwu)。交通和内部活动区属于架空规划；海岸与地形为概化参考，古湖岸线未作精确测绘复原。

## 校验与部署

GitHub Actions 执行 `python scripts/mirror_public.py`，从镜像下载 `asset-manifest.json` 固定的 66 个文件，核验 SHA-256。HTML 从已校验的离线 ZIP 提取，确保两站使用同一版本；历史 24K PNG／SVG 下载保留。

[更新说明与资料来源](docs/README_v21.md) · [地形与边界检查](docs/validation-v21.json) · [渲染采样记录](docs/render-validation-v21.json)

生成工具在 `tools/`。处理顺序为 `update_v21.py` → `regional_v21.py` → `patch_runtime_v21.py` → `static_v21.py` → `package_v21.py`，以保留的 v20 修订包为输入。新数据采用不可变的 `v21_` 文件名和独立离线缓存。站内下载菜单提供完整 ZIP 与单 HTML。旧版 HTML 归档保留在 `source-html/`。

镜像源版本：`917e1373050c84b52f6754d9999dc68dc09e2003`。

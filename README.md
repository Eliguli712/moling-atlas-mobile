# 南齐世界互动地图 v22

[互动地图](https://eliguli712.github.io/moling-atlas-mobile/) · [静态矢量图册](https://eliguli712.github.io/moling-atlas-mobile/static.html) · [镜像](https://moling-atlas-mobile.eliguli712.chatgpt.site/)

本版重建 22 条陆上交通廊道，替换新增干线中的长距离城际直连，沿连续铁路、公路参考资料保留河谷、山麓、沿岸与桥隧走向。线路属于 497 架空交通规划，现代参考资料不表示工程在当时存在。

- 辽东西岸主线约 461 km、东麓辅线约 640 km；辅线经太子河、凤凰谷地、鸭绿江口接入沿海铁路。和龙—辽东货运联络约 408 km，卑沙—鸭绿江—平壤货运约 528 km，岫岩—庄河山地支线约 81 km。普通铁路使用深灰轨道与枕木，9 处共同站点的坐标已核对。
- 海南沿海规划铁路约 707 km，河谷公路约 297 km，采用详细通行廊道参考。台湾环岛常规铁路约 878 km，环岛公路约 926 km；公路采用官方道路中线，保留约 4 m 几何误差范围内的转折。
- 台湾清除横向扫描条带，保留七个诸社活动区、原海岸线及完整覆盖；原有两条地铁、四条地面电车走廊的保守方案延续。
- 静态版同步提供五幅无脚本矢量地图及全部 262 城交通表，单 HTML 与完整 ZIP 同步更新。
- 北魏原始东北边界、渤海湾归属、东北部族衔接、希腊文默认名称、紧凑球形按钮、玄武湖及机场分级显示继续保留。沿用 v21 实时清晰底图和分级缓存；文字、站点、线路实时绘制。

直接定位：[#liaodong](https://eliguli712.github.io/moling-atlas-mobile/#liaodong)、[#taiwan](https://eliguli712.github.io/moling-atlas-mobile/#taiwan)、[#xuanwu](https://eliguli712.github.io/moling-atlas-mobile/#xuanwu)。

## 校验与资料

GitHub Actions 从镜像下载 asset-manifest.json 固定的 69 个文件，核验 SHA-256。HTML 从已校验的离线 ZIP 提取，两站使用同一版本。城市共用资料仍使用不可变 v21 文件，新主资料与离线缓存升级为 v22。站内下载菜单提供完整 ZIP 与单 HTML。

[更新说明](docs/README_v22.md) · [线路参考与检查](docs/corridors-v22.json) · [地理保护检查](docs/validation-v22.json) · [台湾条带修复](docs/island-bands-v22.json) · [渲染检查记录](docs/render-validation-v22.json)

选定线路几何、来源和许可保留在 tools/corridors-v22.geojson。OpenStreetMap 数据依据 ODbL 1.0；Natural Earth 为公共领域参考。台湾公路来源为[內政部國土測繪中心道路中线](https://data.gov.tw/dataset/73232)，依据政府資料開放授權條款第1版使用。[OSM 署名](https://www.openstreetmap.org/copyright)。

镜像源提交：`c377eebcdac17b11c36ef2cf1fd094d92e8dee70`。

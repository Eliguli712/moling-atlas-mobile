# 南齐世界互动地图 v23-r2

互动地图、静态矢量图册与离线包共享 `asset-manifest-v23.json` 的 SHA-256 校验清单。GitHub Pages 与镜像站发布同一份资源。

- 德文、希腊文架空世界观及初次展开的图例；希腊语为默认名称语言。
- 地形约束城市交通，地铁避开湖面，环路保留在陆地；晋安新增子城线及闽江北岸线。
- 辽东主辅铁路、跨境货运使用内地铁路样式；东北归属和缓冲区遵循指定的架空设定。
- 海南、台湾内部共享平滑边界；琼州西桥为琥珀色，东桥为蓝色。
- 每城补充现代生活设施；独立核实的历史遗址附来源，现代设施标为架空规划。
- 球面按视口排除不可见轮廓，再生成有预算的坐标缓存；切换视图保持中心和比例，球形按钮状态同步。投影切换直接显示实时绘制，减少大尺寸过渡截图占用。

`npm run build` 恢复生成资源并按清单校验到干净的 `out` 目录；`node tools/restore-generated.cjs` 可单独恢复。GitHub Pages 的 `tools/mirror_public_v23.py` 从镜像站下载校验后的资源。

静态版入口 `static.html`。更新、验证范围及资料见 `dist/README_v23.md`、`dist/validation-v23.json`、`dist/render-validation-v23.json`。云端 Chrome 验证不等同于 iPhone Safari 实机验证。现代交通、设施及疆界属于497架空世界规划。

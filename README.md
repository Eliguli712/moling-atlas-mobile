# 南齐世界互动地图 v25-r1

[打开地图](https://eliguli712.github.io/moling-atlas-mobile/) · [镜像](https://moling-atlas-mobile.eliguli712.chatgpt.site/)

- 北魏政权对象、原疆界、州郡县与边界线逐项保持 v24 原样。
- 高句丽范围含龙城（和龙）、扶余和辽东，实际控制与外围弱影响分层。广兴小框区归北魏、标为争议；保留双方重叠主张和直接接壤缓冲区。
- 德文与希腊语世界观可折叠；名称默认希腊语，图例说明线路、特别自由市与 ΑΟΖ。
- 普速铁路与内地统一；保留地形走廊、玄武湖避让、海南/台湾/晋安近期规划和两色琼州跨海大桥。
- 城市名优先，次级线路名与机场名按缩放隐藏及避让。现代设施与历史地标区分年代、依据和近似位置。
- 球面使用视口纹理网格和投影前裁剪，后台暂停解码，快速切城丢弃旧请求，缓存有上限。

`asset-manifest.json` 指定当前版本，`asset-manifest-v25.json` 保留本次 SHA-256 清单。GitHub Actions 运行 `python3 scripts/mirror_public.py`，校验全部 81 个公共文件，并从校验后的离线 ZIP 恢复原始 HTML。互动、静态与离线包和镜像使用相同资源。

更新与检查见 `dist/README_v25.md`、`dist/planning-v25.json`、`dist/validation-v25.json`、`dist/render-validation-v25.json`。修订脚本在 `tools/`；历史重建辅助脚本引用完整源仓库保留的提交，此公开镜像仓库使用上述校验下载脚本构建。

云端 Chrome、430 CSS px 手机视口及 WebGL 失效回退检查已完成；iPhone Safari 实机未验证。现代交通、设施与政治范围为 497 架空规划，未作施工可行性论证。

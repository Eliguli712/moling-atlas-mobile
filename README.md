# 南齐世界互动地图 v24-r1

[打开地图](https://eliguli712.github.io/moling-atlas-mobile/) · [镜像](https://moling-atlas-mobile.eliguli712.chatgpt.site/)

- 北魏东北外界与州郡县恢复保留的 v22 轮廓，和龙恢复北魏归属。
- 德文、希腊语世界观可折叠，首次默认收起。希腊语仍为默认名称语言。
- 海南四城、台湾六城分别按实际高程、海岸、河流与道路重做保守轨道规划；小城市优先轻轨与公交，取消模板式环线。
- 晋安新增东山—鼓山山麓线和北站接驳支线。
- 视口控制影像层级、解码并发和缓存；关闭城市或切入后台释放画布及 GPU 资源；快速切换时忽略旧请求。

`asset-manifest.json` 指定当前发布版本，`asset-manifest-v24.json` 保留本次完整 SHA-256 清单。GitHub Actions 运行 `python3 scripts/mirror_public.py`，校验全部 78 个公共文件，并从校验后的离线 ZIP 恢复原始 HTML。互动页面、静态版与离线包和镜像使用相同资源。

更新说明和逐项检查见 `dist/README_v24.md`、`dist/planning-v24.json`、`dist/validation-v24.json`、`dist/render-validation-v24.json`。修订脚本在 `tools/`，其中历史重建辅助脚本引用完整源仓库保留的提交；此镜像仓库的公开构建使用上述校验下载脚本。

云端 Chrome 与模拟手机尺寸检查已完成；iPhone Safari 实机和硬件 WebGL 尚未验证。现代设施、交通和边界属于 497 架空世界规划，未作施工可行性论证。

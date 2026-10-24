# 南齐·秣陵特别区手机互动地图

[打开互动地图](https://eliguli712.github.io/moling-atlas-mobile/)

本仓库将原站第 14 版发布为 GitHub Pages 网站，保留完整地图交互、历史版本、轨道交通、高清导出与离线下载。

构建程序根据 `asset-manifest.json` 获取并核验原站已公开的固定版本资源，更新网站入口及离线文件校验信息，再将完整静态文件发布至本站。访问已发布地图时，程序和数据均从本站加载。

在 GitHub Actions 中运行 `Publish Moling atlas` 可重新构建同一版本；如原站资源已更新，校验将阻止混用不同版本。

# 明鉴产品官网

这是一个可直接部署到GitHub Pages的静态网站，负责介绍明鉴桌面端并提供EXE下载。

## 本地预览

```powershell
npx vite website
```

## 更新下载文件

重新构建桌面端后执行：

```powershell
Copy-Item dist\MingJian.exe website\downloads\MingJian.exe -Force
Copy-Item dist\MingJian.exe.sha256.txt website\downloads\MingJian.exe.sha256.txt -Force
```

随后同步修改`index.html`中的文件大小和SHA-256显示值。

## GitHub Pages

仓库的GitHub Pages来源设置为`GitHub Actions`。推送`main`分支后，`.github/workflows/deploy-pages.yml`会把`website/`目录发布为静态网站。

当前下载按钮使用相对链接`./downloads/MingJian.exe`，因此GitHub Pages可以直接提供下载。正式发布后也可以将按钮链接切换到GitHub Releases，以减少Pages部署包体积。

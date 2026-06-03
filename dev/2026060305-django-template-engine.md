# Feature: Wire Django Template Engine into vaultpub Django Views

## Goal

让 vaultpub 的 Django integration 使用 Django 原生模板引擎（`django.shortcuts.render()`），而非 core 层的 `base_page_template()` 字符串拼接。使用户可以通过 Django 标准的模板覆盖机制（在项目 `templates/vaultpub/` 下放置同名文件）自定义页面布局。

验收标准：
- Django views 通过 `render()` 渲染模板
- `django_app/templates/vaultpub/` 下的模板文件实际被加载
- 用户在自己的 Django 项目中覆盖 `templates/vaultpub/base.html` 可以改变整体布局
- 所有现有测试通过

## Conclusion

已完成。`_render_note` 从原来的字符串拼接改为构建 context dict + `render(request, "vaultpub/page.html", context)`。现有 Django 模板文件从死代码变为实际生效的模板。

同时将 Renderer 的两个私有方法改为 public：
- `renderer._render_toc()` → `renderer.render_toc_html()`
- `renderer._render_backlinks()` → `renderer.render_backlinks_html()`

这样 Django views 可以分别获取正文、目录、反链三部分 HTML，放入模板的不同 sidebar block 中。

## Changed Files

- `src/vaultpub/core/render/renderer.py` — 重命名 `_render_toc` → `render_toc_html`, `_render_backlinks` → `render_backlinks_html`；`render_page_html` 内部调用同步更新
- `src/vaultpub/django_app/views.py` — `_render_note` 改用 `django.shortcuts.render()`；新增 `_build_nav_html` 辅助函数；导入 `build_page_title`/`build_page_description`；移除 `base_page_template` 导入
- `src/vaultpub/django_app/templates/vaultpub/page.html` — 改为使用 `seo_head` 上下文变量，添加 `article` 元素包装器
- `src/vaultpub/django_app/templates/vaultpub/base.html` — 搜索按钮改为 `{% if show_search %}` 条件渲染
- `tests/django/test_django_app.py` — 增加 Django view 真实渲染和 `vaultpub/base.html` 覆盖机制测试
- `src/vaultpub/django_app/views.py` — Django 输出的页面链接、API JSON、graph/search URL 和 redirect Location 统一套用 `url_prefix`
- `src/vaultpub/django_app/static/vaultpub/app.js` — 预构建前端脚本读取 `body[data-url-prefix]`，在 Django mount 下请求正确 API
- `frontend/src/urls.ts`、`frontend/src/search.ts`、`frontend/src/preview.ts`、`frontend/src/graph.ts`、`frontend/src/realtime.ts` — TypeScript 源码同步支持 `url_prefix`
- `README.md`、`help/guide.md` — 增加 Django 模板覆盖方法、常用 context 变量、`url_prefix` 和 include mount path 的说明

## Tests

- 81 passed
- Django 测试覆盖 `test_app_config_loads`、`test_conf_parses`、打包模板渲染、项目模板覆盖、Django mount prefix 下的页面/API/graph URL
- Lint: ruff clean
- Type check: mypy clean (0 errors)

## Manual Verification

补充验证了：

- 用户项目覆盖 `templates/vaultpub/base.html` 后，Django 页面输出会使用覆盖后的布局。
- `path("notes/", include(...))` 且 `url_prefix="/notes/"` 时，页面链接和 API 返回 URL 均带 `/notes/` 前缀。

## Known Limitations

- 静态导出 (`StaticSiteBuilder`) 仍使用 core 的 `base_page_template()`，这是正确的——静态站点不应依赖 Django 模板引擎
- 独立 ASGI 模式 (`web/routes.py`) 仍使用 `base_page_template()`，其无 Django 依赖
- Django views 传入模板的常用变量在 README 中有文档说明，但未提供自动生成的模板变量参考页
- 前端 Vite build 未在本轮执行，因为当前工作区没有 `frontend/node_modules`

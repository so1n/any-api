def get_openapi_ui_html(
    open_api_json_url: str,
    js_src_url: str = "https://cdn.jsdelivr.net/npm/openapi-ui-dist@latest/lib/openapi-ui.umd.js",
    title: str = "openAPI UI",
) -> str:
    """https://github.com/scalar/scalar/?tab=readme-ov-file#from-a-cdn"""
    return f"""
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>{title}</title>
  </head>
  <body>
    <div id="openapi-ui-container" spec-url="{open_api_json_url}" theme="light"></div>
    <script src="{js_src_url}"></script>
  </body>
</html>
"""

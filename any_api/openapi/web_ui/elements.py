def get_elements_html(
    open_api_json_url: str,
    js_src_url: str = "https://unpkg.com/@stoplight/elements/web-components.min.js",
    css_src_url: str = "https://unpkg.com/@stoplight/elements/styles.min.css",
    title: str = "ReDoc",
) -> str:
    """copy from https://github.com/stoplightio/elements"""
    return f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>{title}</title>
        <!-- Embed elements Elements via Web Component -->
        <script src="{js_src_url}"></script>
        <link rel="stylesheet" href="{css_src_url}">
      </head>
      <body>

        <elements-api
          apiDescriptionUrl="{open_api_json_url}"
          router="hash"
          layout="sidebar"
        />

      </body>
    </html>
    """

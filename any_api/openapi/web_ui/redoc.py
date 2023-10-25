def get_redoc_html(
    open_api_json_url: str,
    src_url: str = "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    title: str = "ReDoc",
) -> str:
    """copy from https://github.com/Redocly/redoc#tldr"""
    return f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>{title}</title>
        <!-- needed for adaptive design -->
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">

        <!--
        ReDoc doesn't change outer page styles
        -->
        <style>
          body {{
            margin: 0;
            padding: 0;
          }}
        </style>
      </head>
      <body>
        <redoc spec-url='{open_api_json_url}'></redoc>
        <script src={src_url}> </script>
      </body>
    </html>
    """

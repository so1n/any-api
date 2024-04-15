from typing import Optional


def get_scalar_html(
    open_api_json_url: str,
    proxy_url: Optional[str] = None,
    js_src_url: str = "https://cdn.jsdelivr.net/npm/@scalar/api-reference",
    title: str = "Scalar",
) -> str:
    """https://github.com/scalar/scalar/?tab=readme-ov-file#from-a-cdn"""
    if proxy_url:
        url_script = f"""
        <script id="api-reference" data-url="{open_api_json_url}" data-proxy-url="{proxy_url}"></script>
        """
    else:
        url_script = f"""
        <script id="api-reference" data-url="{open_api_json_url}" ></script>
        """

    return f"""
<!doctype html>
<html>
  <head>
    <title>{title}</title>
    <meta charset="utf-8" />
    <meta
      name="viewport"
      content="width=device-width, initial-scale=1" />
  </head>
  <body>
    <!-- Add your own OpenAPI/Swagger spec file URL here: -->
    <!-- Note: this includes our proxy, you can remove the following line if you do not need it -->
    <!-- data-proxy-url="https://api.scalar.com/request-proxy" -->
    {url_script}
    <!-- You can also set a full configuration object like this -->
    <!-- easier for nested objects -->
    <script>
      var configuration = {{
        theme: 'purple',
      }}

      var apiReference = document.getElementById('api-reference')
      apiReference.dataset.configuration = JSON.stringify(configuration)
    </script>
    <script src="{js_src_url}"></script>
  </body>
</html>
"""

from typing_extensions import Literal

HttpMethodLiteral = Literal["get", "post", "head", "options", "delete", "put", "trace", "patch"]
HttpParamTypeLiteral = Literal["body", "cookie", "file", "form", "header", "path", "query", "multiform"]

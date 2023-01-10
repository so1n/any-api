from typing_extensions import Literal

SecurityLiteral = Literal["apiKey", "http", "oauth2", "openIdConnect"]
SecurityHttpParamTypeLiteral = Literal["query", "header", "cookie"]
HttpMethodLiteral = Literal["get", "post", "head", "options", "delete", "put", "trace", "patch"]
HttpParamTypeLiteral = Literal["body", "cookie", "file", "form", "header", "json", "path", "query", "multiform"]

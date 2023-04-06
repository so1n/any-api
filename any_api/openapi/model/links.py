from typing import TYPE_CHECKING, List, Optional, Type

from pydantic import BaseModel

from any_api.openapi.model import openapi as openapi_model

if TYPE_CHECKING:
    from .response import BaseResponseModel


__all__ = ["LinksModel"]


class LinksModel(object):
    param_name: str
    link_name: str
    operation_id: str
    parameters_dict: dict

    def __init__(self, response_model: "Type[BaseResponseModel]", openapi_runtime_expr: str, desc: str = ""):
        """
        doc: https://swagger.io/docs/specification/links/
        :param response_model: pait response model
        :param openapi_runtime_expr: open api runtime expression syntax.
            Only support $response.headerXXX or $response.bodyXXX
            Please refer to the section of the document at `Runtime Expression Syntax`
        :param desc: links desc
        """
        self.openapi_runtime_expr: str = openapi_runtime_expr
        self.response_model: "Type[BaseResponseModel]" = response_model
        self.desc: str = desc
        self._check_openapi_runtime_expr()

    def _check_openapi_runtime_expr(self) -> None:
        if self.openapi_runtime_expr.startswith("$response.header."):
            header_key: str = self.openapi_runtime_expr.replace("$response.header.", "")
            if header_key not in (self.response_model.header or {}):
                raise KeyError(f"Can not found header key:{header_key} from {self.response_model}")
        elif self.openapi_runtime_expr.startswith("$response.body#"):
            if not self.response_model.is_base_model_response_data():
                raise RuntimeError(
                    f"Expr: {self.openapi_runtime_expr} only support "
                    f"response_model.response_data type is pydantic.Basemodel"
                )
            try:
                key_list: List[str] = [
                    i for i in self.openapi_runtime_expr.replace("$response.body#", "").split("/") if i
                ]
            except Exception:
                raise RuntimeError(
                    f"Check expr: {self.openapi_runtime_expr} error."
                    "Please refer to the section of the document(https://swagger.io/docs/specification/links/) "
                    "at `Runtime Expression Syntax`"
                )  # pragma: no cover

            base_model: Type[BaseModel] = self.response_model.response_data  # type: ignore
            for key in key_list:
                if key not in base_model.__fields__:
                    raise ValueError(
                        f"check expr:{self.openapi_runtime_expr} error "  # type: ignore
                        f"from {self.response_model.response_data}"  # type: ignore
                    )
                temp_type: Type = base_model.__fields__[key].type_
                if issubclass(temp_type, BaseModel):
                    base_model = temp_type
        else:
            raise ValueError(
                "Only support $response.headerXXX or $response.bodyXXX. "
                "Please refer to the section of the document(https://swagger.io/docs/specification/links/) "
                "at `Runtime Expression Syntax`"
            )

    def register(self, *, param_name: str, http_param_type_name: str, operation_id: str) -> None:
        global_key: str = f"{operation_id}/{http_param_type_name}/{param_name}"
        parameter_dict: Optional[dict] = None
        request_body: Optional[str] = None
        if http_param_type_name in ("body", "form", "multiform"):
            request_body = self.openapi_runtime_expr
        else:
            parameter_dict = {param_name: self.openapi_runtime_expr}
        self.response_model.register_link_schema(
            {
                global_key: openapi_model.LinkModel(
                    description=self.desc,
                    operationId=operation_id,
                    parameters=parameter_dict,
                    requestBody=request_body,
                )
            }
        )

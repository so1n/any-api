from typing import Dict, List, Optional

import any_api.openapi.model.openapi
import any_api.openapi.model.openapi.basic
import any_api.openapi.model.openapi.metadata
from any_api.asyncapi.model import asyncapi_model, operation_model
from any_api.base_api.base_api import BaseAPI
from any_api.util.util import get_key_from_template

__all__ = ["AsyncAPI"]


class AsyncAPI(BaseAPI[asyncapi_model.AsyncAPIModel]):
    def __init__(
        self,
        async_api_id: str,
        asyncapi_info_model: Optional[any_api.openapi.model.openapi.metadata.InfoModel] = None,
        server_model_dict: Optional[Dict[str, asyncapi_model.ServerModel]] = None,
        tag_model_list: Optional[List[any_api.openapi.model.openapi.TagModel]] = None,
        external_docs: Optional[any_api.openapi.model.openapi.basic.ExternalDocumentationModel] = None,
    ):
        self._add_tag_dict: dict = {}

        self._api_model: asyncapi_model.AsyncAPIModel = asyncapi_model.AsyncAPIModel(id=async_api_id)
        if asyncapi_info_model:
            self._api_model.info = asyncapi_info_model
        if server_model_dict:
            self._api_model.servers = server_model_dict
        if external_docs:
            self._api_model.external_docs = external_docs
        if tag_model_list:
            for tag_model in tag_model_list:
                self._add_tag(tag_model)

    @classmethod
    def build(
        cls,
        async_api_id: str,
        asyncapi_info_model: Optional[any_api.openapi.model.openapi.metadata.InfoModel] = None,
        server_model_dict: Optional[Dict[str, asyncapi_model.ServerModel]] = None,
        tag_model_list: Optional[List[any_api.openapi.model.openapi.TagModel]] = None,
        external_docs: Optional[any_api.openapi.model.openapi.basic.ExternalDocumentationModel] = None,
    ) -> "AsyncAPI":
        return cls(
            async_api_id=async_api_id,
            asyncapi_info_model=asyncapi_info_model,
            server_model_dict=server_model_dict,
            tag_model_list=tag_model_list,
            external_docs=external_docs,
        )

    def _publish_handle(self, publish_model: operation_model.OperationModel) -> dict:
        publish_dict: dict = publish_model.dict(exclude={"message"})
        # publish_dict["message"] = self._schema_handle()
        return publish_dict

    def _subscribe_handle(self, subscribe_model: operation_model.OperationModel) -> dict:
        subscribe_dict: dict = subscribe_model.dict(exclude={"message"})
        return subscribe_dict

    def add_channel_model(self, channel_model: operation_model.ChannelItemModel) -> "AsyncAPI":
        for key in get_key_from_template(channel_model.name):
            if not channel_model.parameters:
                continue
            if key not in channel_model.parameters.__fields_set__:
                raise ValueError(f"The template name {key} for channel name cannot be found in `parameters`")
        for server in channel_model.servers:
            if server not in self._api_model.servers:
                raise ValueError(f"Unable to find {server} in servers")
        channel_dict: dict = self._api_model.channel.setdefault(channel_model.name, {})

        if channel_model.parameters:
            channel_dict["parameters"] = {}
            for param_name, schema in channel_model.parameters.schema()["properties"]:
                channel_dict["parameters"][param_name] = schema
        channel_dict["description"] = channel_model.description
        channel_dict["servers"] = channel_model.servers
        channel_dict["bindings"] = channel_model.bindings
        if channel_model.publish:
            channel_dict["publish"] = self._publish_handle(channel_model.publish)
        if channel_model.subscribe:
            channel_dict["subscribe"] = self._subscribe_handle(channel_model.subscribe)
        return self

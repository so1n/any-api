from typing import Any

import pytest
from pydantic import BaseModel, Field

from any_api.util import i18n, pydantic_adapter
from any_api.util.util import get_key_from_template


class TestUtil:
    def test_get_key_from_template(self) -> None:
        assert get_key_from_template("{a} | {b} | {c} | {{d}}") == ["a", "b", "c"]


class TestI18n:
    def test_context(self) -> None:
        with i18n.I18nContext("zh-cn"):
            assert i18n.I18n.Name == "名称"
        with i18n.I18nContext("en"):
            assert i18n.I18n.Name == "Name"

    def test_check_i18n_lang(self) -> None:
        i18n.check_i18n_lang("en")
        i18n.check_i18n_lang("zh-cn")
        i18n.check_i18n_lang("customer_a")
        with pytest.raises(ValueError):
            i18n.check_i18n_lang("a")

    def test_join_i18n(self) -> None:
        with i18n.I18nContext("zh-cn"):
            assert i18n.join_i18n([i18n.I18n.Group, i18n.I18n.Name]) == "组名称"
        with i18n.I18nContext("en"):
            assert i18n.join_i18n([i18n.I18n.Group, i18n.I18n.Name]) == "Group Name"


class Demo(BaseModel):
    class SubDemo(BaseModel):
        sub_a: int = Field()

    a: int = Field(alias="aa", example=1)
    b: int = Field(alias="bb", example=2)
    sub_a: SubDemo = Field()

    @pydantic_adapter.field_validator("a")
    def check_value(cls, value: Any) -> Any:
        return value

    @pydantic_adapter.model_validator(mode="before")
    def before_check_model(cls, value: Any) -> Any:
        return value

    @pydantic_adapter.model_validator(mode="after")
    def after_check_model(cls, value: Any) -> Any:
        return value


class TestPydanticAdapter:
    def test_get_model_definitions(self) -> None:
        pass

    def test_model_fields(self) -> None:
        assert list(pydantic_adapter.model_fields(Demo).keys()) == ["a", "b", "sub_a"]

    def test_get_field_info(self) -> None:
        assert pydantic_adapter.model_fields(Demo)["a"].alias == "aa"
        assert pydantic_adapter.model_fields(Demo)["b"].alias == "bb"

    def test_field_validator(self) -> None:
        if pydantic_adapter.is_v1:
            assert Demo.__validators__["a"][0].func.__name__ == "check_value"
        else:
            assert Demo.__pydantic_decorators__.field_validators["check_value"].func.__name__ == "check_value"

    def test_model_json_schema(self) -> None:
        assert len(pydantic_adapter.model_json_schema(Demo)["$defs"]) == 1
        assert len(pydantic_adapter.model_json_schema(Demo, "definitions")["definitions"]) == 1

    def test_model_dump(self) -> None:
        assert pydantic_adapter.model_dump(Demo(aa=1, bb=2, sub_a=Demo.SubDemo(sub_a=1))) == {
            "a": 1,
            "b": 2,
            "sub_a": {"sub_a": 1},
        }

    def test_model_validator(self) -> None:
        if pydantic_adapter.is_v1:
            assert len(Demo.__pre_root_validators__) == 1
            assert Demo.__pre_root_validators__.__name__ == "before_check_model"

            assert len(Demo.__post_root_validators__) == 1
            assert Demo.__post_root_validators__.__name__ == "after_check_model"
        else:
            assert Demo.__pydantic_decorators__.model_validators["before_check_model"].info.mode == "before"
            assert Demo.__pydantic_decorators__.model_validators["after_check_model"].info.mode == "after"

    def test_get_extra_by_field_info(self) -> None:
        assert (
            1
            == pydantic_adapter.get_extra_by_field_info(  # type: ignore[index]
                pydantic_adapter.model_fields(Demo)["a"]
            )["example"]
        )
        assert (
            2
            == pydantic_adapter.get_extra_by_field_info(  # type: ignore[index]
                pydantic_adapter.model_fields(Demo)["b"]
            )["example"]
        )

    def test_get_extra_dict_by_field_info(self) -> None:
        assert 1 == pydantic_adapter.get_extra_dict_by_field_info(pydantic_adapter.model_fields(Demo)["a"])["example"]
        assert 2 == pydantic_adapter.get_extra_dict_by_field_info(pydantic_adapter.model_fields(Demo)["b"])["example"]

        if pydantic_adapter.is_v1:
            return

        class CallbackExtraDemo(BaseModel):
            a: int = Field(json_schema_extra=lambda x: x.update(example=1))

        assert (
            1
            == pydantic_adapter.get_extra_dict_by_field_info(pydantic_adapter.model_fields(CallbackExtraDemo)["a"])[
                "example"
            ]
        )

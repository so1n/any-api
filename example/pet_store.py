from enum import Enum
from typing import Dict, List, Type

from pydantic import BaseModel, Field

from any_api.openapi.openapi import OpenAPI, openapi_model, request_model, response_model
from any_api.util.by_pydantic import create_pydantic_model

#######
# tag #
#######
pet_tag: openapi_model.TagModel = openapi_model.TagModel(
    name="pet",
    description="Everything about your Pets",
    externalDocs=openapi_model.ExternalDocumentationModel(description="Find out more", url="http://swagger.io"),
)
store_tag: openapi_model.TagModel = openapi_model.TagModel(
    name="store",
    description="Access to Petstore orders",
    externalDocs=openapi_model.ExternalDocumentationModel(
        description="Find out more about our store", url="http://swagger.io"
    ),
)
user_tag: openapi_model.TagModel = openapi_model.TagModel(
    name="user",
    description="Operations about user",
)


#########
# model #
#########
class Status(str, Enum):
    placed = "placed"
    approved = "approved"
    delivered = "delivered"


class OrderModel(BaseModel):
    id_: int = Field(None, alias="id", example=10, format="int64")
    pet_id: int = Field(None, alias="petId", example=198772, format="int64")
    quantity: int = Field(None, example=7, format="int32")
    shipDate: str = Field(None, format="date-time")
    status: Status = Field(None, description="Order Status", exclude=Status.approved)
    complete: bool = Field(
        None,
    )


class Address(BaseModel):
    street: str = Field(None, example="437 Lytton")
    city: str = Field(None, example="Palo Alto")
    state: str = Field(None, example="CA")
    zip: str = Field(None, example="94301")


class Customer(BaseModel):
    id_: int = Field(None, alias="id", example=100000, format="int64")
    username: str = Field(None, example="fehguy")
    address: List[Address]


class Category(BaseModel):
    id_: int = Field(None, alias="id", example=1, format="int64")
    name: str = Field(None, example="Dogs")


class User(BaseModel):
    id_: int = Field(None, alias="id", example=10, format="int64")
    username: str = Field(None, example="theUser")
    first_name: str = Field(None, alias="firstName", example="John")
    last_name: str = Field(None, alias="lastName", example="James")
    email: str = Field(None, example="john@email.com")
    password: str = Field(None, example="12345")
    phone: str = Field(None, example="12345")
    user_status: int = Field(None, alias="userStatus", description="User Status", example=1, format="int32")


class Tag(BaseModel):
    id_: int = Field(None, alias="id", format="int64")
    name: str = Field(
        None,
    )


class Pet(BaseModel):
    id_: int = Field(None, alias="id", example=10, format="int64")
    name: str = Field(example="Dogs")
    category: Category
    photo_urls: List[str] = Field(alias="photoUrls")
    tags: List[Tag]
    status: Status = Field(description="pet status in the store")


class ApiResponse(BaseModel):
    code: int = Field(None, format="int32")
    type_: str = Field(None, alias="type")
    message: str = Field(
        None,
    )


############
# response #
############
class PetSuccessfulJsonResponse(response_model.JsonResponseModel):
    description = "Successful operation"
    response_data = Pet


class PetSuccessfulXmlResponse(response_model.XmlResponseModel):
    description = "Successful operation"
    response_data = Pet


class SuccessfulOperationAndSchemaJsonResponse(PetSuccessfulJsonResponse):
    openapi_schema = {"type": "object", "additionalProperties": {"type": "integer", "format": "int32"}}


class UserSuccessfulJsonResponse(response_model.JsonResponseModel):
    description = "Successful operation"
    response_data = User


class UserSuccessfulXmlResponse(response_model.XmlResponseModel):
    description = "Successful operation"
    response_data = User


class MyJsonResponse(response_model.BaseResponseModel):
    class HeaderModel(BaseModel):
        rate_limit: int = Field(
            default=None, alias="X-rate-Limit", description="calls per hour allowed by the user", format="int32"
        )
        expires_after: str = Field(
            default=None, alias="X-Expires-After", description="date in UTC when token expires", format="date-time"
        )

    response_data: str = "example data"
    media_type: str = "application/json"
    header: BaseModel = HeaderModel


class MyXmlResponse(MyJsonResponse):
    media_type: str = "application/xml"


def create_response_type(description: str, status_code: int) -> Type[request_model.BaseResponseModel]:
    return type(  # type: ignore
        description, (request_model.BaseResponseModel,), {"description": description, "status_code": (status_code,)}
    )


############
# security #
############
petstore_auth = openapi_model.Oauth2SecurityModel(
    flows=openapi_model.OAuthFlowsModel(
        implicit=openapi_model.OAuthFlowModel(
            authorizationUrl="https://petstore3.swagger.io/oauth/authorize",
            scopes={"write:pets": "modify pets in your account", "read:pets": "read your pets"},
        )
    )
)
api_key_auth = openapi_model.ApiKeySecurityModel(name="api_key", in_stub="header")
petstore_auth_dict: Dict[str, openapi_model.SecurityModelType] = {"petstore_auth": petstore_auth}
petstore_include_api_key_auth_dict: Dict[str, openapi_model.SecurityModelType] = {
    "api_key": api_key_auth,
    "petstore_auth": petstore_auth,
}


if __name__ == "__main__":
    # copy from https://petstore3.swagger.io/api/v3/openapi.json

    pet_store_openapi: OpenAPI = OpenAPI(
        openapi_info_model=openapi_model.InfoModel(
            title="Swagger Petstore - OpenAPI 3.0",
            description=(
                "This is a sample server Petstore server.  "
                "You can find out more about Swagger at [http://swagger.io](http://swagger.io) or on"
                " [irc.freenode.net, #swagger](http://swagger.io/irc/).  "
                "For this sample, you can use the api key `special-key` to test the authorization filters."
            ),
            termsOfService="http://swagger.io/terms/",
            contact=openapi_model.Contact(email="apiteam@swagger.io"),
            license=openapi_model.License(name="Apache 2.0", url="http://www.apache.org/licenses/LICENSE-2.0.html"),
            version="1.0.17",
        ),
        tag_model_list=[pet_tag, store_tag, user_tag],
        external_docs=openapi_model.ExternalDocumentationModel(
            description="Find out more about Swagger", url="http://swagger.io"
        ),
        server_model_list=[openapi_model.ServerModel(url="/api/v3")],
    )
    pet_store_openapi.add_api_model(
        request_model.ApiModel(
            path="/pet",
            http_method_list=["put"],
            tags=[pet_tag],
            summary="Update an existing pet",
            description="Update an existing pet by Id",
            operation_id="updatePet",
            request_dict={
                "body": [
                    request_model.RequestModel(
                        required=True,
                        description="Update an existent pet in the store",
                        media_type_list=["application/json", "application/xml"],
                        model=Pet,
                    ),
                ],
                "form": [request_model.RequestModel(media_type_list=["application/x-www-form-urlencoded"], model=Pet)],
            },
            response_list=[
                PetSuccessfulJsonResponse,
                PetSuccessfulXmlResponse,
                create_response_type("Invalid ID supplied", 400),
                create_response_type("Pet not found", 404),
                create_response_type("Validation exception", 405),
            ],
            security=petstore_auth_dict,
        )
    )
    pet_store_openapi.add_api_model(
        request_model.ApiModel(
            path="/pet",
            http_method_list=["post"],
            tags=[pet_tag],
            summary="Add a new pet to rhe store",
            description="Add a new pet to rhe store",
            operation_id="addPet",
            request_dict={
                "body": [
                    request_model.RequestModel(media_type_list=["application/json", "application/xml"], model=Pet),
                ],
                "form": [request_model.RequestModel(media_type_list=["application/x-www-form-urlencoded"], model=Pet)],
            },
            response_list=[
                PetSuccessfulJsonResponse,
                PetSuccessfulXmlResponse,
                create_response_type("Invalid input", 405),
            ],
            security=petstore_auth_dict,
        )
    )
    pet_store_openapi.add_api_model(
        request_model.ApiModel(
            path="/pet/findByStatus",
            http_method_list=["get"],
            tags=[pet_tag],
            summary="Finds Pets by status",
            description="Multiple status values can be provided with comma separated strings",
            operation_id="findPetsByStatus",
            request_dict={
                "query": [
                    request_model.RequestModel(
                        model=create_pydantic_model(
                            {
                                "name": (
                                    Status,
                                    Field(
                                        default="available",
                                        description="Status values that need to be considered for filter",
                                        explode=True,
                                    ),
                                )
                            }
                        )
                    )
                ]
            },
            response_list=[
                PetSuccessfulJsonResponse,
                PetSuccessfulXmlResponse,
                create_response_type("Invalid status value", 400),
            ],
            security=petstore_auth_dict,
        )
    )
    pet_store_openapi.add_api_model(
        request_model.ApiModel(
            path="/pet/findByTags",
            http_method_list=["get"],
            tags=[pet_tag],
            summary="Finds Pets by tags",
            description="Multiple tags can be provided with comma separated strings. Use tag1, tag2, tag3 for testing.",
            operation_id="findPetsByTags",
            request_dict={
                "query": [
                    request_model.RequestModel(
                        model=create_pydantic_model(
                            {
                                "tags": (
                                    List[str],
                                    Field(None, description="Tags to filter by", explode=True),
                                )
                            }
                        )
                    )
                ]
            },
            response_list=[
                PetSuccessfulJsonResponse,
                PetSuccessfulXmlResponse,
                create_response_type("Invalid tag value", 400),
            ],
            security=petstore_auth_dict,
        )
    )
    pet_store_openapi.add_api_model(
        request_model.ApiModel(
            path="/pet/{petId}",
            http_method_list=["get"],
            summary="Find pet by ID",
            description="Returns a single pet",
            operation_id="getPetById",
            request_dict={
                "path": [
                    request_model.RequestModel(
                        model=create_pydantic_model(
                            {
                                "petId": (
                                    int,
                                    Field(description="Id of pet to return", format="int64"),
                                )
                            }
                        )
                    )
                ]
            },
            response_list=[
                PetSuccessfulJsonResponse,
                PetSuccessfulXmlResponse,
                create_response_type("Invalid Id supplied", 400),
                create_response_type("Pet not found", 400),
            ],
            security=petstore_include_api_key_auth_dict,
        )
    )
    pet_store_openapi.add_api_model(
        request_model.ApiModel(
            path="/pet/{petId}",
            http_method_list=["delete"],
            operation_id="deletePet",
            summary="Deletes a pet",
            request_dict={
                "path": [
                    request_model.RequestModel(
                        model=create_pydantic_model(
                            {"petId": (int, Field(description="Pet id to delete", format="int64"))}
                        )
                    )
                ],
                "header": [request_model.RequestModel(model=create_pydantic_model({"api_key": (str, Field())}))],
            },
            response_list=[
                PetSuccessfulJsonResponse,
                PetSuccessfulXmlResponse,
                create_response_type("Invalid input", 405),
            ],
            security=petstore_auth_dict,
        )
    )
    pet_store_openapi.add_api_model(
        request_model.ApiModel(
            path="/pet/{petId}/uploadImage",
            http_method_list=["post"],
            summary="uploads an image",
            operation_id="uploadId",
            request_dict={
                "path": [
                    request_model.RequestModel(
                        model=create_pydantic_model(
                            {
                                "petId": (
                                    int,
                                    Field(description="Id of pet to update", format="int64"),
                                )
                            }
                        )
                    )
                ],
                "query": [
                    request_model.RequestModel(
                        model=create_pydantic_model(
                            {"additionalMetadata": (str, Field(description="Additional Metadata"))}
                        )
                    )
                ]
                # TODO body?
            },
            response_list=[PetSuccessfulJsonResponse],
            security=petstore_auth_dict,
        )
    )
    pet_store_openapi.add_api_model(
        request_model.ApiModel(
            path="/store/inventory",
            tags=[store_tag],
            http_method_list=["get"],
            summary="Returns pet inventories by status",
            description="Returns a map of status codes to quantities",
            operation_id="getInventory",
            response_list=[SuccessfulOperationAndSchemaJsonResponse],
            security=petstore_include_api_key_auth_dict,
        )
    )
    pet_store_openapi.add_api_model(
        request_model.ApiModel(
            path="/store/order",
            http_method_list=["post"],
            tags=[store_tag],
            summary="Place an order for a pet",
            description="Place a new order in the store",
            operation_id="placeOrder",
            request_dict={
                "body": [
                    request_model.RequestModel(media_type_list=["application/json", "application/xml"], model=Pet)
                ],
                "form": [request_model.RequestModel(media_type_list=["application/x-www-form-urlencoded"], model=Pet)],
            },
            response_list=[SuccessfulOperationAndSchemaJsonResponse, create_response_type("Invalid input", 405)],
        )
    )
    pet_store_openapi.add_api_model(
        request_model.ApiModel(
            path="/store/order/{orderId}",
            http_method_list=["get"],
            tags=[store_tag],
            summary="Find purchase order by ID",
            description=(
                "For valid response try integer IDs with value <= 5 or > 10. Other values will generate exceptions."
            ),
            operation_id="getOrderById",
            request_dict={
                "path": [
                    request_model.RequestModel(
                        model=create_pydantic_model(
                            {
                                "orderId": (
                                    str,
                                    Field(description="ID of order that needs to be fetched", format="int64"),
                                )
                            }
                        )
                    )
                ]
            },
            response_list=[
                PetSuccessfulJsonResponse,
                PetSuccessfulXmlResponse,
                create_response_type("Invalid ID supplied", 400),
                create_response_type("Order not found", 404),
            ],
        )
    )
    pet_store_openapi.add_api_model(
        request_model.ApiModel(
            path="/store/order/{orderId}",
            http_method_list=["delete"],
            tags=[store_tag],
            summary="Delete purchase order by ID",
            description=(
                "For valid response try integer IDs with value < 1000. Anything above 1000 or nonintegers will"
                " generate API errors"
            ),
            operation_id="deleteOrder",
            request_dict={
                "path": [
                    request_model.RequestModel(
                        model=create_pydantic_model(
                            {
                                "orderId": (
                                    str,
                                    Field(description="Id of the order that needs to be deleted", format="int64"),
                                )
                            }
                        )
                    )
                ]
            },
            response_list=[
                create_response_type("Invalid ID supplied", 400),
                create_response_type("Order not found", 404),
            ],
        )
    )
    pet_store_openapi.add_api_model(
        request_model.ApiModel(
            path="/user",
            http_method_list=["post"],
            tags=[user_tag],
            summary="Create user",
            description="This can only be done by the logged in user.",
            operation_id="createUser",
            request_dict={
                "body": [
                    request_model.RequestModel(media_type_list=["application/json", "application/xml"], model=User)
                ],
                "form": [request_model.RequestModel(media_type_list=["application/x-www-form-urlencoded"], model=User)],
            },
            response_list=[
                PetSuccessfulJsonResponse,
                UserSuccessfulJsonResponse,
                UserSuccessfulXmlResponse,
            ],
        )
    )
    pet_store_openapi.add_api_model(
        request_model.ApiModel(
            path="/user/createWithList",
            http_method_list=["post"],
            tags=[user_tag],
            summary="Creates list of users with given input array",
            description="Creates list of users with given input array",
            operation_id="createUsersWithListInput",
            request_dict={"body": [request_model.RequestModel(media_type_list=["application/json"], model=(User,))]},
            response_list=[
                UserSuccessfulXmlResponse,
                UserSuccessfulJsonResponse,
            ],
        )
    )
    pet_store_openapi.add_api_model(
        request_model.ApiModel(
            path="/user/login",
            http_method_list=["get"],
            tags=[user_tag],
            summary="Logs user into the system",
            operation_id="loginUser",
            request_dict={
                "query": [
                    request_model.RequestModel(
                        model=create_pydantic_model(
                            {
                                "username": (str, Field(None, description="The user name for login")),
                                "password": (str, Field(None, description="The password for login in clear text")),
                            },
                        )
                    )
                ]
            },
            response_list=[
                MyJsonResponse,
                MyXmlResponse,
                create_response_type(description="Invalid username/password supplied", status_code=400),
            ],
        )
    )
    pet_store_openapi.add_api_model(
        request_model.ApiModel(
            path="/user/logout",
            http_method_list=["get"],
            tags=[user_tag],
            summary="Logs out current logged in user session",
            operation_id="logoutUser",
            response_list=[
                # TODO default response
            ],
        )
    )
    pet_store_openapi.add_api_model(
        request_model.ApiModel(
            path="/user/{username}",
            http_method_list=["get"],
            summary="Get user by user name",
            operation_id="getUserByName",
            request_dict={
                "path": [
                    request_model.RequestModel(
                        model=create_pydantic_model(
                            {
                                "username": (
                                    str,
                                    Field(description="The name that needs to be fetched. Use user1 for testing. "),
                                )
                            }
                        )
                    )
                ]
            },
            response_list=[
                UserSuccessfulJsonResponse,
                UserSuccessfulXmlResponse,
                create_response_type("Invalid username supplied", 400),
                create_response_type("User not found", 404),
            ],
        )
    )
    pet_store_openapi.add_api_model(
        request_model.ApiModel(
            path="/user/{username}",
            tags=[user_tag],
            http_method_list=["put"],
            summary="Update user",
            description="This can only be done by the logged in user.",
            operation_id="updateUser",
            request_dict={
                "path": [
                    request_model.RequestModel(
                        model=create_pydantic_model(
                            {"username": (str, Field(description="name that need to be deleted"))}
                        )
                    )
                ],
                "body": [
                    request_model.RequestModel(media_type_list=["application/json", "application/xml"], model=User)
                ],
                "form": [request_model.RequestModel(media_type_list=["application/x-www-form=urlencoded"], model=User)],
            },
            response_list=[
                # TODO default response
            ],
        )
    )
    pet_store_openapi.add_api_model(
        request_model.ApiModel(
            path="/user/{username}",
            http_method_list=["delete"],
            summary="Delete user",
            description="This can only be done by the logged in user.",
            operation_id="deleteUser",
            request_dict={
                "path": [
                    request_model.RequestModel(
                        model=create_pydantic_model(
                            {"username": (str, Field(description="name that need to be deleted"))}
                        )
                    )
                ],
            },
            response_list=[
                create_response_type("Invalid username supplied", 400),
                create_response_type("User not found", 404),
            ],
        )
    )
    print(pet_store_openapi.content())
    # from any_api.openapi.to.markdown import Markdown
    #
    # print(Markdown(pet_store_openapi).content)

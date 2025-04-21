import models
from controllers.base_controller import AicaciaPublicAPI
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter

my_router = InferringRouter()


@cbv(my_router)
class MyNewController(AicaciaPublicAPI):
    @my_router.get("/")
    def get(self) -> str:
        return f"Hello, World!"

from controllers.hello_world_controller import HelloworldController
from fastapi import FastAPI
from fastapi_utils import Api


def create_app():
    app = FastAPI()
    api = Api(app)

    hello_world_controller = HelloworldController()
    api.add_resource(hello_world_controller, "/hello")

    return app


app = create_app()

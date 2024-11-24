import ast
import json
import uuid

import models
from controllers.base_controller import AicaciaProtectedAPI
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from library.ai_summary_utils import generate_summary
from library.vectordb_utils import (
    create_embedding_class,
    create_vectordb_client,
    load_config,
)
from pydantic import BaseModel

user_query_router = InferringRouter()
config = load_config('/config.yaml')
client = create_vectordb_client(config)
embed_model = create_embedding_class(config)


class UserQueryPostRequest(BaseModel):
    question: str


class UserQueryPostResponse(BaseModel):
    query_id: str
    references: list[models.Reference]
    summary: str


@cbv(user_query_router)
class UserQueryController(AicaciaProtectedAPI):

    @user_query_router.post("/")
    def post(self, request: UserQueryPostRequest) -> UserQueryPostResponse:
        query_id = str(uuid.uuid4())

        # Embed query
        query_embedding = embed_model.get_text_embedding(request.question)

        # Search in vector store
        results = client.query_points(
            collection_name=config['vectordb']['collection'],
            query=query_embedding,
            limit=3,
        )

        references = []
        rag_context = []
        for res in results.points:
            sources = ast.literal_eval(res.payload['sources'].split(';{')[0])

            if res.payload["title"] in [ref["title"] for ref in references]:
                rag_context.append(
                    {
                        "title": res.payload["title"],
                        "url": sources["link"],
                        "text": json.loads(res.payload["_node_content"])["text"],
                    }
                )
                print(f"Skipping duplicate reference: {res.payload['title']}")
                continue

            references.append(
                models.Reference(
                    title=res.payload["title"],
                    url=sources["link"],
                    description=res.payload["_node_content"].split('"text":')[-1][:1000]
                    + "...",
                ).model_dump()
            )

        print(f"RAG Context: {json.dumps(rag_context, indent=2)}")

        summary = generate_summary(request.question, json.dumps(rag_context))

        query = models.Query(
            query_id=query_id,
            question=request.question,
            references=references,
            summary=summary,
            user_id=self.user.user_id,
        )

        session = self.get_db_session()
        session.add(query)
        session.commit()

        return UserQueryPostResponse(
            query_id=query_id,
            references=query.references,
            summary=query.summary,
        )

import os
import logging
from typing import Optional

from r2r.core import (
    LLMProvider,
    LoggingDatabaseConnection,
    PromptProvider,
    VectorDBProvider,
    log_execution_to_db,
)
from r2r.embeddings import OpenAIEmbeddingProvider
from r2r.integrations import SerperClient
# from r2r.integrations.ionic import IonicClient # TODO update __init__.py
from r2r.pipelines import BasicPromptProvider

from r2r.pipelines.basic.rag import BasicRAGPipeline

from ionic import Ionic as IonicSDK
from ionic.models.components import QueryAPIRequest
from ionic.models.components import Query as SDKQuery
from ionic.models.operations import QueryResponse, QuerySecurity

class IonicClient:
    def __init__(self, api_key: str = os.getenv("IONIC_API_KEY")) -> None:
        if not api_key:
            raise ValueError(
                "Please set the `IONIC_API_KEY` env var or pass a parameter to use `IonicCLient`."
            )
        
        self.client = IonicSDK(api_key_header=api_key)

    def search(
        self,
        query: str,
        num_results: Optional[int] = 10,
    ):
        request = QueryAPIRequest(
            query=SDKQuery(
                query=query,
                num_results=num_results
            )
        )
        response: QueryResponse = self.client.query(
            request=request,
            security=QuerySecurity(),
        )

        products = [
            product
            for result in response.query_api_response.results
            for product in result.products
        ]

        return products
    
 


logger = logging.getLogger(__name__)

class IonicProductPipeline(BasicRAGPipeline):
    def __init__(
        self,
        llm: LLMProvider,
        db: VectorDBProvider,
        embedding_model: str,
        embeddings_provider: OpenAIEmbeddingProvider,
        logging_connection: Optional[LoggingDatabaseConnection] = None,
        prompt_provider: Optional[PromptProvider] = BasicPromptProvider(),
    ) -> None:
        logger.debug(f"Initalizing `IonicRagPipeline`.")
        super().__init__(
            llm=llm,
            logging_connection=logging_connection,
            db=db,
            embedding_model=embedding_model,
            embeddings_provider=embeddings_provider,
            prompt_provider=prompt_provider,
        )
        self.ionic_client = IonicClient("whatever_api_key_here")

    def transform_query(self, query: str) -> str:
        return query

    @log_execution_to_db
    def search(
        self,
        transformed_query: str,
        filters: dict,
        limit: int,
        *args,
        **kwargs,
    ) -> list:
        results = []
        local_results = super().search(transformed_query, filters, limit)

        results.extend(
            [{"type": "local", "result": ele} for ele in local_results]
        )

        ionic_results = self.ionic_client.search(transformed_query, limit)

        formatted_results = self._format_ionic_results(ionic_results)
        
        results.extend(
            [{"type": "external", "result": ele} for ele in formatted_results]
        )

        return results

    def construct_context(self, results: list) -> str:
        local_context = super().construct_context(
            [ele["result"] for ele in results if ele["type"] == "local"]
        )

        web_context = self._construct_ionic_context(
            [ele["result"] for ele in results if ele["type"] == "external"]
        )
        return local_context + "\n\n" + web_context
    
    # TODO move to client
    def _format_ionic_results(self, products: list) -> list:
        formatted_results = []
        for product in products:
            print(product)
            # TODO
            product_dict = {
                "name": product.name,
                "price": product.price,
                "brand_name": product.brand_name,
                "upc": product.upc,
                "merchant_name": product.merchant_name,
                "thumbnail": product.thumbnail,
                "link": product.links[0].url,
            }
            product_dict["type"] = "answer_box"
            formatted_results.append(product_dict)

        return formatted_results

    # TODO move to client
    def _construct_ionic_context(self, products: list) -> str:
        organized_results = {}

        for product in products:
            result_type = product.pop(
                "type", "Unknown"
            )  # Pop the type and use as key

            if result_type not in organized_results:
                organized_results[result_type] = [product]
            else:
                organized_results[result_type].append(product)

        print(organized_results)
        context = ""
        # Iterate over each result type
        for result_type, items in organized_results.items():
            context += f"# {result_type} Results:\n"
            for index, item in enumerate(items, start=1):
                # Process each item under the current type
                context += f"Item {index}:\n"
                context += process_json(item) + "\n"

        return context

########################################################################################

def process_json(json_object, indent=0):
    """
    Recursively traverses the JSON object (dicts and lists) to create an unstructured text blob.
    """
    text_blob = ""
    if isinstance(json_object, dict):
        for key, value in json_object.items():
            padding = "  " * indent
            if isinstance(value, (dict, list)):
                text_blob += (
                    f"{padding}{key}:\n{process_json(value, indent + 1)}"
                )
            else:
                text_blob += f"{padding}{key}: {value}\n"

    elif isinstance(json_object, list):
        for index, item in enumerate(json_object):
            padding = "  " * indent
            if isinstance(item, (dict, list)):
                text_blob += f"{padding}Item {index + 1}:\n{process_json(item, indent + 1)}"
            else:
                text_blob += f"{padding}Item {index + 1}: {item}\n"
    return text_blob

import shutil
import unittest
from src import constants
from src.semantic_search import SemanticSearch
import together
import os

class TestSemanticTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        # setup togetherAI
        together.api_key = os.environ.get("TOGETHER_API_KEY")
        together.Models.start("togethercomputer/llama-2-7b-chat")

        # setup semantic search
        cls.semantic_search = SemanticSearch()

        # setup chroma database
        cls.collection = cls.semantic_search.collection

        cls.collection.add(
            ids = ["1","2","3","4","5"],
            documents=[
                "<@U05DHDPL4FK> has joined the channel",
                "hello",
                "<https:\/\/haystack.deepset.ai\/tutorials\/08_preprocessing>",
                "It's best if we just post random topics here to test the semantic search.",
                "yeah then we'll see how we can clean the data"
            ],
            metadatas= [
                {
                    "user" : "U05DHDPL4FK",
                    "ts" : "1687165577.272839"
                },
                {
                    "user" : "U05DHDPL4FK",
                    "ts" : "1687166197.580079"
                },
                {
                    "user" : "U05DHDPL4FK",
                    "ts" : "1687166202.864639"
                },
                {
                    "user" : "U05CQ93C3FZ",
                    "ts" : "1687166901.338569"
                },
                {
                    "user" : "U05DHDPL4FK",
                    "ts" : "1687167171.439409"
                }   
            ]
        )



    @classmethod
    def tearDownClass(cls) -> None:
        # remove togetherAI setup
        together.api_key = os.environ.get("TOGETHER_API_KEY")
        together.Models.stop("togethercomputer/llama-2-7b-chat")

        # remove database setup
        try:
            shutil.rmtree(constants.CHROMA_PATH)
        except FileNotFoundError:
            pass
    

    
    def test_semantic_search(self):
        res = self.semantic_search.semantic_search("who said hello")
        
        print('-'*50)
        print(res)
        print('-'*50)


        # placeholder assertion
        self.assertEqual(1,1)

    def test_dummy(self):
        self.assertEqual(1,1)

class TestSemanticSearchBuilder(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        pass

    @classmethod
    def tearDownClass(cls) -> None:
        pass

if __name__ == "__main__":
    unittest.main()
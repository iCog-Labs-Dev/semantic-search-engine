
import unittest
from semantic_search_engine.semantic_search import SemanticSearch


class TestSemanticTest(unittest.TestCase):
    # def test_semantic_search(self):
    #     res = SemanticSearch.semantic_search(
    #             "Hello there!", 
    #             "67a96691fabefa1320d838470ca884833d0d99131c6d59d741609361e2141ee2"
    #         )
    #     print(
    #         f"\nresponse: {res['response']}\nmetadata : {res['metadata']}\n"
    #     )
    #     # placeholder assertion
    #     self.assertIsInstance(res["response"], str)
    def test_dummy(self):
        self.assertEqual(1,1)

if __name__ == "__main__":
    unittest.main()
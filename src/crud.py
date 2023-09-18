from src.chroma import ChromaSingleton
from src.constants import CHROMA_COLLECTION


class CRUD():

    collection = ChromaSingleton()\
        .get_connection()\
        .get_or_create_collection(CHROMA_COLLECTION)
    

    def create(self, message : str, metadata : object) -> None:
        """embeds and adds the message to chroma and inserts data to the SQL db

        Parameters
        ----------
        message : str
            the message to be embedded
        metadata : object
            arbitrary information regarding the message

        Returns
        -------
        None
        """
        self.collection.add(
            documents=["message", ...],
            metadatas=[{"chat_id": "..." }, ...],
            ids=["message_id", ...]
        )

        # TODO: Add the rest of the data to the sql database and define their relationships
    
    def read(self, query : str, n_results : int) -> list[str]:
        """takes a query and returns a list of message ids related to the query

        Parameters
        ----------
        query : str
            the query entered by the user
        n_results : str
            the number of messages that will be given to the llm

        Returns
        -------
        list[str]
            a list of message ids related to the user's query
        """
        return self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where = {
                "chat" : {
                    "$in" : self.__filter('user_id')
                }
            }
        )

    def update():
        # TODO: implement update/edit functionality
        pass

    def delete():
        # TODO: implement delete functionality
        pass


    # ***************** Helper functions ********************


    def __filter(self, user_id : str) -> list[str]:
        """extracts and returns a list of chat ids in which a user is permitted to view.

        Parameters
        ----------
        user_id : str
            the id of the user making the query

        Returns
        -------
        list[str]
            a list of chat ids a user is permitted to view
        """
        # TODO : implement chat filter functionality
from typing import List

from embeddings.Embeddings import Embeddings
from ingestion.chunking.Chunk import ParentChunk, ChildChunk
from langchain_text_splitters import RecursiveCharacterTextSplitter
import math
import uuid


class Chunker:

    def __init__(self, embedding_generator: Embeddings):
        self.embedding_generator = embedding_generator

        self.child_parent_ratio = 4
        self.child_text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=0)


    def create_chunks_from_splits_children(self, doc_id: uuid.UUID, user_id: uuid.UUID, splits):
        prev_chunk = None

        # Initialize an empty list to hold the chunk data
        chunks_data = []

        for split in splits:
            split = split.replace("\n", "")
            new_chunk_id = uuid.uuid4()  # Generate a new unique ID

            if prev_chunk is not None:
                prev_chunk.next_id = new_chunk_id

            if split == "":
                continue

            new_chunk = ChildChunk(
                chunk_id=new_chunk_id,
                text=split,
                prev_id=None if prev_chunk is None else prev_chunk.chunk_id,
                next_id=None,  # Will be updated later or remains -1 if it's the last chunk
                embeddings=[], # self.embedding_generator.get_embedding(split),
                metadata={},
                parent_id=None,
                user_id=user_id,
                document_id=doc_id
            )
            chunks_data.append(new_chunk)  # Add the new chunk to the list
            prev_chunk = new_chunk  # Update prev_chunk for the next iteration

        assert len(chunks_data) == len(splits)

        return chunks_data

    def create_parent_chunks_using_child_chunks(self, doc_id: uuid.UUID, user_id: uuid.UUID, children_chunks_list: List[ChildChunk]):

        prev_par_chunk = None
        parent_chunks = []

        chunk_size = 4
        for i in range(0, len(children_chunks_list), chunk_size):
            # Get the next chunk of up to 4 elements
            child_chunks = children_chunks_list[i:i + chunk_size]

            parent_chunk_ID = uuid.uuid4()
            text = ""
            for chunk in child_chunks:
                chunk.parent_id = parent_chunk_ID
                text += chunk.text

            new_parent_chunk = ParentChunk(
                chunk_id=parent_chunk_ID,
                text=text,
                embeddings=[],
                metadata={},
                prev_id=None if prev_par_chunk is None else prev_par_chunk.chunk_id,
                next_id=None,
                number_of_children=len(child_chunks),
                user_id=user_id,
                document_id=doc_id
            )

            # If you need to replace the original list elements with modified ones:
            children_chunks_list[i:i + chunk_size] = child_chunks

            parent_chunks.append(new_parent_chunk)

            prev_par_chunk = new_parent_chunk


        assert math.ceil(len(children_chunks_list) / self.child_parent_ratio) == len(parent_chunks)

        return children_chunks_list, parent_chunks


    def split_text(self, text: str) -> List[str]:
        return self.child_text_splitter.split_text(text)


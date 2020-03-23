from document import Document
from typing import Iterable, Union
from components.cleaner_component import CleanerComponent
import argparse


class DocumentOrganizer(CleanerComponent):
    def __init__(self, args: argparse.Namespace):
        pass

    @staticmethod
    def add_args(parser: argparse.ArgumentParser):
        pass

    @staticmethod
    def check_args(args: argparse.Namespace):
        # TODO check custom args
        pass

    def organize_documents(self, documents: Iterable[Document]) -> Iterable[Document]:
        # TODO add keywords/labels
        return documents

    def _find_domains(self):
        raise NotImplementedError()

    def apply(self, documents: Union[Iterable[Document], None]) -> Union[Iterable[Document], None]:
        return self.organize_documents(documents)

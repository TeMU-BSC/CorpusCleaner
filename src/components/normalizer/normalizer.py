from document import Document
from typing import Iterable, Union, Dict
from components.cleaner_component import CleanerComponent
import argparse


class Normalizer(CleanerComponent):
    @staticmethod
    def add_args(parser: argparse.ArgumentParser):
        parser.add_argument('--spell-check', action='store_true', help='Apply spell checking.')
        parser.add_argument('--terminology-norm', type=str, help='Path to a terminology dictionary to appliy normalization',
                            default=None)
        parser.add_argument('--punctuation-norm', action='store_true', help='Apply punctuation normalization.')

    @staticmethod
    def check_args(args: argparse.Namespace):
        # TODO check custom args
        pass

    def __init__(self, args: argparse.Namespace, spell_check: bool = False, terminology_norm: Union[None, Dict[str, str]] = None,
                 punctuation_norm: bool = False):
        self.spell_check = args.spell_check if args.spell_check is not None else spell_check
        self.terminology_norm = args.terminology_norm if args.terminology_norm is not None else terminology_norm
        self.punctuation_norm = args.punctuation_norm if args.punctuation_norm is not None else punctuation_norm

    def normalize(self, documents: Iterable[Document]) -> Iterable[Document]:
        if self.spell_check:
            self._spell_checking()
        if self.terminology_norm is not None:
            self._terminology_normalization()
        if self.punctuation_norm:
            self._punctuation_normalization()
        return documents

    def _spell_checking(self):
        raise NotImplementedError()

    def _terminology_normalization(self):
        raise NotImplementedError()

    def _punctuation_normalization(self):
        raise NotImplementedError()

    def apply(self, documents: Union[Iterable[Document], None]) -> Union[Iterable[Document], None]:
        return self.normalize(documents)

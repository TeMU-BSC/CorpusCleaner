from corpus_cleaner.document import Document
from typing import Iterable, Union, Tuple
from corpus_cleaner.components.cleaner_component import CleanerComponent
from langid.langid import LanguageIdentifier, model
import argparse



class SentenceFilter(CleanerComponent):
    @staticmethod
    def add_args(parser: argparse.ArgumentParser):
        parser.add_argument('--char-length-filter-sentence', type=int, default=30,
                            help='filter sentences shorter than a given minimum character length')
        parser.add_argument('--profanity-check', action='store_true',
                            help='filter sentences with sensible content')

    @staticmethod
    def check_args(args: argparse.Namespace):
        # TODO check custom args
        pass

    def __init__(self, args: argparse.Namespace, char_length_filter_sentence: int = 30, 
                 lang_filter: Union[Tuple[str], None] = None, lang_filter_threshold: float = 0.90,
                 profanity_check: bool = True):
        super().__init__(args)
        self.char_length_filter_sentence = args.char_length_filter_sentence if args.char_length_filter_sentence is not \
                                                                               None else char_length_filter_sentence
        self.profanity_check = args.profanity_check if args.profanity_check is not None else profanity_check
        self.lang_filter = args.lang_filter if args.lang_filter is not None else lang_filter
        self.lang_id = None
        self.lang_filter_threshold = args.lang_filter_threshold if args.lang_filter_threshold is not None else \
            lang_filter_threshold
        self.filters = []
        self._get_filters()

    def _filter(self, documents: Iterable[Document]) -> Iterable[Document]:
        for doc in documents:
            sentences_filtered = []
            for sent in doc.sentences:
                # keep only sentences that are not filtered out by all the filters
                if all(_filter(sent) for _filter in self.filters):
                    sentences_filtered.append(sent)
            # return the document if contains at least one sentence
            if sentences_filtered:
                doc.sentences = sentences_filtered
                yield doc

    def _get_filters(self):
        if self.char_length_filter_sentence is not None:
            self.filters.append(self._filter_by_char_len)
        if self.lang_filter is not None:
            self.lang_id = LanguageIdentifier.from_modelstring(model, norm_probs=True)
            self.filters.append(self._filter_by_lang)

    def _filter_by_char_len(self, sentence: str) -> bool:
        if len(sentence) > self.char_length_filter_sentence:
            return True
        return False
        
    def _filter_by_lang(self, sentence: str):
        res = self.lang_id.classify(sentence)
        if res[0] in self.lang_filter and res[1] > self.lang_filter_threshold:
            return True
        return False


    def apply(self, documents: Union[Iterable[Document], None]) -> Union[Iterable[Document], None]:
        return self._filter(documents)
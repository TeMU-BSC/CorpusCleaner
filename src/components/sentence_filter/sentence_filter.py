from document import Document
from typing import Iterable
from components.data_parser.bsc_crawl_json_parser import BSCCrawlJSONParser
from components.sentence_splitter_component.sentence_splitter_component import SentenceSplitterComponent
from components.cleaner_component import CleanerComponent
import argparse


class SentenceFilter(CleanerComponent):
    @staticmethod
    def add_args(parser: argparse.ArgumentParser):
        parser.add_argument('--char-length-filter-sentence', type=int, help='Minimum char length to accept a sentence.',
                            default=40)
        parser.add_argument('--profanity_check', action='store_true',
                            help='filter sentences with sensible content')

    @staticmethod
    def check_args(args: argparse.Namespace):
        # TODO check custom args
        pass

    def __init__(self, char_length_filter_sentence: int, profanity_check: bool = True):
        self.char_length_filter_sentence = char_length_filter_sentence
        self.profanity_check = profanity_check
        self.filters = []
        self._get_filters()

    def filter(self, documents: Iterable[Document]) -> Iterable[Document]:
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
        if self.char_length_filter_sentence:
            self.filters.append(self._check_char_len)

    def _check_char_len(self, sentence: str) -> bool:
        if len(sentence) > self.char_length_filter_sentence:
            return True
        else:
            return False


def test():
    file_dir = '../../../test/bne'
    # parse documents
    parser = BSCCrawlJSONParser(file_dir)
    documents_parsed = parser.parse()

    # apply sentence splitting
    splitter = SentenceSplitterComponent(language='es')
    documents_splitted = splitter.split(documents_parsed)

    # apply sentence filtering
    sentence_filter = SentenceFilter(char_length_filter_sentence=1)
    documents_sentence_filtered = sentence_filter.filter(documents_splitted)

    # Show the first two documents
    for idx, doc in enumerate(documents_sentence_filtered):
        print(f'DOC {idx} (sentences filtered): {doc.sentences}\n')

        if idx == 1:
            break


if __name__ == '__main__':
    test()

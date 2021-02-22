from .wikipedia_parser import  WikipediaParser
from .bsc_crawl_json_parser import BSCCrawlJSONParser
from .fairseq_lm_parser import FairseqLMParser
from .sentence_parser import SentenceParser
from .onion_parser import OnionParser
from .warc_parser import WARCParser
from .data_parser import DataParser, DataParserConfig
from .data_parser_mapper import DataParserMapper
from .document_parser import DocumentParser
from .textfile_parser import TextfileParser
from corpus_cleaner.par_utils.par_utils import PipelineLogger
from typing import Optional


class DataParserFactory:
    VALID_INPUT_FORMATS = ['wikipedia', 'bsc-crawl-json', 'fairseq-lm', 'sentence', 'warc', 'document', 'textfile']

    @staticmethod
    def get_parser(input_format: str, config: DataParserConfig, logger: Optional[PipelineLogger] = None,
                   debug: bool = False) -> DataParser:
        if input_format == 'wikipedia':
            return WikipediaParser(config, logger)
        elif input_format == 'bsc-crawl-json':
            return BSCCrawlJSONParser(config, logger)
        elif input_format == 'fairseq-lm':
            return FairseqLMParser(config, logger)
        elif input_format == 'sentence':
            return SentenceParser(config, logger)
        elif input_format == 'warc':
            return WARCParser(config, logger)
        elif input_format == 'document':
            return DocumentParser(config, logger)
        elif input_format == 'textfile':
            return TextfileParser(config, logger)
        elif input_format == 'onion':
            config.encoding = 'utf-8'
            return OnionParser(config, logger, debug=debug)
        else:
            raise NotImplementedError(input_format)

    @staticmethod
    def get_parser_mapper(input_format: str, config: DataParserConfig, debug: bool = False) -> DataParserMapper:
        return DataParserMapper(DataParserFactory.get_parser(input_format, config, debug=debug))

from functools import lru_cache
import os

from flask import Flask, jsonify, request
from pydantic import ValidationError
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge, UnsupportedMediaType

from hts_core.adapters import nlp
from hts_core.adapters.parsers import UnsupportedFileError, parse_document
from hts_core.adapters.parsers.pdf_parser import NoTextLayerError, ProtectedPdfError, PdfReadError
from hts_core.adapters.parsers.txt_parser import TxtDecodeError
from hts_core.adapters.resources import idf_resource, load_policy
from hts_core.adapters.schemas import ApiError, CompareRequest, ComparisonResult, Extraction
from hts_core.adapters.semantic import ResourceUnavailable, SemanticEncoder
from hts_core.application.comparison import ComparisonService, InvalidDocument


def create_app(service=None):
    app = Flask(__name__)
    config, config_hash = load_policy()
    app.config['MAX_CONTENT_LENGTH'] = 2 * config['max_upload_bytes'] + 65536

    @lru_cache(maxsize=1)
    def resources():
        if service is not None:
            return service
        idf, idf_info = idf_resource(os.environ.get('HTS_IDF_PATH'))
        try:
            encoder, error = SemanticEncoder(), None
        except ResourceUnavailable as exc:
            encoder, error = None, str(exc)
        return ComparisonService(idf, idf_info, encoder, config, config_hash, nlp.analyze, nlp.STOPWORDS, error)

    def error(state, detail, status):
        return jsonify(ApiError(state=state, detail=detail).model_dump()), status

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(exc):
        return error('invalid_input', 'limite de upload excedido', 413)

    @app.get('/v1/health')
    def health():
        return jsonify(contract_version='1.0', status='alive')

    @app.post('/v1/compare')
    def compare():
        try:
            data = CompareRequest.model_validate(request.get_json())
        except (ValidationError, BadRequest, UnsupportedMediaType, TypeError):
            return error('invalid_input', 'requisição incompatível com contrato 1.0', 400)
        try:
            result = resources().compare(data.source.text, data.suspect.text, data.mode)
            return jsonify(ComparisonResult.model_validate(result).model_dump())
        except InvalidDocument as exc:
            state = 'no_useful_content' if 'sem conteúdo' in str(exc) else 'invalid_input'
            return error(state, str(exc), 422)
        except ResourceUnavailable:
            return error('resource_unavailable', 'recurso obrigatório indisponível', 503)
        except ValueError:
            return error('resource_unavailable', 'representação inválida ou limite de tokens excedido; sem classificação', 503)

    @app.post('/v1/extract')
    def extract():
        if set(request.files) != {'file'} or set(request.form) != {'contract_version'} or request.form['contract_version'] != '1.0':
            return error('invalid_input', 'envie file e contract_version=1.0', 400)
        file = request.files['file']
        data = file.read(config['max_upload_bytes'] + 1)
        if len(data) > config['max_upload_bytes']:
            return error('invalid_input', 'limite de upload excedido', 413)
        try:
            text = parse_document(file.filename or '', data)
        except UnsupportedFileError:
            return error('unsupported_format', 'tipo real e extensão incompatíveis ou não suportados', 415)
        except NoTextLayerError as exc:
            return error('no_useful_content', str(exc), 422)
        except (ProtectedPdfError, PdfReadError, TxtDecodeError) as exc:
            return error('extraction_failed', str(exc), 422)
        except (ValueError, OSError, KeyError):
            return error('extraction_failed', 'não foi possível extrair texto; OCR não executado', 422)
        if not text.strip():
            return error('no_useful_content', 'documento sem texto utilizável', 422)
        return jsonify(Extraction(contract_version='1.0', text=text).model_dump())

    return app

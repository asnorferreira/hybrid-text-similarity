import codecs


class TxtDecodeError(ValueError):
    pass


def extract_txt_text(data: bytes) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        if data.startswith(codecs.BOM_UTF8):
            raise TxtDecodeError("Não foi possível decodificar TXT: BOM UTF-8 com conteúdo inválido.") from error
    try:
        return data.decode("cp1252")
    except UnicodeDecodeError as error:
        raise TxtDecodeError("Não foi possível decodificar TXT como UTF-8 ou cp1252, sem perda.") from error

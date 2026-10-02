from . import santander, itau, bradesco, bb_corrente, bb_poupanca, caixa

PARSERS = {
    "Santander": santander.parse,
    "Itau": itau.parse,
    "Bradesco": bradesco.parse,
    "Banco Brasil Corrente": bb_corrente.parse,
    "Banco Brasil Poupanca": bb_poupanca.parse,
    "Caixa": caixa.parse,
}

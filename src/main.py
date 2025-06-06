#!/usr/bin/env python3

# Importa os módulos necessários do Flask e do sistema operacional
from flask import Flask, render_template
import os
# Importa o módulo para carregar variáveis de ambiente de um arquivo .env
from dotenv import load_dotenv
# Importa o módulo sys para manipular o caminho de importação
import sys

# Adiciona o diretório pai ao caminho de importação do Python.
# Isso é necessário para que o Flask possa encontrar os módulos dentro de 'src'.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa o Blueprint de análise de imagem que contém as rotas da API
from src.routes.image_analysis import image_analysis_bp

# Carrega as variáveis de ambiente do arquivo .env
# Por exemplo, a chave da API da OpenAI será carregada daqui.
load_dotenv()

# Inicializa a aplicação Flask
app = Flask(__name__)

# Configura uma chave secreta para a aplicação Flask.
# É usada para segurança, como proteger sessões.
# os.urandom(24) gera uma sequência aleatória de 24 bytes.
app.config["SECRET_KEY"] = os.urandom(24)

# Define o limite máximo de tamanho para uploads de arquivos (16 MB).
# Isso evita que arquivos muito grandes sobrecarreguem o servidor.
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 Megabytes

# Registra o Blueprint de análise de imagem na aplicação Flask.
# Todas as rotas definidas em image_analysis_bp terão o prefixo "/api".
# Por exemplo, a rota /upload se tornará /api/upload.
app.register_blueprint(image_analysis_bp, url_prefix="/api")

# Define a rota principal da aplicação (a página inicial).
# Quando alguém acessa a URL base (por exemplo, http://localhost:5000/), esta função é executada.
@app.route("/")
def index():
    # Renderiza o template HTML chamado "index.html".
    # Este arquivo HTML é o frontend da nossa aplicação.
    return render_template("index.html")

# Bloco principal de execução do script.
# Garante que o servidor Flask só seja iniciado se o script for executado diretamente.
if __name__ == "__main__":
    # Inicia o servidor Flask.
    # host=\'0.0.0.0\': Torna o servidor acessível de qualquer endereço IP (útil em ambientes de contêiner/sandbox).
    # port=5000: Define a porta em que o servidor irá escutar as requisições.
    # debug=True: Ativa o modo de depuração, que recarrega o servidor automaticamente em caso de alterações no código
    # e fornece mensagens de erro detalhadas.
    app.run(host="0.0.0.0", port=5000, debug=True)



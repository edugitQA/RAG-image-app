from flask import Blueprint, request, jsonify, render_template, current_app, send_file
import os
import base64
from openai import OpenAI
from werkzeug.utils import secure_filename
import json
from datetime import datetime
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
# Isso garante que a chave da API da OpenAI esteja disponível.
load_dotenv()

# Cria um Blueprint para as rotas de análise de imagem.
# Blueprints ajudam a organizar as rotas em módulos lógicos.
image_analysis_bp = Blueprint("image_analysis", __name__)

# Inicializa o cliente OpenAI com a chave da API.
# A chave é obtida das variáveis de ambiente.
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    # Emite um aviso se a chave da API não for encontrada.
    print("AVISO: OPENAI_API_KEY não encontrada no ambiente. Certifique-se de que o arquivo .env está configurado corretamente.")
client = OpenAI(api_key=api_key)

# Define o diretório onde as imagens enviadas serão salvas.
# Ele é criado dentro da pasta 'static' para que o frontend possa acessá-las.
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "uploads")

# Define as extensões de arquivo permitidas para upload.
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "tiff"}

# Prompt padrão para análise de imagens.
# Este prompt será usado se o usuário não fornecer um prompt personalizado.
DEFAULT_PROMPT = "Descreva detalhadamente o conteúdo desta imagem para fins de RAG. Inclua objetos, pessoas, ações, texto visível e o contexto geral da cena."

# Cria o diretório de uploads se ele ainda não existir.
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """
    Verifica se o nome do arquivo tem uma extensão permitida.
    
    Args:
        filename (str): O nome do arquivo a ser verificado.
        
    Returns:
        bool: True se a extensão for permitida, False caso contrário.
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_image_to_base64(image_path):
    """
    Codifica uma imagem para o formato base64.
    Isso é necessário porque a API da OpenAI aceita imagens em base64.
    
    Args:
        image_path (str): O caminho completo para o arquivo de imagem.
        
    Returns:
        str: A string da imagem codificada em base64.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def analyze_image_with_openai(image_path, prompt=None):
    """
    Envia uma imagem para a API de Visão da OpenAI para análise e retorna a descrição.
    
    Args:
        image_path (str): Caminho para o arquivo de imagem.
        prompt (str, optional): Prompt personalizado para análise. Se None ou vazio, usa o prompt padrão.
        
    Returns:
        str: A descrição da imagem gerada pela OpenAI ou uma mensagem de erro.
    """
    # Usa o prompt fornecido ou o prompt padrão se nenhum for dado.
    if prompt is None or prompt.strip() == "":
        prompt = DEFAULT_PROMPT
        
    try:
        # Codifica a imagem para base64.
        base64_image = encode_image_to_base64(image_path)
        
        # Faz a chamada à API da OpenAI.
        response = client.chat.completions.create(
            model="gpt-4o", # Modelo de visão da OpenAI (gpt-4o é o mais recente com visão).
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}, # O prompt para a análise.
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}", # A imagem em base64.
                                "detail": "high" # Solicita uma análise de alta resolução.
                            },
                        },
                    ],
                }
            ],
            max_tokens=1000, # Limite de tokens para a resposta da OpenAI.
        )
        # Retorna o conteúdo da descrição gerada.
        return response.choices[0].message.content
    except Exception as e:
        # Captura e retorna qualquer erro que ocorra durante a análise.
        return f"Erro ao analisar a imagem {os.path.basename(image_path)}: {e}"

@image_analysis_bp.route("/upload", methods=["POST"])
def upload_file():
    """
    Endpoint para upload de imagens.
    Recebe arquivos de imagem via POST, os salva, analisa com a OpenAI e gera um arquivo RAG.
    """
    # Verifica se há arquivos na requisição.
    if "files[]" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    # Obtém a lista de arquivos enviados.
    files = request.files.getlist("files[]")
    
    # Verifica se algum arquivo foi realmente selecionado.
    if not files or files[0].filename == "":
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400
    
    # Obtém o prompt personalizado enviado pelo frontend ou usa o padrão.
    custom_prompt = request.form.get("prompt", DEFAULT_PROMPT)
    
    results = [] # Lista para armazenar os resultados de cada imagem.
    
    # Cria um diretório único para esta sessão de upload usando um timestamp.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(UPLOAD_FOLDER, f"session_{timestamp}")
    os.makedirs(session_dir, exist_ok=True)
    
    # Define o caminho para o arquivo JSON que armazenará os resultados intermediários.
    results_file = os.path.join(session_dir, "analysis_results.json")
    
    # Itera sobre cada arquivo enviado.
    for i, file in enumerate(files):
        # Verifica se o arquivo existe e tem uma extensão permitida.
        if file and allowed_file(file.filename):
            # Garante um nome de arquivo seguro para evitar problemas de segurança.
            filename = secure_filename(file.filename)
            file_path = os.path.join(session_dir, filename)
            file.save(file_path) # Salva o arquivo no diretório da sessão.
            
            # Analisa a imagem usando a função analyze_image_with_openai com o prompt.
            description = analyze_image_with_openai(file_path, custom_prompt)
            
            # Adiciona o resultado da análise à lista.
            result = {
                "filename": filename,
                "path": file_path,
                "description": description
            }
            results.append(result)
            
            # Atualiza o arquivo de resultados JSON após cada análise.
            # Isso permite acompanhar o progresso e recuperar dados em caso de falha.
            with open(results_file, "w") as f:
                json.dump(results, f, indent=4)
        else:
            # Adiciona um erro se o arquivo não for válido.
            results.append({
                "filename": file.filename if file else "unknown",
                "error": "Tipo de arquivo não permitido"
            })
    
    # Gera o arquivo RAG estruturado em formato de texto.
    rag_file = os.path.join(session_dir, "rag_structured_data.txt")
    with open(rag_file, "w", encoding="utf-8") as f:
        f.write("# Dados Estruturados para RAG\n\n")
        f.write(f"## Prompt utilizado\n\n{custom_prompt}\n\n") # Inclui o prompt usado.
        f.write("## Resultados da Análise\n\n")
        for result in results:
            if "description" in result:
                f.write(f"### {result['filename']}\n\n") # Título para cada imagem.
                f.write(f"{result['description']}\n\n") # Descrição da imagem.
    
    # Gera também uma versão em PDF do arquivo RAG usando a ferramenta manus-md-to-pdf.
    rag_pdf = os.path.join(session_dir, "rag_structured_data.pdf")
    try:
        import subprocess
        # Executa o comando para converter Markdown para PDF.
        subprocess.run(["manus-md-to-pdf", rag_file, rag_pdf], check=True)
    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")
    
    # Retorna uma resposta JSON para o frontend com os resultados e caminhos dos arquivos.
    return jsonify({
        "message": f"{len(results)} imagens processadas com sucesso",
        "results": results,
        "rag_file": rag_file,
        "rag_pdf": rag_pdf if os.path.exists(rag_pdf) else None, # Retorna o caminho do PDF se gerado.
        "session_id": f"session_{timestamp}", # ID da sessão para referência futura.
        "prompt_used": custom_prompt # O prompt que foi efetivamente usado.
    })

@image_analysis_bp.route("/download", methods=["GET"])
def download_file():
    """
    Endpoint para download do arquivo RAG estruturado (TXT ou PDF).
    """
    file_path = request.args.get("file") # Obtém o caminho do arquivo da URL.
    
    # Verifica se o caminho do arquivo foi fornecido e se o arquivo existe.
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "Arquivo não encontrado"}), 404
    
    # Se for um arquivo TXT, verifica se existe uma versão PDF correspondente para download.
    if file_path.endswith(".txt"):
        pdf_path = file_path.replace(".txt", ".pdf")
        if os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True) # Envia o PDF se existir.
    
    # Caso contrário, envia o arquivo original (TXT).
    return send_file(file_path, as_attachment=True)

@image_analysis_bp.route("/results/<session_id>", methods=["GET"])
def get_results(session_id):
    """
    Endpoint para obter os resultados de uma sessão específica.
    Isso pode ser útil para recuperar resultados de análises anteriores.
    
    Args:
        session_id (str): O ID da sessão de upload.
        
    Returns:
        json: Os resultados da análise para a sessão especificada.
    """
    # Constrói o caminho para o diretório da sessão.
    session_dir = os.path.join(UPLOAD_FOLDER, session_id)
    results_file = os.path.join(session_dir, "analysis_results.json")
    
    # Verifica se o arquivo de resultados da sessão existe.
    if not os.path.exists(results_file):
        return jsonify({"error": "Sessão não encontrada"}), 404
    
    # Carrega e retorna os resultados do arquivo JSON.
    with open(results_file, "r") as f:
        results = json.load(f)
    
    return jsonify(results)



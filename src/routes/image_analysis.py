from flask import Blueprint, request, jsonify, send_file
import os
import base64
from openai import OpenAI
from werkzeug.utils import secure_filename
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
image_analysis_bp = Blueprint("image_analysis", __name__)
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("AVISO: OPENAI_API_KEY não encontrada no ambiente. Certifique-se de que o arquivo .env está configurado corretamente.")
client = OpenAI(api_key=api_key)
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "tiff"}
DEFAULT_PROMPT = "Descreva detalhadamente o conteúdo desta imagem para fins de RAG. Inclua objetos, pessoas, ações, texto visível e o contexto geral da cena."
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def analyze_image_with_openai(image_path, prompt=None):
    if prompt is None or prompt.strip() == "":
        prompt = DEFAULT_PROMPT
    try:
        base64_image = encode_image_to_base64(image_path)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            },
                        },
                    ],
                }
            ],
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erro ao analisar a imagem {os.path.basename(image_path)}: {e}"

def clean_openai_response(response_text):
    import re
    tags = [
        r'<role>.*?</role>',
        r'<objetivo>.*?</objetivo>',
        r'<entrada>.*?</entrada>',
        r'<instrucoes>.*?</instrucoes>',
        r'<formato_saida>.*?</formato_saida>',
        r'<output_final>.*?</output_final>',
        r'<pensando>.*?</pensando>',
        r'<imagens>.*?</imagens>',
    ]
    cleaned = response_text
    for tag in tags:
        cleaned = re.sub(tag, '', cleaned, flags=re.DOTALL|re.IGNORECASE)
    cleaned = re.sub(r'```.*?```', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'^- .*$','', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    match = re.search(r'<resposta>(.*?)</resposta>', cleaned, flags=re.DOTALL|re.IGNORECASE)
    if match:
        cleaned = match.group(1)
    cleaned = re.sub(r'<.*?>', '', cleaned)
    cleaned = cleaned.strip()
    return cleaned

@image_analysis_bp.route("/upload", methods=["POST"])
def upload_file():
    if "files[]" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    files = request.files.getlist("files[]")
    if not files or files[0].filename == "":
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400
    custom_prompt = request.form.get("prompt", DEFAULT_PROMPT)
    results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(UPLOAD_FOLDER, f"session_{timestamp}")
    os.makedirs(session_dir, exist_ok=True)
    results_file = os.path.join(session_dir, "analysis_results.json")
    for i, file in enumerate(files):
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(session_dir, filename)
            file.save(file_path)
            description_raw = analyze_image_with_openai(file_path, custom_prompt)
            description = clean_openai_response(description_raw)
            result = {
                "filename": filename,
                "path": file_path,
                "description": description
            }
            results.append(result)
            with open(results_file, "w") as f:
                json.dump(results, f, indent=4)
        else:
            results.append({
                "filename": file.filename if file else "unknown",
                "error": "Tipo de arquivo não permitido"
            })
    rag_file = os.path.join(session_dir, "rag_structured_data.txt")
    with open(rag_file, "w", encoding="utf-8") as f:
        f.write("# Resultados da Análise\n\n")
        for result in results:
            if "description" in result:
                f.write(f"### {result['filename']}\n\n")
                f.write(f"{result['description']}\n\n")
    rag_pdf = os.path.join(session_dir, "rag_structured_data.pdf")
    try:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        with open(rag_file, "r", encoding="utf-8") as txtfile:
            for line in txtfile:
                for subline in [line[i:i+100] for i in range(0, len(line), 100)]:
                    pdf.cell(0, 10, subline.rstrip(), ln=1)
        pdf.output(rag_pdf)
    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")
    return jsonify({
        "message": f"{len(results)} imagens processadas com sucesso",
        "results": results,
        "rag_file": rag_file,
        "rag_pdf": rag_pdf if os.path.exists(rag_pdf) else None,
        "session_id": f"session_{timestamp}",
        "prompt_used": custom_prompt
    })

@image_analysis_bp.route("/download", methods=["GET"])
def download_file():
    file_path = request.args.get("file")
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "Arquivo não encontrado"}), 404
    return send_file(file_path, as_attachment=True)

@image_analysis_bp.route("/results/<session_id>", methods=["GET"])
def get_results(session_id):
    session_dir = os.path.join(UPLOAD_FOLDER, session_id)
    results_file = os.path.join(session_dir, "analysis_results.json")
    if not os.path.exists(results_file):
        return jsonify({"error": "Sessão não encontrada"}), 404
    with open(results_file, "r") as f:
        results = json.load(f)
    return jsonify(results)



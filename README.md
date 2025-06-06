# Automação de Análise de Imagens para RAG com OpenAI e Flask

Este projeto é uma automação em Python que permite o upload de imagens, as analisa usando a API de Visão da OpenAI (GPT-4o) e gera um arquivo de texto estruturado (e opcionalmente um PDF) para uso em sistemas de Retrieval-Augmented Generation (RAG). A aplicação inclui um frontend web simples para facilitar o upload e a visualização dos resultados, além de permitir a personalização do prompt de análise.

## Funcionalidades

*   **Upload de Múltiplas Imagens:** Envie várias imagens de uma só vez através de uma interface web intuitiva.
*   **Análise de Conteúdo de Imagens:** Utiliza a API GPT-4o da OpenAI para descrever detalhadamente o conteúdo de cada imagem.
*   **Prompt Personalizável:** Altere o prompt de análise diretamente no frontend para extrair informações específicas de acordo com suas necessidades.
*   **Geração de Dados Estruturados para RAG:** Os resultados da análise são formatados em um arquivo de texto (`.txt`) com uma estrutura clara, ideal para alimentar modelos de IA.
*   **Geração de PDF:** Uma versão em PDF do arquivo estruturado é gerada automaticamente para facilitar a visualização e o compartilhamento.
*   **Exibição de Progresso:** Acompanhe o progresso da análise das imagens diretamente na interface.

## Estrutura do Projeto

```
image_rag_app/
├── venv/                   # Ambiente virtual Python
├── src/
│   ├── static/             # Arquivos estáticos (CSS, JS, imagens de upload)
│   │   └── uploads/        # Diretório para imagens enviadas e resultados de sessão
│   ├── templates/          # Templates HTML (frontend)
│   │   └── index.html
│   ├── routes/             # Módulos com as rotas da API Flask
│   │   └── image_analysis.py
│   └── main.py             # Ponto de entrada principal da aplicação Flask
├── .env                    # Arquivo para variáveis de ambiente (chave da API OpenAI)
├── requirements.txt        # Dependências do projeto Python
└── README.md               # Este arquivo de documentação
```

## Como Configurar e Executar

Siga os passos abaixo para configurar e executar a aplicação em seu ambiente local.

### Pré-requisitos

*   Python 3.8 ou superior
*   Chave da API da OpenAI (você pode obtê-la em [platform.openai.com](https://platform.openai.com/))

### 1. Clonar o Repositório (ou criar a estrutura)

Se você recebeu o projeto como um arquivo zip, descompacte-o. Caso contrário, você pode criar a estrutura de diretórios manualmente.

### 2. Configurar o Ambiente Virtual

É altamente recomendável usar um ambiente virtual para gerenciar as dependências do projeto.

Abra o terminal na pasta `image_rag_app` e execute os seguintes comandos:

```bash
python3 -m venv venv
source venv/bin/activate  # No Windows: .\venv\Scripts\activate
```

### 3. Instalar Dependências

Com o ambiente virtual ativado, instale as bibliotecas Python necessárias:

```bash
pip install -r requirements.txt
```

### 4. Configurar a Chave da API da OpenAI

Crie um arquivo chamado `.env` na raiz do diretório `image_rag_app` (ao lado de `requirements.txt`) e adicione sua chave da API da OpenAI no seguinte formato:

```
OPENAI_API_KEY='sua_chave_aqui'
```

**Substitua `sua_chave_aqui` pela sua chave real da API da OpenAI.**

### 5. Executar a Aplicação Flask

Com o ambiente virtual ativado, execute o arquivo `main.py`:

```bash
python src/main.py
```

Você verá uma saída no terminal indicando que o servidor Flask está rodando. Geralmente, ele estará acessível em `http://127.0.0.1:5000` ou `http://localhost:5000`.

### 6. Acessar a Aplicação no Navegador

Abra seu navegador web e navegue para o endereço fornecido pelo terminal (por exemplo, `http://127.0.0.1:5000`).

## Como Usar a Aplicação

1.  **Upload de Imagens:** Clique em "Selecione as imagens para análise" e escolha uma ou mais imagens do seu computador.
2.  **Pré-visualização:** As imagens selecionadas aparecerão como miniaturas abaixo do campo de upload.
3.  **Personalizar Prompt (Opcional):** No campo "Prompt para análise das imagens:", você pode digitar um prompt personalizado para guiar a análise da IA. Se deixar em branco, o prompt padrão será utilizado. Há um botão "Restaurar Prompt Padrão" para conveniência.
4.  **Analisar Imagens:** Clique no botão "Analisar Imagens". Um spinner e uma barra de progresso (simulada) aparecerão enquanto as imagens são processadas.
5.  **Visualizar Resultados:** Após a análise, os resultados (descrição gerada pela IA para cada imagem) serão exibidos na seção "Resultados da Análise".
6.  **Baixar Arquivo RAG Estruturado:** Clique no botão "Baixar Arquivo RAG Estruturado" para fazer o download de um arquivo de texto (`.txt`) contendo todas as descrições formatadas para RAG. Uma versão em PDF também será gerada e baixada se a conversão for bem-sucedida.

## Detalhes Técnicos

*   **Backend:** Desenvolvido com Flask, um microframework web para Python.
*   **Frontend:** HTML, CSS (com Bootstrap para estilização) e JavaScript puro para interatividade.
*   **Análise de Imagens:** Utiliza a API `gpt-4o` da OpenAI para capacidades de visão computacional.
*   **Geração de PDF:** A ferramenta `manus-md-to-pdf` é utilizada para converter o arquivo Markdown (que é o formato do `.txt` gerado) em PDF.

## Considerações para RAG e IA

O arquivo de texto estruturado gerado (`rag_structured_data.txt`) é projetado para ser facilmente consumido por sistemas de RAG. Cada imagem e sua descrição são claramente delimitadas, permitindo que um modelo de linguagem (LLM) possa buscar e recuperar informações relevantes com base em consultas. O prompt personalizado é uma ferramenta poderosa para direcionar a extração de características específicas das imagens, otimizando a qualidade dos dados para o seu caso de uso de IA.

## Licença

Este projeto é de código aberto e está disponível sob a licença MIT. Sinta-se à vontade para modificar e distribuir.

<h1 align="center">📊 Multimodal Financial Report Analyzer</h1>

<p align="center">
AI-Powered Financial Document Analysis Using Google's Gemini API
</p>
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white" alt="Python 3.12">
</p>



## 🔍 Overview
This Python tool leverages Google's Gemini multimodal models to analyze financial documents (PDFs or images) and automatically generate structured, insightful, and visually enriched financial reports.

It extracts text, tables, and graphs from reports like:

- 📄 Quarterly earnings

- 📘 Annual financial statements

- 📈 Strategic financial disclosures

The system produces professional Markdown and PDF reports, summarizing:

- Revenue & profit trends 💰

- Key financial metrics 📊

- Strategic insights & risks 🔍

- Visual data from charts & tables 📉

## 🚀 Features
- ✅ PDF to image conversion

- 🤖 AI-powered content extraction & summarization (Gemini 1.5 models)

- 📁 Input: PDF or image directory

- 🧠 Two analysis modes:

    - smart (faster, focused)

    - full_context (deep & complete)

- 📄 Auto-generated Markdown + PDF report

- 📌 Includes original image references

## 🛠️ Setup
1. Clone the Repository
```bash
git clone https://github.com/yourusername/financial-analyzer.git
cd financial-analyzer
```
2. Install System Dependencies


   - Poppler (required by pdf2image):

        Ubuntu/Debian:

        ```bash
        sudo apt-get update
        sudo apt-get install -y poppler-utils
        ```
        macOS (using Homebrew):
        ```bash
        brew install poppler
        ```
        Windows:
        -   Download and extract Poppler from the official GitHub releases:  
            [Poppler for Windows - Installation Guide](https://github.com/oschwartz10612/poppler-windows#installation).
   

   - WeasyPrint dependencies (Cairo, Pango, GDK-PixBuf, etc.):
        
     Follow the official installation guide:
     [WeasyPrint Installation](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html)
     - [WeasyPrint Installation on Windows via WSL](https://weasyprint.org/docs/install/)

3. Install Python Dependencies
```bash
pip install -r requirements.txt
```
4. Set Up Environment: Create a .env file with your Gemini API key:

```bash
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

## 📂 Input Options
You can run the tool with either:

- A PDF file (it will convert pages to images)

- A directory of images (e.g., screenshots of financial pages)

## ⚙️ Usage
### 🔸 From PDF
```bash
python main.py \
  --input_images_dir input_images \
  --model_name gemini-1.5-pro \
  --from_pdf_path source_docs/ABN_AMRO_Bank_Q3_2024.pdf \
  --analysis_mode full_context
```
```bash
python main.py \
  --input_images_dir my_new_image_dir \
  --model_name gemini-1.5-flash-8b \
  --from_pdf_path source_docs/ABN_AMRO_Bank_Q3_2024.pdf \
  --analysis_mode smart
```
### 🔸 From Directory of Images

```bash
python main.py \
  --input_images_dir input_images \
  --model_name gemini-1.5-pro \
  --analysis_mode full_context
```
```bash
python main.py \
  --input_images_dir input_images \
  --model_name gemini-1.5-flash-8b \
  --analysis_mode smart
```

## 🧠 Analysis Modes

| Mode           | Description                              | Speed   |
| -------------- | ---------------------------------------- | ------- |
| `smart`        | Lightweight, faster, good for highlights | ⚡ Fast  |
| `full_context` | In-depth review, richer insights         | 🧠 Deep |


## 📦 File Structure

    financial-analyzer/
    ├── main.py
    ├── .env
    ├── requirements.txt
    ├── input_images/
    ├── source_docs/
    ├── stored_outputs/
    ├── report_output.md
    ├── report_output.pdf
    ├── README.md


## 📄 License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🙌 Acknowledgements
- Powered by Google's Gemini multimodal models

- PDF/image processing via `pdf2image`, `PIL`, `markdown2pdf`.

- CLI support via `python-fire`.

## 📬 Contact
Have questions, suggestions, or want to contribute?

📧 [lavmlk20201@gmail.com](mailto:lavmlk20201@gmail.com)
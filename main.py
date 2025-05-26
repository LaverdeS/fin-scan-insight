import os
import google.generativeai as gemini_api
import logging

from dotenv import load_dotenv
from markdown2pdf import generate_report_with_images
from pdf2image import convert_from_path
from pathlib import Path
from typing import Union, List
from PIL import Image
from fire import Fire
from typing import Optional


# Configure logging and load environment variables
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()

# System and Model Configuration
ANALYSIS_MODES = ["smart", "full_context"]

# Prompts
SYSTEM_PROMPT = """
You are a multimodal financial analysis assistant designed to interpret images of financial documents such as earnings reports, balance sheets, and annual reports.

Your task is to process images that may contain text, tables, graphs, or financial figures, and extract relevant information to assist analysts, investors, and auditors. Each image should be analyzed in its own context, and the extracted content should be structured, complete, and actionable.

You must:
- Read and interpret all textual, numerical, and visual content (e.g., graphs, charts, diagrams).
- Understand financial language and terminology.
- Identify key financial metrics (e.g., revenue, income, EPS), changes over time, and relevant ratios.
- Extract and summarize operational highlights, risks, strategic priorities, and other insights mentioned in the visuals or text.
- Provide outputs that are structured and tailored for further processing (e.g., in JSON or bullet points).

You will be guided by specific prompts to:
1. Extract the content fo each image.
2. Identify key insights and important information.
3. Generate structured summaries or reports for decision-making.

Be accurate, concise, and context-aware. Prioritize clarity and completeness in financial interpretation.
"""
DEFAULT_SMART_MODEL_NAME = "gemini-1.5-flash-8b"
DEFAULT_FULL_CONTEXT_MODEL_NAME = "gemini-1.5-pro"


def pdf2img_tool_executor(pdf_path: Path, output_images_dir:str) -> List[Path]:
    """
    Converts a PDF file to images and returns the image paths.
    """
    logging.info(f"source document: {str(pdf_path)}")
    images = convert_from_path(pdf_path, dpi=300, thread_count=4)

    if not os.path.exists(output_images_dir):
        os.makedirs(output_images_dir)

    image_paths = []
    for i, image in enumerate(images):
        image_path = Path(f'{output_images_dir}/page_{i + 1}.png')
        image.save(image_path, 'PNG')
        image_paths.append(image_path)

    return image_paths


def analyse_and_report(
        input_images_dir: str = 'input_images',
        model_name : str = DEFAULT_FULL_CONTEXT_MODEL_NAME,
        from_pdf_path: Optional[str] = "",
        analysis_mode : Optional[str] = ANALYSIS_MODES[1],
):
    """
    Analyze financial documents and generate a report using Google's Gemini models. If the `from_pdf_path` is provided,
    it will convert the PDF to images and analyze them. If no `from_pdf_path` is provided, it will analyze images from the specified directory
    in `input_images_dir`.

    :param input_images_dir: Directory containing input images (default: 'input_images').
    :param model_name: Name of the Gemini model to use (default: 'gemini-1.5-pro').
    :param from_pdf_path: Path to the PDF file to analyze (default: 'source_docs/ABN_AMRO_Bank_Q3_2024.pdf').
    :param analysis_mode: Mode of analysis, either 'smart' or 'full_context' (default: 'full_context').
    :raises ValueError: If the model name is not supported or if no images are found.
    :raises RuntimeError: If there is an error initializing the Gemini model.
    :raises FileNotFoundError: If the specified PDF file or images directory does not exist.
    :return: None
    """

    if not model_name or "gemini" not in model_name.lower():
        raise ValueError("Unsupported model. Only Google's Gemini models are supported.")

    try:
        gemini_api.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model_config = gemini_api.types.GenerationConfig(temperature=0)
        gemini = gemini_api.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_PROMPT,
            generation_config=model_config
        )
    except Exception as e:
        logging.error(f"Error initializing Gemini model: {e}")
        raise RuntimeError(
            f"Failed to initialize Gemini model '{model_name}'. "
            "Ensure the model name is valid and the API key is correctly set."
        ) from e

    source_doc_path = Path(from_pdf_path)

    print()
    logging.info(f"model name: {model_name}")
    logging.info(f"analysis mode: {analysis_mode}\n")

    logging.info("loading input images...")

    if from_pdf_path:
        [f.unlink() for f in Path(input_images_dir).glob('*') if f.is_file()]
        image_paths = pdf2img_tool_executor(source_doc_path, input_images_dir)
    else:
        logging.info(f"loading images from {input_images_dir}...")
        image_paths = [Path(f'{input_images_dir}/{image_name}') for image_name in os.listdir(input_images_dir)]

    if not image_paths:
        raise ValueError(f"No images found in the specified directory: {input_images_dir}")

    images = [Image.open(image_path) for image_path in image_paths]

    extract_content_prompt = """
        For each image, extract and organize the content into four main categories: textual content, tables, graphs, and metadata. Return the results in a structured JSON format as described below.

        For every image, provide a JSON object with the following fields:
        - "image_name": the name of the image file (e.g., "page_1.png")
        - "text_content": all visible text, including paragraphs, figure captions, headers, footnotes, and in-text financial figures. Do not summarize; extract it verbatim.
        - "tables": a list of tables found in the image, represented using markdown format. Preserve the layout and numerical accuracy of each table as much as possible.
        - "graphs": a list of visual graphs or charts with descriptive text explaining their content. For each graph, describe:
          - the chart type (e.g., bar chart, line graph, pie chart),
          - axis labels and units,
          - data series or variables displayed,
          - titles and legends (if present),
          - trends or key visual takeaways.
        - "metadata": any additional visual elements not captured in the above fields, such as logos, icons, signatures, footers, page numbers, section dividers, or decorative illustrations. Summarize them briefly.

        Process each image independently. Ensure the structure is consistent and no content is duplicated across fields.

        Example format:
        [
          {
            "image_name": "page_1.png",
            "text_content": "Revenue increased by 12% year-over-year...",
            "tables": [
              "| Metric         | Q1 2024 | Q1 2023 |\n|----------------|---------|---------|\n| Revenue        | $25B    | $22.4B  |"
            ],
            "graphs": [
              "Bar chart titled 'Quarterly Revenue Growth'. X-axis: Quarters (Q1 2023–Q1 2024), Y-axis: Revenue in billions. Shows consistent growth with a noticeable spike in Q4 2023."
            ],
            "metadata": "Tesla logo at top left, page number 1 at bottom right."
          },
          ...
        ]
        """

    contents = [*images, extract_content_prompt]

    logging.info("extracting content...")
    response_extract_content = gemini.generate_content(contents)
    logging.debug(
        f"extracted content (tokens:{len(response_extract_content.text.split())}): \n{response_extract_content.text}")

    extract_key_insights_prompt = f"""
        You are a financial analyst assistant. You are given a set of structured data extracted from a financial report, including text content, tables, graphs, and other metadata, organized by page.

        Your task is to:
        - Identify and extract the most relevant and actionable financial insights from the content.
        - Focus on key metrics, trends, risks, strategic moves, and commentary that help investors or professionals quickly understand the company’s performance.
        - Avoid repeating raw data. Instead, summarize and analyze each point clearly and concisely.
        - Group related insights across multiple images if applicable, and provide deep, context-aware commentary.

        Prioritize content related to:
        - Revenue, profit, and margin trends
        - Year-over-year and quarter-over-quarter comparisons
        - Guidance and forecasts
        - Operational metrics
        - Risk factors and challenges
        - Strategic initiatives (e.g., R&D, expansion, M&A)
        - Shareholder information (e.g., dividends, stock performance)
        - Visual insights from tables and graphs (explain them clearly)

        Output Format:
        Return a list of dictionaries, where each dictionary represents a distinct section of the report. Each dictionary must have:

        - "title": A concise and informative title for this insight section.
        - "content": A summarized and insightful explanation or analysis of the key points, aggregating information across related images.
        - "sources": A list of image filenames (e.g., "page_1.png", "page_2.png") that support the analysis.

        Example Output Structure:
        [
          {{
            "title": "Revenue Growth and Profitability Trends",
            "content": "The company reported a 12% YoY increase in revenue driven by higher unit sales and pricing power. Operating margin improved to 18% due to cost optimizations and supply chain efficiencies. These trends are consistent across multiple business units.",
            "sources": ["page_3.png", "page_5.png"]
          }},
          {{
            "title": "Future Outlook and Strategic Priorities",
            "content": "Management reiterated strong demand projections for Q2, emphasizing expansion into emerging markets and continued investment in R&D, particularly in AI-based vehicle systems.",
            "sources": ["page_7.png", "page_9.png"]
          }}
        ]

        Content:
        {response_extract_content.text}
        """

    logging.debug(f"EXTRACT_KEY_INSIGHTS_PROMPT: \n{extract_key_insights_prompt}")

    logging.info("extracting key insights...")
    response_key_insights = gemini.generate_content(extract_key_insights_prompt)
    logging.debug(f"key_insights (tokens:{len(response_key_insights.text.split())}): \n{response_key_insights.text}")

    generate_report_prompt = f"""
        You are a financial analyst AI assistant. Using the extracted key insights from the financial document images, generate a clear, comprehensive, and well-structured financial report in Markdown format.

        Your report should include the following sections (but not limited to):

        1. **Executive Summary**:  
           A concise overview of the company’s financial health and strategic direction.

        2. **Key Financial Metrics**:  
           Highlight revenue, net income, earnings per share (EPS), growth trends compared to previous periods, and relevant financial ratios (profitability, liquidity, leverage).

        3. **Financial Statements Overview**:  
           Summarize key points from the balance sheet, income statement, and cash flow statement, emphasizing assets, liabilities, equity, revenue, expenses, and cash flows.

        4. **Operational Performance and Market Conditions**:  
           Insights on company operations, market environment, and external economic factors.

        5. **Management Commentary and Strategic Priorities**:  
           Summarize management’s outlook, strategic plans, and any relevant risks or challenges.

        6. **Notable Events**:  
           Cover acquisitions, partnerships, shareholder-related information such as dividends and stock performance.

        7. **Risks and Mitigation**:  
           Discuss any risks, challenges, and the company’s approach to managing those risks.

        8. (additional sections as needed based on the insights provided)...
        ...

        Additionally, include a section for **Graphs and Tables** where you summarize the key visual insights from the images. Use markdown tables to represent any tabular data clearly.

        Use the provided key points as the source of information. Wherever appropriate, reference the image names (e.g., "page_3.png") containing relevant details by mentioning them in parentheses.

        Format your output with clear headings, bullet points, and tables where necessary to enhance readability.

        Only includes non-empty sections where you count with enough information to provide a meaningful summary/insight.
        Leave out any sections that do not have sufficient information to report on.

        ---

        **Note:** At the end of the report, include a section titled "Images to Attach" listing all unique image filenames referenced throughout the document for manual attachment. Leave the rest of the report content as is, without any additional instructions or comments.
        Also, enhance readability and engagement by using relevant emojis such as 📈 (growth), 📉 (decline), 💰 (financial metrics), and 🔍 (insights) throughout the report.
        Add a fitting title to the report, such as "Financial Report for Q1 2025" or "Earnings Update for Q1 2025".

        ---

        """

    # if analysis_mode = "smart" or any other than "full_context"
    report_prompt_input = f"""
                Here are the key insights extracted from the content:  
                {response_key_insights.text}
                """

    if analysis_mode == "full_context":
        report_prompt_input = f"""
            Here is the extracted content from the images structured in a json format:  
            {response_extract_content.text}

            And {report_prompt_input}
            """

    generate_report_prompt += report_prompt_input

    response = gemini.generate_content(generate_report_prompt)

    print("-" * 50)
    logging.info(f"✅ report generated successfully!")
    logging.debug(f"report content: \n{response.text}")
    logging.debug("-" * 50)

    report_filename = f'report_{source_doc_path.stem}_{analysis_mode}_{model_name}.md' if from_pdf_path else f'report_{analysis_mode}_{model_name}.md'
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(response.text)

    logging.info(f"generating .pdf report...")
    generate_report_with_images(report_filename)


if __name__ == "__main__":#
    Fire(analyse_and_report)

    """script execution example:
    
    FROM PDF:
        python main.py --input_images_dir input_images --model_name gemini-1.5-pro --from_pdf_path source_docs/ABN_AMRO_Bank_Q3_2024.pdf --analysis_mode full_context
        python main.py --input_images_dir my_new_image_dir --model_name gemini-1.5-flash-8b --from_pdf_path source_docs/ABN_AMRO_Bank_Q3_2024.pdf --analysis_mode smart
    
    FROM DIRECTORY OF IMAGES:
        python main.py --input_images_dir input_images --model_name gemini-1.5-pro --analysis_mode full_context
        python main.py --input_images_dir input_images --model_name gemini-1.5-flash-8b --analysis_mode smart
    """
"""
Streamlit Web Application for Supermarket Brochure AI

This application allows users to:
1. Upload brochure images or PDFs
2. Extract text and deal information using OCR
3. Visualize detected regions
4. Export structured data
"""

import streamlit as st
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json
import pandas as pd
import tempfile

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.ocr_engine import create_ocr_engine
from src.preprocessing.pdf_converter import PDFConverter
from src.preprocessing.image_processor import ImageProcessor


# Page configuration
st.set_page_config(
    page_title="Supermarket Brochure AI",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)


def draw_bboxes(image: Image.Image, results: list, show_text: bool = True) -> Image.Image:
    """
    Draw bounding boxes on image.

    Args:
        image: PIL Image
        results: List of OCR results with bbox and text
        show_text: Whether to show text labels

    Returns:
        Image with bounding boxes drawn
    """
    img_with_boxes = image.copy()
    draw = ImageDraw.Draw(img_with_boxes)

    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font = ImageFont.load_default()

    for result in results:
        bbox = result['bbox']
        text = result['text']
        confidence = result['confidence']

        # Draw rectangle
        draw.rectangle(bbox, outline='red', width=2)

        # Draw text label if requested
        if show_text and text:
            # Draw background for text
            text_bbox = draw.textbbox((bbox[0], bbox[1] - 15), text, font=font)
            draw.rectangle(text_bbox, fill='red')
            draw.text((bbox[0], bbox[1] - 15), text, fill='white', font=font)

    return img_with_boxes


def main():
    """Main application."""

    # Title and description
    st.title("🛒 Supermarket Brochure AI")
    st.markdown("""
    Upload a supermarket brochure (image or PDF) to automatically extract product information,
    prices, and deals using advanced OCR and AI technology.
    """)

    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")

    # OCR engine selection
    ocr_engine = st.sidebar.selectbox(
        "OCR Engine",
        options=['PaddleOCR', 'EasyOCR', 'Tesseract'],
        index=0,
        help="Select the OCR engine to use for text extraction"
    )

    # Language selection
    languages = st.sidebar.multiselect(
        "Languages",
        options=['de', 'en', 'fr', 'es'],
        default=['de', 'en'],
        help="Select languages to recognize"
    )

    # GPU toggle
    use_gpu = st.sidebar.checkbox(
        "Use GPU",
        value=False,
        help="Enable GPU acceleration (if available)"
    )

    # Visualization options
    st.sidebar.header("📊 Visualization")
    show_bbox = st.sidebar.checkbox("Show bounding boxes", value=True)
    show_text = st.sidebar.checkbox("Show text labels", value=True)
    confidence_threshold = st.sidebar.slider(
        "Confidence threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
        help="Filter results by confidence score"
    )

    # File upload
    st.header("📤 Upload Brochure")
    uploaded_file = st.file_uploader(
        "Choose a brochure file",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        help="Upload a brochure image or PDF file"
    )

    if uploaded_file is not None:
        # Determine file type
        file_type = uploaded_file.type

        with st.spinner("Processing file..."):
            # Handle PDF
            if file_type == 'application/pdf':
                st.info("📄 PDF detected. Converting to images...")

                # Save PDF to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                    tmp_pdf.write(uploaded_file.getbuffer())
                    tmp_pdf_path = Path(tmp_pdf.name)

                # Convert PDF to images
                converter = PDFConverter(output_dir=tempfile.gettempdir())
                image_paths = converter.convert_pdf(tmp_pdf_path)

                if not image_paths:
                    st.error("Failed to convert PDF to images.")
                    return

                st.success(f"✅ Converted PDF to {len(image_paths)} page(s)")

                # Process first page for demo
                image_path = image_paths[0]
                image = Image.open(image_path)

            else:
                # Handle image
                image = Image.open(uploaded_file)

        # Display original image
        st.header("🖼️ Original Brochure")
        col1, col2 = st.columns([1, 1])

        with col1:
            st.image(image, caption="Uploaded Brochure", use_container_width=True)

        # Run OCR
        with st.spinner(f"Extracting text using {ocr_engine}..."):
            try:
                # Create OCR engine
                ocr = create_ocr_engine(
                    engine_type=ocr_engine.lower(),
                    languages=languages,
                    use_gpu=use_gpu,
                    gpu=use_gpu
                )

                # Extract text
                results = ocr.extract_text(image)

                # Filter by confidence
                filtered_results = [
                    r for r in results
                    if r['confidence'] >= confidence_threshold
                ]

                st.success(f"✅ Extracted {len(filtered_results)} text regions (filtered from {len(results)})")

            except Exception as e:
                st.error(f"OCR extraction failed: {e}")
                return

        # Display results with bounding boxes
        with col2:
            if show_bbox and filtered_results:
                img_with_boxes = draw_bboxes(image, filtered_results, show_text=show_text)
                st.image(img_with_boxes, caption="Detected Regions", use_container_width=True)
            else:
                st.info("Enable 'Show bounding boxes' in the sidebar to visualize detected regions.")

        # Display extracted text
        st.header("📝 Extracted Text")

        if filtered_results:
            # Create DataFrame
            df = pd.DataFrame([
                {
                    'Text': r['text'],
                    'Confidence': f"{r['confidence']:.2%}",
                    'BBox': f"[{r['bbox'][0]}, {r['bbox'][1]}, {r['bbox'][2]}, {r['bbox'][3]}]"
                }
                for r in filtered_results
            ])

            st.dataframe(df, use_container_width=True)

            # Export options
            st.header("💾 Export Data")

            col1, col2, col3 = st.columns(3)

            with col1:
                # Export as JSON
                json_data = json.dumps(filtered_results, indent=2, ensure_ascii=False)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name="brochure_data.json",
                    mime="application/json"
                )

            with col2:
                # Export as CSV
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name="brochure_data.csv",
                    mime="text/csv"
                )

            with col3:
                # Export as Text
                text_data = "\n".join([r['text'] for r in filtered_results])
                st.download_button(
                    label="📥 Download TXT",
                    data=text_data,
                    file_name="brochure_text.txt",
                    mime="text/plain"
                )

            # Statistics
            st.header("📈 Statistics")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Regions", len(results))

            with col2:
                st.metric("After Filtering", len(filtered_results))

            with col3:
                avg_confidence = sum(r['confidence'] for r in filtered_results) / len(filtered_results)
                st.metric("Avg Confidence", f"{avg_confidence:.2%}")

            with col4:
                total_chars = sum(len(r['text']) for r in filtered_results)
                st.metric("Total Characters", total_chars)

        else:
            st.warning("No text regions found. Try adjusting the confidence threshold or use a different OCR engine.")

    else:
        # Show instructions when no file is uploaded
        st.info("""
        👆 Please upload a brochure file to get started.

        **Supported formats:**
        - Images: PNG, JPG, JPEG
        - Documents: PDF

        **Features:**
        - Automatic text extraction with multiple OCR engines
        - Bounding box visualization
        - Structured data export (JSON, CSV, TXT)
        - Multi-language support
        """)

        # Show example
        st.header("📸 Example")
        st.markdown("""
        Here's what you can expect:
        1. Upload a brochure image or PDF
        2. The AI will detect and extract text regions
        3. Visualize detected regions with bounding boxes
        4. Export structured data for further analysis
        """)


if __name__ == '__main__':
    main()

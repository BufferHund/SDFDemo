"""
Enhanced Streamlit Web Application for Supermarket Brochure AI

Features:
- Multi-tab interface (Single/Batch/Compare)
- Pipeline integration (OCR/VLM/Hybrid)
- Real-time processing with progress
- Visual deal highlighting
- Batch processing with reports
- Interactive configuration
"""

import streamlit as st
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json
import pandas as pd
import tempfile
from datetime import datetime
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline import create_pipeline, PipelineConfig, ProcessingMethod, BatchProcessor

# Page configuration
st.set_page_config(
    page_title="Supermarket Brochure AI - Enhanced",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.deal-card {
    background-color: #f0f2f6;
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
    border-left: 5px solid #1f77b4;
}
.price-tag {
    font-size: 24px;
    font-weight: bold;
    color: #e74c3c;
}
.product-name {
    font-size: 18px;
    font-weight: 600;
    color: #2c3e50;
}
.discount-badge {
    background-color: #2ecc71;
    color: white;
    padding: 5px 10px;
    border-radius: 5px;
    font-weight: bold;
}
.metric-card {
    text-align: center;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)


def draw_deals_on_image(image: Image.Image, deals: list) -> Image.Image:
    """Draw highlighted deals on image."""
    img_with_deals = image.copy()
    draw = ImageDraw.Draw(img_with_deals, 'RGBA')

    # Try to load font
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw each deal
    for i, deal in enumerate(deals, 1):
        # Calculate position (top-left area)
        y_pos = 20 + (i-1) * 80
        x_pos = 20

        # Deal box
        box_width = 400
        box_height = 70

        # Background with transparency
        draw.rectangle(
            [(x_pos, y_pos), (x_pos + box_width, y_pos + box_height)],
            fill=(0, 0, 0, 180)
        )

        # Product name
        product_name = deal.get('product_name', 'Unknown Product')[:30]
        draw.text((x_pos + 10, y_pos + 5), product_name, fill='white', font=font_small)

        # Price
        price = deal.get('discounted_price', '?')
        price_text = f"€{price}"
        draw.text((x_pos + 10, y_pos + 35), price_text, fill='#2ecc71', font=font_large)

        # Discount badge
        discount = deal.get('discount_percentage')
        if discount:
            discount_text = f"-{discount}%"
            # Badge background
            badge_x = x_pos + box_width - 80
            draw.rectangle(
                [(badge_x, y_pos + 35), (badge_x + 70, y_pos + 65)],
                fill=(231, 76, 60, 255)
            )
            draw.text((badge_x + 5, y_pos + 38), discount_text, fill='white', font=font_small)

    return img_with_deals


def display_deal_card(deal: dict, index: int):
    """Display a single deal as a card."""
    product_name = deal.get('product_name', 'Unknown Product')
    discounted_price = deal.get('discounted_price', 'N/A')
    original_price = deal.get('original_price')
    discount_percentage = deal.get('discount_percentage')
    valid_from = deal.get('valid_from', '')
    valid_to = deal.get('valid_to', '')

    html = f"""
    <div class="deal-card">
        <div class="product-name">🏷️ {product_name}</div>
        <div style="margin: 10px 0;">
            <span class="price-tag">€{discounted_price}</span>
    """

    if original_price:
        html += f'<span style="text-decoration: line-through; color: #95a5a6; margin-left: 10px;">€{original_price}</span>'

    if discount_percentage:
        html += f'<span class="discount-badge" style="margin-left: 10px;">-{discount_percentage}%</span>'

    html += "</div>"

    if valid_from or valid_to:
        validity = ""
        if valid_from:
            validity += f"From: {valid_from}"
        if valid_to:
            validity += f" To: {valid_to}" if valid_from else f"Until: {valid_to}"
        html += f'<div style="color: #7f8c8d; font-size: 14px;">📅 {validity}</div>'

    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)


def single_file_tab():
    """Single file processing tab."""
    st.header("📄 Single File Processing")

    # Configuration in columns
    col1, col2, col3 = st.columns(3)

    with col1:
        method = st.selectbox(
            "Processing Method",
            options=['Hybrid', 'OCR', 'VLM'],
            help="Hybrid: Best accuracy | OCR: Fastest | VLM: Best understanding"
        )

    with col2:
        ocr_engine = st.selectbox(
            "OCR Engine",
            options=['paddleocr', 'tesseract', 'easyocr'],
            help="OCR engine for text extraction"
        )

    with col3:
        vlm_engine = st.selectbox(
            "VLM Engine",
            options=['ollama', 'gemini'],
            help="Vision Language Model engine"
        )

    # Advanced settings
    with st.expander("⚙️ Advanced Settings"):
        col1, col2 = st.columns(2)
        with col1:
            use_gpu = st.checkbox("Use GPU for OCR", value=False)
            preprocess = st.checkbox("Preprocess Images", value=True)
        with col2:
            save_viz = st.checkbox("Save Visualizations", value=True)
            vlm_model = st.text_input("VLM Model", value="llava:latest")

    # File upload
    uploaded_file = st.file_uploader(
        "📤 Upload Brochure",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        help="Upload a brochure image or PDF file"
    )

    if uploaded_file:
        # Display original
        st.subheader("Original Brochure")

        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_path = Path(tmp_file.name)

        # Show original image
        if uploaded_file.type != 'application/pdf':
            original_image = Image.open(tmp_path)
            st.image(original_image, use_container_width=True)
        else:
            st.info("📄 PDF file uploaded. Will be converted during processing.")

        # Process button
        if st.button("🚀 Process Brochure", type="primary", use_container_width=True):
            # Create progress containers
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # Create pipeline
                status_text.text("⚙️ Initializing pipeline...")
                progress_bar.progress(10)

                pipeline = create_pipeline(
                    method=method.lower(),
                    ocr_engine=ocr_engine,
                    vlm_engine=vlm_engine,
                    vlm_model=vlm_model,
                    ocr_use_gpu=use_gpu,
                    preprocess_images=preprocess,
                    save_visualizations=save_viz,
                    output_dir=tempfile.gettempdir()
                )

                progress_bar.progress(20)

                # Process
                status_text.text(f"🔄 Processing with {method} method...")
                progress_bar.progress(30)

                start_time = time.time()
                result = pipeline.process(tmp_path)
                processing_time = time.time() - start_time

                progress_bar.progress(100)
                status_text.text("✅ Processing complete!")

                if result.success:
                    # Display results
                    st.success(f"✅ Successfully processed in {processing_time:.2f}s")

                    # Metrics
                    st.subheader("📊 Results Summary")
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Deals Found", len(result.deals))
                    with col2:
                        st.metric("Processing Time", f"{processing_time:.2f}s")
                    with col3:
                        st.metric("Method", method)
                    with col4:
                        total_savings = sum(
                            (deal.get('original_price', 0) or 0) - (deal.get('discounted_price', 0) or 0)
                            for deal in result.deals
                            if deal.get('original_price') and deal.get('discounted_price')
                        )
                        st.metric("Total Savings", f"€{total_savings:.2f}" if total_savings > 0 else "N/A")

                    # Display results in two columns
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        st.subheader("🖼️ Highlighted Deals")
                        if uploaded_file.type != 'application/pdf':
                            highlighted_image = draw_deals_on_image(original_image, result.deals)
                            st.image(highlighted_image, use_container_width=True)
                        else:
                            st.info("Visualization available for image files")

                    with col2:
                        st.subheader("📋 Extracted Deals")
                        if result.deals:
                            for i, deal in enumerate(result.deals):
                                display_deal_card(deal, i)
                        else:
                            st.warning("No deals found in this brochure.")

                    # Export options
                    st.subheader("💾 Export Results")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        json_data = json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
                        st.download_button(
                            "📥 Download JSON",
                            data=json_data,
                            file_name=f"deals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )

                    with col2:
                        if result.deals:
                            df = pd.DataFrame(result.deals)
                            csv_data = df.to_csv(index=False)
                            st.download_button(
                                "📥 Download CSV",
                                data=csv_data,
                                file_name=f"deals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )

                    with col3:
                        # Summary report
                        report = f"""Brochure Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Method: {method}
Processing Time: {processing_time:.2f}s
Deals Found: {len(result.deals)}

Deals:
"""
                        for i, deal in enumerate(result.deals, 1):
                            report += f"\n{i}. {deal.get('product_name', 'Unknown')}"
                            report += f"\n   Price: €{deal.get('discounted_price', 'N/A')}"
                            if deal.get('discount_percentage'):
                                report += f" (-{deal['discount_percentage']}%)"
                            report += "\n"

                        st.download_button(
                            "📥 Download Report",
                            data=report,
                            file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )

                else:
                    st.error(f"❌ Processing failed: {result.error}")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)

            finally:
                # Cleanup
                if tmp_path.exists():
                    tmp_path.unlink()


def batch_processing_tab():
    """Batch processing tab."""
    st.header("📦 Batch Processing")

    st.info("""
    Upload multiple brochures to process them in parallel.
    The system will generate a comprehensive report with all extracted deals.
    """)

    # Configuration
    col1, col2, col3 = st.columns(3)

    with col1:
        method = st.selectbox(
            "Processing Method",
            options=['Hybrid', 'OCR', 'VLM'],
            key='batch_method'
        )

    with col2:
        max_workers = st.slider("Parallel Workers", 1, 8, 4)

    with col3:
        generate_report = st.checkbox("Generate Report", value=True)

    # File upload (multiple)
    uploaded_files = st.file_uploader(
        "📤 Upload Brochures (multiple files)",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        accept_multiple_files=True,
        help="Upload multiple brochure files for batch processing"
    )

    if uploaded_files:
        st.write(f"📁 {len(uploaded_files)} files uploaded")

        # Show file list
        with st.expander("📋 View uploaded files"):
            for f in uploaded_files:
                st.text(f"• {f.name} ({f.size / 1024:.1f} KB)")

        if st.button("🚀 Process All Files", type="primary", use_container_width=True):
            # Create temp directory for files
            temp_dir = Path(tempfile.mkdtemp())
            file_paths = []

            # Save all files
            for uploaded_file in uploaded_files:
                file_path = temp_dir / uploaded_file.name
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                file_paths.append(file_path)

            # Create batch processor
            config = PipelineConfig(
                method=ProcessingMethod(method.lower()),
                output_dir=str(temp_dir / "outputs")
            )

            processor = BatchProcessor(config=config, max_workers=max_workers)

            # Progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_container = st.container()

            try:
                status_text.text("🔄 Processing files...")

                # Process
                batch_result = processor.process(file_paths, show_progress=False)

                # Update progress
                for i, file_result in enumerate(batch_result.results):
                    progress = int((i + 1) / len(batch_result.results) * 100)
                    progress_bar.progress(progress)
                    status_text.text(f"Processed {i+1}/{len(batch_result.results)} files...")

                # Complete
                status_text.text("✅ Batch processing complete!")

                # Display results
                st.success(f"✅ Processed {batch_result.successful}/{batch_result.total} files successfully")

                # Metrics
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Total Files", batch_result.total)
                with col2:
                    st.metric("Successful", batch_result.successful)
                with col3:
                    st.metric("Failed", batch_result.failed)
                with col4:
                    st.metric("Success Rate", f"{batch_result.success_rate:.1f}%")

                # Processing time metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Time", f"{batch_result.total_time:.2f}s")
                with col2:
                    st.metric("Avg Time/File", f"{batch_result.avg_time:.2f}s")
                with col3:
                    total_deals = sum(len(r.deals) for r in batch_result.results if r.success)
                    st.metric("Total Deals", total_deals)

                # Show individual results
                st.subheader("📋 Individual Results")

                for i, file_result in enumerate(batch_result.results):
                    with st.expander(f"{'✅' if file_result.success else '❌'} {Path(file_result.input_path).name}"):
                        if file_result.success:
                            st.write(f"⏱️ Processing time: {file_result.processing_time:.2f}s")
                            st.write(f"🏷️ Deals found: {len(file_result.deals)}")

                            if file_result.deals:
                                for deal in file_result.deals:
                                    display_deal_card(deal, 0)
                        else:
                            st.error(f"Error: {file_result.error}")

                # Export aggregated results
                if generate_report and batch_result.successful > 0:
                    st.subheader("💾 Export Results")

                    # Generate report
                    report_dir = temp_dir / "report"
                    processor.generate_report(batch_result, report_dir)

                    # Read summary
                    if (report_dir / "summary.json").exists():
                        with open(report_dir / "summary.json") as f:
                            summary = json.load(f)

                        col1, col2 = st.columns(2)

                        with col1:
                            st.download_button(
                                "📥 Download Summary (JSON)",
                                data=json.dumps(summary, indent=2),
                                file_name="batch_summary.json",
                                mime="application/json"
                            )

                        with col2:
                            # Read all deals
                            if (report_dir / "all_deals.json").exists():
                                with open(report_dir / "all_deals.json") as f:
                                    all_deals = json.load(f)

                                df = pd.DataFrame(all_deals)
                                csv_data = df.to_csv(index=False)

                                st.download_button(
                                    "📥 Download All Deals (CSV)",
                                    data=csv_data,
                                    file_name="all_deals.csv",
                                    mime="text/csv"
                                )

            except Exception as e:
                st.error(f"❌ Batch processing failed: {str(e)}")
                st.exception(e)


def comparison_tab():
    """Method comparison tab."""
    st.header("⚖️ Method Comparison")

    st.info("""
    Compare different processing methods (OCR vs VLM vs Hybrid) on the same brochure.
    This helps you understand the strengths and trade-offs of each approach.
    """)

    # File upload
    uploaded_file = st.file_uploader(
        "📤 Upload Brochure for Comparison",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        key='compare_upload'
    )

    if uploaded_file:
        # Save to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_path = Path(tmp_file.name)

        if st.button("🔬 Run Comparison", type="primary", use_container_width=True):
            methods = ['ocr', 'vlm', 'hybrid']
            results = {}

            progress_bar = st.progress(0)
            status_text = st.empty()

            # Run each method
            for i, method in enumerate(methods):
                status_text.text(f"Running {method.upper()} method...")

                try:
                    pipeline = create_pipeline(
                        method=method,
                        output_dir=tempfile.gettempdir()
                    )

                    result = pipeline.process(tmp_path)
                    results[method] = result

                except Exception as e:
                    st.error(f"{method.upper()} failed: {str(e)}")
                    results[method] = None

                progress_bar.progress(int((i + 1) / len(methods) * 100))

            status_text.text("✅ Comparison complete!")

            # Display comparison
            st.subheader("📊 Comparison Results")

            # Metrics comparison
            col1, col2, col3 = st.columns(3)

            for col, method in zip([col1, col2, col3], methods):
                with col:
                    st.markdown(f"### {method.upper()}")

                    if results[method] and results[method].success:
                        r = results[method]
                        st.metric("Deals Found", len(r.deals))
                        st.metric("Time", f"{r.processing_time:.2f}s")
                        st.metric("Status", "✅ Success")
                    else:
                        st.metric("Status", "❌ Failed")

            # Detailed comparison
            st.subheader("🔍 Detailed Comparison")

            for method in methods:
                if results[method] and results[method].success:
                    with st.expander(f"📋 {method.upper()} Results ({len(results[method].deals)} deals)"):
                        for deal in results[method].deals:
                            display_deal_card(deal, 0)


def main():
    """Main application."""

    # Header
    st.title("🛒 Supermarket Brochure AI - Enhanced Interface")
    st.markdown("""
    Advanced brochure analysis with multiple processing methods, batch processing, and comparison tools.
    """)

    # Sidebar
    st.sidebar.title("ℹ️ About")
    st.sidebar.info("""
    **Features:**
    - 🔄 Three processing methods
    - 📦 Batch processing
    - ⚖️ Method comparison
    - 🎨 Visual deal highlighting
    - 📊 Detailed analytics
    - 💾 Multiple export formats
    """)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📖 Processing Methods")
    st.sidebar.markdown("""
    **OCR**: Fast text extraction
    - ⚡ Fastest processing
    - 💻 Works offline
    - 📝 Text-based

    **VLM**: AI-powered analysis
    - 🧠 Semantic understanding
    - 🎯 High accuracy
    - 🌐 Requires server/API

    **Hybrid**: Best of both
    - ✨ Optimal accuracy
    - 🔄 Combined approach
    - 🏆 Recommended
    """)

    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📄 Single File", "📦 Batch Processing", "⚖️ Compare Methods"])

    with tab1:
        single_file_tab()

    with tab2:
        batch_processing_tab()

    with tab3:
        comparison_tab()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #7f8c8d;">
        Built with Streamlit • Powered by PaddleOCR, Ollama, and Gemini
    </div>
    """, unsafe_allow_html=True)


if __name__ == '__main__':
    main()

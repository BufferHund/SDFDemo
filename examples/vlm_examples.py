"""
Vision Language Model Examples

This script demonstrates the use of VLM for brochure analysis.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.vlm_engine import create_vlm_engine
from src.models.ocr_engine import create_ocr_engine
import json


def example_ollama_basic():
    """Basic Ollama usage example."""
    print("=== Example 1: Basic Ollama Usage ===\n")

    # Create VLM
    vlm = create_vlm_engine('ollama', model_name='llava:latest')

    # Analyze image (replace with your image path)
    image_path = 'path/to/brochure.png'

    # Uncomment when you have an image:
    # result = vlm.analyze_image(image_path)
    #
    # print(f"Found {len(result['deals'])} deals:\n")
    # for i, deal in enumerate(result['deals'], 1):
    #     print(f"{i}. {deal['product_name']}")
    #     print(f"   Price: €{deal.get('discounted_price', 'N/A')}")
    #     print()

    print("(Replace image_path with actual brochure image)\n")


def example_gemini_basic():
    """Basic Gemini usage example."""
    print("=== Example 2: Basic Gemini Usage ===\n")

    import os

    # Set API key
    # os.environ['GEMINI_API_KEY'] = 'your-api-key-here'

    # Create VLM
    # vlm = create_vlm_engine('gemini', model_name='gemini-1.5-flash')
    #
    # result = vlm.analyze_image('brochure.png')
    # print(json.dumps(result, indent=2))

    print("(Set GEMINI_API_KEY environment variable first)\n")


def example_custom_prompt():
    """Custom prompt example."""
    print("=== Example 3: Custom Prompt ===\n")

    vlm = create_vlm_engine('ollama')

    custom_prompt = """
    Look at this supermarket brochure and extract:
    1. All fresh produce items with prices
    2. Any "buy one get one free" offers
    3. Weekly specials

    Format as JSON.
    """

    # result = vlm.analyze_image('brochure.png', prompt=custom_prompt)
    # print(json.dumps(result, indent=2))

    print("(Custom prompts allow targeted extraction)\n")


def example_comparison():
    """Compare OCR vs VLM."""
    print("=== Example 4: OCR vs VLM Comparison ===\n")

    image_path = 'brochure.png'

    # Method 1: Traditional OCR
    print("Method 1: PaddleOCR")
    print("-" * 40)
    ocr = create_ocr_engine('paddleocr')
    # ocr_results = ocr.extract_text(image_path)
    # print(f"Extracted {len(ocr_results)} text regions")
    # print("(Needs post-processing to find prices)\n")

    # Method 2: Ollama VLM
    print("Method 2: Ollama VLM")
    print("-" * 40)
    ollama = create_vlm_engine('ollama')
    # ollama_result = ollama.analyze_image(image_path)
    # print(f"Found {len(ollama_result.get('deals', []))} structured deals")
    # print("(Direct JSON output, no post-processing)\n")

    # Method 3: Gemini VLM
    print("Method 3: Gemini VLM")
    print("-" * 40)
    # gemini = create_vlm_engine('gemini')
    # gemini_result = gemini.analyze_image(image_path)
    # print(f"Found {len(gemini_result.get('deals', []))} structured deals")
    # print("(Cloud API, very fast)\n")

    print("(Each method has tradeoffs in speed, cost, and accuracy)\n")


def example_hybrid_approach():
    """Hybrid OCR + VLM approach."""
    print("=== Example 5: Hybrid Approach (Best) ===\n")

    image_path = 'brochure.png'

    # Step 1: Use OCR for precise text detection
    print("Step 1: OCR for text detection...")
    ocr = create_ocr_engine('paddleocr')
    # ocr_results = ocr.extract_text(image_path)
    # print(f"Detected {len(ocr_results)} text regions with bounding boxes")

    # Step 2: Use VLM for semantic understanding
    print("\nStep 2: VLM for semantic understanding...")
    vlm = create_vlm_engine('ollama')
    # vlm_results = vlm.analyze_image(image_path)
    # print(f"Extracted {len(vlm_results.get('deals', []))} deals with context")

    # Step 3: Combine results
    print("\nStep 3: Combine for best results")
    print("- OCR provides precise locations")
    print("- VLM provides semantic understanding")
    print("- Combined: accurate + structured\n")


def example_batch_processing():
    """Batch process multiple brochures."""
    print("=== Example 6: Batch Processing ===\n")

    from pathlib import Path
    import time

    brochure_dir = Path('data/processed/images')

    if not brochure_dir.exists():
        print(f"Directory not found: {brochure_dir}")
        return

    # Get all images
    images = list(brochure_dir.glob('*.png'))
    print(f"Found {len(images)} brochures to process\n")

    # Create VLM
    vlm = create_vlm_engine('ollama')

    results = {}

    for i, image_path in enumerate(images[:5], 1):  # Process first 5
        print(f"Processing {i}/{len(images[:5])}: {image_path.name}")
        start = time.time()

        # Analyze
        # result = vlm.analyze_image(str(image_path))
        # results[image_path.name] = result

        # print(f"  Found {len(result.get('deals', []))} deals")
        # print(f"  Time: {time.time() - start:.2f}s\n")

    # Save all results
    # with open('batch_results.json', 'w') as f:
    #     json.dump(results, f, indent=2)

    print("(Batch processing complete)\n")


def example_error_handling():
    """Proper error handling."""
    print("=== Example 7: Error Handling ===\n")

    def analyze_with_fallback(image_path):
        """Analyze with automatic fallback."""

        # Try Ollama first
        try:
            print("Trying Ollama...")
            vlm = create_vlm_engine('ollama')
            result = vlm.analyze_image(image_path)

            if result.get('deals'):
                print(f"✓ Ollama success: {len(result['deals'])} deals")
                return result

        except Exception as e:
            print(f"✗ Ollama failed: {e}")

        # Fallback to Gemini
        try:
            print("Trying Gemini...")
            vlm = create_vlm_engine('gemini')
            result = vlm.analyze_image(image_path)

            if result.get('deals'):
                print(f"✓ Gemini success: {len(result['deals'])} deals")
                return result

        except Exception as e:
            print(f"✗ Gemini failed: {e}")

        # Final fallback: OCR
        print("Falling back to OCR...")
        ocr = create_ocr_engine('paddleocr')
        ocr_result = ocr.extract_text(image_path)

        from src.models.entity_extractor import EntityExtractor
        extractor = EntityExtractor()
        deals = extractor.extract_from_ocr(ocr_result)

        print(f"✓ OCR success: {len(deals)} deals")
        return {'deals': [d.to_dict() for d in deals]}

    # result = analyze_with_fallback('brochure.png')

    print("(Robust error handling ensures results)\n")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print(" Vision Language Model (VLM) Examples")
    print("=" * 80 + "\n")

    examples = [
        ("Basic Ollama Usage", example_ollama_basic),
        ("Basic Gemini Usage", example_gemini_basic),
        ("Custom Prompts", example_custom_prompt),
        ("OCR vs VLM Comparison", example_comparison),
        ("Hybrid Approach", example_hybrid_approach),
        ("Batch Processing", example_batch_processing),
        ("Error Handling", example_error_handling),
    ]

    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"Error in {name}: {e}\n")

    print("=" * 80)
    print("To run these examples with real data:")
    print("1. Install Ollama: https://ollama.ai/")
    print("2. Pull a model: ollama pull llava")
    print("3. Start server: ollama serve")
    print("4. Replace 'brochure.png' with your image path")
    print("5. Uncomment the code blocks")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()

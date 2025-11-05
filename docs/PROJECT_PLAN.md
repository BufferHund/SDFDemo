# Project Development Plan

## 8-Week Timeline for Supermarket Brochure AI

This document outlines the detailed development plan for the Supermarket Brochure AI project, organized by weekly milestones.

---

## Week 1: Project Setup & Data Collection Planning

### Goals
- Establish project infrastructure
- Set up development environment
- Begin collecting brochure samples
- Design data organization structure

### Tasks

#### Day 1-2: Environment Setup
- [x] Create project repository
- [x] Set up directory structure
- [x] Create README and documentation
- [x] Initialize version control
- [ ] Set up virtual environment
- [ ] Install dependencies
- [ ] Configure IDE/editor

#### Day 3-4: Data Collection Planning
- [ ] Research supermarket websites
- [ ] Document URL patterns and structures
- [ ] Plan scraping strategies
- [ ] Design metadata schema
- [ ] Create data collection scripts

#### Day 5-7: Initial Data Collection
- [ ] Implement web scrapers for:
  - [ ] Aldi Süd
  - [ ] Aldi Nord
  - [ ] REWE
  - [ ] Edeka
  - [ ] (Optional) Lidl, Penny
- [ ] Download 10-20 sample brochures
- [ ] Organize raw data in structured folders

### Deliverables
- ✅ Project repository with clear structure
- ✅ README with project description
- ✅ Data collection scripts
- [ ] 10-20 raw brochure samples (PDFs/images)
- [ ] Metadata files for collected samples

---

## Week 2: Data Collection & Initial Preprocessing

### Goals
- Expand brochure dataset
- Implement preprocessing pipeline
- Run initial OCR experiments
- Identify data quality issues

### Tasks

#### Day 1-2: Continued Data Collection
- [ ] Run scrapers to collect more brochures
- [ ] Target: 50-100 brochure pages
- [ ] Document data sources and dates
- [ ] Check for format variations

#### Day 3-4: Preprocessing Implementation
- [ ] Implement PDF to image converter
- [ ] Create image standardization pipeline
- [ ] Test with different DPI settings
- [ ] Benchmark conversion quality
- [ ] Process all collected PDFs

#### Day 5-7: OCR Exploration
- [ ] Set up OCR engines (Tesseract, PaddleOCR, EasyOCR)
- [ ] Run comparative tests on sample brochures
- [ ] Evaluate OCR accuracy by engine
- [ ] Identify common OCR errors:
  - Price symbol recognition
  - Font variations
  - Distorted text
  - Multi-column layouts
- [ ] Document OCR error patterns

### Deliverables
- [ ] 50-100 cleaned brochure images
- [ ] Preprocessing scripts that standardize images
- [ ] OCR comparison report
- [ ] Error pattern documentation

---

## Week 3: Data Annotation & Standardization

### Goals
- Manually annotate training samples
- Define annotation schema
- Create annotation guidelines
- Evaluate OCR baseline accuracy

### Tasks

#### Day 1-2: Annotation Schema Design
- [ ] Define entity types:
  - Product name
  - Original price
  - Discounted price
  - Discount percentage
  - Valid dates
  - Store location (if available)
- [ ] Design JSON annotation format
- [ ] Create annotation guidelines document
- [ ] Set up annotation tool (LabelStudio, CVAT, or custom)

#### Day 3-6: Manual Annotation
- [ ] Select 10-15 diverse brochure pages
- [ ] Annotate bounding boxes and labels
- [ ] Record annotation time per page
- [ ] Validate annotations for consistency
- [ ] Create train/validation/test splits

#### Day 7: Baseline Evaluation
- [ ] Run OCR on annotated samples
- [ ] Calculate baseline metrics:
  - Text recognition accuracy
  - Entity detection rate
  - Bbox alignment quality
- [ ] Analyze error cases
- [ ] Document improvement opportunities

### Deliverables
- [ ] JSON annotation schema specification
- [ ] Annotation guidelines document
- [ ] 10-15 fully annotated brochure pages
- [ ] Train/val/test data splits
- [ ] Baseline evaluation report

---

## Week 4: Model Selection & Environment Setup

### Goals
- Research and select extraction models
- Set up training infrastructure
- Configure GPU environment
- Design model pipeline

### Tasks

#### Day 1-2: Model Research
- [ ] Review state-of-the-art models:
  - LayoutLMv3 (multimodal document understanding)
  - Donut (OCR-free transformer)
  - LayoutXLM (multilingual)
  - Pix2Struct (image-to-structure)
- [ ] Compare model characteristics:
  - Input requirements
  - Training complexity
  - Inference speed
  - Memory requirements
- [ ] Select primary model: **LayoutLMv3** (recommended)
- [ ] Select backup model: **Donut**

#### Day 3-4: Training Environment Setup
- [ ] Set up GPU environment:
  - Check CUDA availability
  - Install PyTorch with CUDA
  - Verify GPU memory
- [ ] Configure training tools:
  - Weights & Biases for logging
  - TensorBoard for visualization
  - Hydra for configuration management
- [ ] Test model loading and basic inference

#### Day 5-7: Pipeline Design
- [ ] Design end-to-end pipeline:
  1. Image preprocessing
  2. OCR text extraction
  3. Layout analysis
  4. Entity recognition
  5. Post-processing
- [ ] Implement data loaders
- [ ] Create training/validation loops
- [ ] Set up checkpointing
- [ ] Configure evaluation metrics

### Deliverables
- [ ] Model selection report with justification
- [ ] Fully configured training environment
- [ ] Training pipeline (v1)
- [ ] Data loader implementations
- [ ] Configuration files for experiments

---

## Week 5: Model Fine-tuning

### Goals
- Fine-tune selected model on annotated data
- Apply PEFT techniques
- Optimize hyperparameters
- Monitor training progress

### Tasks

#### Day 1-2: PEFT Setup
- [ ] Implement LoRA (Low-Rank Adaptation):
  - Configure rank (r=16 recommended)
  - Set alpha parameter (α=32)
  - Select target modules
- [ ] Test PEFT vs full fine-tuning
- [ ] Compare memory usage and speed

#### Day 3-5: Initial Training
- [ ] Start training with baseline hyperparameters:
  - Learning rate: 5e-5
  - Batch size: 4-8
  - Epochs: 10-20
  - Warmup steps: 500
- [ ] Monitor training metrics:
  - Loss curves
  - Validation accuracy
  - Entity F1 scores
- [ ] Adjust hyperparameters based on initial results

#### Day 6-7: Optimization
- [ ] Implement data augmentation:
  - Rotation
  - Brightness/contrast adjustment
  - Noise injection
  - Synthetic examples
- [ ] Experiment with:
  - Different learning rate schedules
  - Batch sizes
  - Gradient accumulation
- [ ] Save best checkpoints

### Deliverables
- [ ] Fine-tuned model (v1)
- [ ] Training logs and curves
- [ ] Hyperparameter tuning report
- [ ] Best model checkpoints

---

## Week 6: Evaluation & Refinement

### Goals
- Comprehensively evaluate model performance
- Conduct error analysis
- Iterate improvements
- Achieve target accuracy

### Tasks

#### Day 1-2: Quantitative Evaluation
- [ ] Evaluate on test set:
  - **F1 Score** for each entity type
  - **Precision** and **Recall**
  - **mAP** (mean Average Precision) for detection
  - **Exact Match** for prices
- [ ] Compare against baseline (pure OCR)
- [ ] Benchmark inference speed

#### Day 3-4: Error Analysis
- [ ] Categorize errors:
  - Missed detections (false negatives)
  - False detections (false positives)
  - Incorrect entity types
  - Bbox misalignment
  - OCR errors propagated to model
- [ ] Identify problematic cases:
  - Small fonts
  - Unusual layouts
  - Overlapping text regions
  - Low-quality images

#### Day 5-7: Iterative Improvements
- [ ] Address top error categories:
  - Collect more examples of problematic cases
  - Add targeted augmentations
  - Adjust post-processing heuristics
  - Fine-tune on hard examples
- [ ] Re-train improved model (v2)
- [ ] Re-evaluate and compare

### Deliverables
- [ ] Comprehensive evaluation report
- [ ] Error analysis with visualizations
- [ ] Improved model (v2)
- [ ] Recommendations for future work

---

## Week 7: Application Prototyping

### Goals
- Develop user-facing web application
- Implement visualization features
- Add export functionality
- Create demo-ready prototype

### Tasks

#### Day 1-2: UI Design & Setup
- [ ] Design user interface:
  - File upload component
  - Image display with bboxes
  - Results table
  - Export options
- [ ] Choose framework:
  - Streamlit (recommended for rapid prototyping)
  - Gradio (alternative)
  - Flask + React (for production)
- [ ] Implement basic upload and display

#### Day 3-4: Backend Integration
- [ ] Integrate preprocessing pipeline
- [ ] Connect OCR engine
- [ ] Load fine-tuned model
- [ ] Implement inference endpoint
- [ ] Add result visualization:
  - Draw bounding boxes on image
  - Color-code by entity type
  - Show confidence scores

#### Day 5-6: Export & Features
- [ ] Implement export formats:
  - JSON (structured data)
  - CSV (tabular format)
  - HTML (report)
- [ ] Add filtering options:
  - Confidence threshold
  - Entity type selection
- [ ] (Optional) Add recommendation feature:
  - Identify best deals
  - Compare prices across stores

#### Day 7: Testing & Polish
- [ ] Test with various brochure types
- [ ] Handle edge cases gracefully
- [ ] Add loading indicators
- [ ] Improve UI/UX
- [ ] Write user documentation

### Deliverables
- [ ] Functional web application (v1)
- [ ] Visualization of detected regions
- [ ] Structured data export
- [ ] User guide/documentation
- [ ] Demo video or screenshots

---

## Week 8: Integration, Testing & Presentation

### Goals
- Finalize end-to-end system
- Conduct thorough testing
- Prepare presentation materials
- Document project

### Tasks

#### Day 1-2: System Integration
- [ ] Connect all components:
  - Data collection → Preprocessing → Model → Application
- [ ] Create end-to-end test pipeline
- [ ] Fix integration issues
- [ ] Optimize performance bottlenecks

#### Day 3-4: Testing
- [ ] Functional testing:
  - Test all supermarket brochures
  - Verify format compatibility (PDF, images)
  - Check error handling
- [ ] Performance testing:
  - Measure processing time per page
  - Test with large files
  - Monitor memory usage
- [ ] User acceptance testing:
  - Ask classmates to test
  - Collect feedback
  - Iterate improvements

#### Day 5-6: Presentation Preparation
- [ ] Create presentation slides:
  - Problem statement
  - Methodology
  - Results and evaluation
  - Demo
  - Future work
- [ ] Prepare demo script
- [ ] Record demo video (backup)
- [ ] Create poster/infographic (optional)

#### Day 7: Final Documentation
- [ ] Complete README
- [ ] Write technical report:
  - Introduction
  - Related work
  - Methodology
  - Experiments
  - Results
  - Conclusion
- [ ] Add code documentation
- [ ] Create GitHub release
- [ ] Archive dataset and models

### Deliverables
- [ ] Complete end-to-end system
- [ ] Test results and performance benchmarks
- [ ] Presentation slides
- [ ] Demo video
- [ ] Final project report
- [ ] GitHub repository with full documentation

---

## Success Metrics

### Quantitative
- **Data Collection**: 50-100 brochure pages
- **Annotation**: 10-15 fully annotated pages
- **Model Performance**:
  - F1 Score: >0.80 for product names
  - F1 Score: >0.90 for prices
  - mAP: >0.75 for detection
- **Inference Speed**: <5 seconds per page

### Qualitative
- System handles various brochure formats
- User-friendly web interface
- Clear visualization of results
- Structured and exportable data
- Well-documented codebase

---

## Risk Management

### Potential Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Website scraping blocked | High | Use Selenium, rotate user agents, manual download |
| Insufficient labeled data | High | Use synthetic data generation, semi-supervised learning |
| OCR accuracy too low | Medium | Try multiple OCR engines, ensemble methods |
| Model overfitting | Medium | More data augmentation, regularization, PEFT |
| GPU unavailable | Low | Use Google Colab, cloud GPUs, or CPU training |
| Time constraints | High | Prioritize core features, use pre-trained models |

---

## Future Enhancements (Beyond 8 Weeks)

1. **Expand Data Coverage**
   - More supermarket chains
   - Different product categories
   - Time series data (track price changes)

2. **Advanced Features**
   - Multi-store price comparison
   - Product recommendation system
   - Deal alerts and notifications
   - Mobile application

3. **Model Improvements**
   - Fine-tune on larger dataset
   - Ensemble multiple models
   - Active learning for annotation
   - Zero-shot learning for new entity types

4. **Production Deployment**
   - Containerization (Docker)
   - API service (FastAPI)
   - Cloud deployment (AWS, Azure)
   - Scalability optimizations

---

## Resources

### Computing Resources
- Local GPU (if available)
- Google Colab (free GPU/TPU)
- University computing cluster
- AWS/Azure free tier

### Tools & Libraries
- PyTorch, Transformers, PEFT
- PaddleOCR, Tesseract, EasyOCR
- Streamlit, Gradio
- Weights & Biases, TensorBoard

### References
- [LayoutLMv3 Paper](https://arxiv.org/abs/2204.08387)
- [Donut Paper](https://arxiv.org/abs/2111.15664)
- [PEFT Documentation](https://huggingface.co/docs/peft)
- [PaddleOCR GitHub](https://github.com/PaddlePaddle/PaddleOCR)

---

## Team Responsibilities

### Weekly Meetings
- Review progress
- Discuss challenges
- Plan next steps
- Update documentation

### Task Distribution
- Liyang: [To be assigned]
- Zhaokun: [To be assigned]

### Communication
- GitHub Issues for task tracking
- Shared documentation (Google Docs/Notion)
- Regular check-ins (e.g., twice per week)

---

**Good luck with your project! 🚀**

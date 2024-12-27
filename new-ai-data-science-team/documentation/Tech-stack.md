# Technology Stack

## Core Technologies

### Programming Language
- **Python 3.10+**
  - Primary language for all components
  - Strong ML/data science ecosystem
  - Async capabilities for concurrent operations

### Container Infrastructure
- **Docker**: Application containerization
- **Docker Compose**: Multi-container orchestration

## Data Layer

### Data Collection
- **Scrapy**: Web crawling framework
- **Beautiful Soup**: HTML parsing
- **Selenium**: Dynamic content scraping
- **Schema**: Data validation
- **Great Expectations**: Data quality checks

### Data Storage
- **MongoDB**: Raw data storage
  - Used by: data/collection/mongodb_client.py
  - Purpose: Storing unstructured raw data

- **PostgreSQL**: Processed data storage
  - Used by: data/storage/postgresql_client.py
  - Purpose: Structured data storage post-processing

- **Redis**: Caching layer
  - Used by: data/storage/redis_client.py
  - Purpose: Results caching, temporary storage

## Processing Pipeline

### Data Wrangling
- **Pandas**: Data manipulation
- **NumPy**: Numerical operations
- **Dask**: Large dataset processing
- **Vaex**: Out-of-memory dataframes

### Data Cleaning
- **Pandas Profiling**: Automated data analysis
- **Imputations**: Missing data handling
- **Dedupe**: Duplicate detection

### Feature Engineering
- **Scikit-learn**: Feature transformation
- **Feature-engine**: Feature creation/selection
- **Category Encoders**: Categorical encoding

## Analysis Pipeline

### Data Analysis
- **StatsModels**: Statistical analysis
- **SciPy**: Scientific computing
- **Plotly**: Interactive visualization
- **Streamlit**: Data app creation

### ML Modeling
- **Scikit-learn**: Traditional ML algorithms
- **XGBoost**: Gradient boosting
- **LightGBM**: Gradient boosting
- **TensorFlow**: Deep learning
- **PyTorch**: Deep learning
- **Optuna**: Hyperparameter optimization

### Interpretability
- **SHAP**: Model interpretation
- **LIME**: Local interpretability
- **Alibi**: Model explanation
- **MLflow**: Experiment tracking

## Supervisor Layer

### Monitoring
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization
- **ELK Stack**: Log management
  - Elasticsearch: Log storage
  - Logstash: Log processing
  - Kibana: Log visualization

### Error Handling
- **Sentry**: Error tracking
- **Python logging**: Log generation

## Development Tools

### Testing
- **Pytest**: Unit testing
- **Hypothesis**: Property-based testing
- **Coverage.py**: Code coverage

### Code Quality
- **Black**: Code formatting
- **Flake8**: Linting
- **Mypy**: Type checking
- **Pre-commit**: Git hooks

### Documentation
- **Sphinx**: Documentation generation
- **MkDocs**: Documentation hosting
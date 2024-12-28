# AI Data Science Team

A multi-agent data pipeline system implementing automated collection, processing, analysis, and interpretation of data with ML capabilities.

## Architecture

The system is organized into four main layers:

1. **Supervisor Layer** (`supervisors/`)
   - Supervisor Agent: Primary coordination using Python async
   - Error Handler: Sentry integration with custom recovery procedures
   - Logging System: ELK Stack deployment
   - System Monitor: Prometheus + Grafana dashboards

2. **Data Layer** (`data/`)
   - Collection:
     - Scrapy Crawlers
     - Validation Agent
     - Schema Management
     - Anomaly Detection
   - Storage:
     - MongoDB: Raw data
     - PostgreSQL: Processed data
     - Redis: Results cache

3. **Processing Pipeline** (`processing/`)
   - Data Wrangling
   - Data Cleaning
   - Feature Engineering

4. **Analysis Pipeline** (`analysis/`)
   - Data Analysis
   - ML Modeling
   - Interpretability

## Prerequisites

- Python 3.10+
- Docker and Docker Compose
- MongoDB
- PostgreSQL
- Redis
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Prometheus and Grafana

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd new-ai-data-science-team
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start the services using Docker Compose:
```bash
docker-compose up -d
```

## Configuration

### Database Configuration
- MongoDB: Raw data storage with automatic sharding
- PostgreSQL: Processed data with partitioning
- Redis: LRU cache with 15-minute TTL

Configuration files are located in `config/`:
- `settings.py`: Application settings
- `db_config.py`: Database connections
- `logging_config.py`: Logging configuration
- `prometheus.yml`: Prometheus configuration
- `logstash.conf`: Logstash pipeline configuration

### Monitoring Setup

1. **Prometheus** (localhost:9090)
   - Metrics collection
   - Alert configuration
   - Recording rules

2. **Grafana** (localhost:3000)
   - Dashboard setup
   - Visualization
   - Alert management

3. **ELK Stack**
   - Elasticsearch (localhost:9200)
   - Logstash (localhost:5000)
   - Kibana (localhost:5601)

## Usage

1. Start the supervisor layer:
```python
from supervisors.supervisor_agent import supervisor

async def main():
    await supervisor.start()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

2. Monitor the system:
- Access Grafana dashboards at http://localhost:3000
- View logs in Kibana at http://localhost:5601
- Check metrics in Prometheus at http://localhost:9090

## Development

### Testing
```bash
pytest tests/
```

### Code Quality
```bash
# Format code
black .

# Run linter
flake8

# Type checking
mypy .
```

### Documentation
- API documentation is available in `docs/`
- Generate documentation:
```bash
cd docs
make html
```

## Performance Requirements

- Data Pipeline Latency: < 5 minutes
- Model Training: < 2 hours
- API Response: < 500ms
- System Uptime: > 99.9%
- Cache Hit Ratio: > 90%
- Error Recovery: < 1 minute
- Database Query Time: < 100ms

## Security

- Data Encryption: AES-256
- Authentication: JWT + OAuth2
- Access Control: RBAC
- Audit Logging
- GDPR and CCPA Compliance
- Regular Security Audits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

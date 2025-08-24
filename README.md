# 🔍 ProductInsights

> **Modern AI-Powered Content Analysis Platform**

ProductInsights is an enterprise-grade platform that analyzes content from multiple platforms (Amazon, Twitter, Instagram, TikTok) using local LLM technology to provide comprehensive insights and actionable intelligence.

## ✨ Features

- 🤖 **AI-Powered Analysis**: Advanced sentiment analysis, emotion detection, and content quality assessment
- 🔗 **Multi-Platform Integration**: Amazon reviews, Twitter/X, Instagram, and TikTok content analysis
- 📊 **Rich Visualizations**: Interactive charts, time-series analysis, and comprehensive dashboards
- 🏗️ **Clean Architecture**: Scalable, maintainable codebase following Domain-Driven Design principles
- 🚀 **Production Ready**: Docker containers, monitoring, and enterprise-grade security
- 📱 **RESTful API**: Comprehensive API with versioning, rate limiting, and documentation
- 🔒 **Security First**: JWT authentication, CSRF protection, input validation, and rate limiting

## 🏗️ Architecture

This project follows **Clean Architecture** principles with clear separation of concerns:

```
app/
├── api/           # REST API layer (versioned)
├── core/          # Business logic (domains)
├── infrastructure/# External services & database  
├── web/           # Web interface
└── shared/        # Common utilities
```

### Key Components

- **Domain Layer**: Pure business logic with entities and services
- **API Layer**: RESTful endpoints with proper validation and error handling
- **Infrastructure Layer**: Database, external APIs, caching, and AI services
- **Web Layer**: Clean templates and user interface components

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd ProductInsights

# Start with Docker
make docker-quickstart
```

Visit [http://localhost:5000](http://localhost:5000)

### Option 2: Local Development

```bash
# Install dependencies
make install

# Set up environment
cp env.example .env
# Edit .env with your configuration

# Initialize database
make db-init

# Start development server
make dev
```

## 📋 Requirements

### System Requirements
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (for containerized deployment)

### AI Requirements
- Ollama (for local LLM)
- Or OpenAI API key (alternative)

### Platform API Keys
- Twitter/X API credentials
- Instagram Basic Display API
- TikTok Developer API
- Amazon Product Advertising API (optional)

## 🔧 Configuration

Copy `env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/productinsights

# Redis
REDIS_URL=redis://localhost:6379/0

# AI Service
OLLAMA_API_URL=http://localhost:11434

# Platform APIs
TWITTER_API_KEY=your_key_here
INSTAGRAM_ACCESS_TOKEN=your_token_here
# ... etc
```

## 🐳 Docker Deployment

### Development
```bash
make docker-dev
```

### Production
```bash
BUILD_TARGET=production make docker-prod
```

### With Monitoring
```bash
make monitor
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration

# Run with coverage
pytest --cov=app tests/
```

## 📊 API Documentation

The API is versioned and follows RESTful principles:

### Authentication
```bash
# Get JWT token
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "password"
}

# Use token in headers
Authorization: Bearer <jwt_token>
```

### Analysis Endpoints
```bash
# Create analysis
POST /api/v1/analysis/
{
  "platform": "twitter",
  "target_identifier": "@username",
  "analysis_type": "comprehensive_analysis"
}

# Get analyses
GET /api/v1/analysis/?platform=twitter&limit=10

# Get specific analysis
GET /api/v1/analysis/{analysis_id}
```

## 📈 Monitoring

Access monitoring dashboards:

- **Application**: [http://localhost:5000](http://localhost:5000)
- **Prometheus**: [http://localhost:9090](http://localhost:9090)
- **Grafana**: [http://localhost:3000](http://localhost:3000) (admin/admin123)

## 🎯 Development

### Project Structure

```
ProductInsights/
├── app/                    # Application code
│   ├── api/               # REST API layer
│   ├── core/              # Business logic
│   ├── infrastructure/    # External services
│   ├── web/               # Web interface
│   └── shared/            # Common utilities
├── config/                # Configuration
├── tests/                 # Test suite
├── requirements/          # Dependencies
├── deployments/          # Deployment configs
├── docker-compose.yml    # Container orchestration
├── Dockerfile           # Container definition
└── Makefile            # Development tasks
```

### Key Commands

```bash
# Development
make dev              # Start development server
make test             # Run tests
make lint             # Code linting
make format           # Format code

# Docker
make docker-dev       # Development with Docker
make docker-prod      # Production deployment
make docker-clean     # Clean Docker resources

# Database
make db-init          # Initialize database
make db-migrate       # Run migrations
make db-seed          # Seed sample data
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Code Standards
- Follow PEP 8 style guide
- Write comprehensive tests
- Use type hints
- Document your code
- Follow Clean Architecture principles

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📚 **Documentation**: [Full documentation](docs/)
- 🐛 **Issues**: [GitHub Issues](https://github.com/yourorg/productinsights/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourorg/productinsights/discussions)
- 📧 **Email**: support@productinsights.com

## 🙏 Acknowledgments

- Built with Flask and Clean Architecture principles
- Uses Ollama for local LLM capabilities
- Inspired by modern software engineering practices
- Thanks to all contributors and the open-source community

---

**ProductInsights** - Transforming content analysis with AI-powered insights 🚀

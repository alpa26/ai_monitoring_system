# AI Monitoring System

Система обнаружения аномалий в микросервисных backend-системах на основе LSTM Autoencoder.

Проект разработан как MVP интеллектуальной системы мониторинга для Kubernetes / microservices environments с интеграцией в Prometheus и поддержкой real-time anomaly detection.

---

# Возможности

- Сбор метрик из Prometheus
- Анализ временных рядов
- Обнаружение аномалий с помощью LSTM Autoencoder
- Streaming inference
- Batch analysis
- Автоматический retraining модели
- Email / VK alerting
- Web UI (Streamlit)
- Kubernetes deployment
- Docker containerization

---

# Используемые технологии

- Python 3.13
- TensorFlow / Keras
- Prometheus
- Kubernetes
- Istio
- Streamlit
- Docker

---

# Архитектура

Pipeline системы:

Prometheus → preprocessing → feature engineering → LSTM Autoencoder → anomaly score → alerting

---

# Структура проекта

```text
ai_monitoring_system/
│
├── data/
├── model/
├── k8s/
│
├── detector.py
├── preprocess.py
├── stream.py
├── train.py
├── retrain.py
├── main.py
├── app.py
│
├── Dockerfile
├── requirements.txt
└── README.md
```

---

# Установка

## 1. Клонирование репозитория

```bash
git clone <YOUR_REPOSITORY_URL>
cd ai_monitoring_system
```

---

## 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

---

# Запуск системы

## Streaming mode

```bash
python main.py --stream
```

---

## Batch mode

```bash
python main.py --input data/dataset.csv
```

---

# Web UI

Запуск панели управления:

```bash
streamlit run app.py
```

После запуска интерфейс будет доступен по адресу:

```text
http://localhost:8501
```

---

# Retraining

Переобучение модели:

```bash
python retrain.py
```
Также переобучение можно запустить через админ панель

---

# Docker

## Сборка контейнера

```bash
docker build -t ai-monitoring-system .
```

## Запуск контейнера

```bash
docker run ai-monitoring-system
```

---

# Kubernetes deployment

```bash
kubectl apply -f k8s/deployment.yaml
```

---

# Основные метрики

Система анализирует:

- CPU usage
- Memory usage
- RPS
- Error rate
- Latency p95
- Network traffic
- Container restarts

---

# Model

Используется LSTM Autoencoder для анализа многомерных временных рядов.

Модель обучается на нормальном поведении системы и использует reconstruction error как anomaly score.

---

# Alerting

Поддерживаются:

- Email alerts
- VK alerts
- Console alerts

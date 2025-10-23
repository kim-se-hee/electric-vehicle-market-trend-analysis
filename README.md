# EV Market Intelligence Agent

**전기차 시장 트렌드를 자동으로 분석하고 투자 리포트를 생성**하는 Supervisor 기반 Multi-Agent 시스템 실습 프로젝트입니다.

## Overview

- **Objective**: 전기차 산업의 시장 동향, 주요 기업 분석, 주가 데이터를 종합하여 투자 의사결정을 위한 전문 리포트 자동 생성
- **Method**: Supervisor-based Multi-Agent System + Agentic RAG + Web Search
- **Tools**: LangGraph, LangChain, Tavily Search, FAISS, OpenAI GPT-4

## Features

- **실시간 시장 조사**: 전기차 시장 트렌드, 리튬 배터리 공급망 이슈, 산업 성장률 등을 자동 검색 및 분석
- **기업 심층 분석**: Tesla, BYD, 삼성SDI 등 주요 전기차/배터리 기업의 IR 자료 및 뉴스를 RAG 기반으로 분석
- **재무/주가 분석**: 실시간 주가 데이터, PER/PBR 등 밸류에이션 지표, 재무제표 기반 건전성 평가
- **데이터 시각화**: 주가 추이, 시가총액 비교, 섹터별 수익률 등을 matplotlib/plotly로 차트 생성
- **자동 리포트 생성**: 모든 분석 결과를 통합하여 Executive Summary가 포함된 PDF 투자 리포트 생성
- **지능형 워크플로우**: Supervisor Agent가 State의 상태에 따라 Agent 동작 흐름을 동적으로 결정하고 모든 분석 결과를 통합한 최종 투자 리포트를 생성

## Tech Stack

| Category            | Details                           |
| ------------------- | --------------------------------- |
| **Framework**       | LangChain 0.1.x, Python 3.10+     |
| **LLM**             | GPT-4o-mini via OpenAI API 1.12+  |
| **Retrieval**       | FAISS (vector store), Agentic RAG |
| **Embedding**       | HuggingFace sentence-transformers |
| **Search**          | Tavily Search API 0.3+            |
| **Web Scraping**    | BeautifulSoup4, lxml, html2text   |
| **HTTP Client**     | aiohttp, httpx, requests          |
| **Data Validation** | Pydantic 2.6+, pydantic-settings  |
| **Environment**     | python-dotenv                     |

## Agents

### Supervisor Agent

사용자 요청을 분석하여 필요한 Agent를 선택하고 실행 순서를 동적으로 결정하는 에이전트

**동작 방식**:

- 사용자 쿼리 분석 후 작업에 필요한 Agent 조합을 결정
- 각 Agent의 실행 결과를 State에 저장하고 다음 실행할 Agent를 선택
- 모든 필수 작업이 완료될 때까지 반복적으로 Agent 호출

**실행 예시**:

```
사용자: "테슬라 주가 분석해줘"
→ Stock_Analyzer → Chart_Generator → Report_Compiler

사용자: "전기차 시장 동향과 주요 기업 분석해줘"
→ Market_Researcher → Company_Analyzer → Stock_Analyzer
→ Chart_Generator → Report_Compiler

사용자: "BYD와 테슬라 비교 분석"
→ Company_Analyzer → Stock_Analyzer → Chart_Generator → Report_Compiler
```

**결정 기준**:

- State 확인을 통한 중복 실행 방지
- Agent 간 의존성 파악 (예를 들어 Chart_Generator는 Stock_Analyzer 이후 실행)
- 사용자 쿼리에 따라 필요하지 않은 Agent는 건너뛰기

### Market_Researcher

전기차 시장의 최신 트렌드와 현황을 조사

**Tools**: Web Search (Tavily API)

**Output**:

- 시장 규모 및 성장률
- 주요 트렌드 (예: 가격 경쟁, 충전 인프라)
- 리튬 배터리 공급망 이슈
- 주요 이슈 분석
- 참고 문헌 URL

### Company_Analyzer

주요 전기차 제조사 및 배터리 공급사의 사업 전략 분석

**Tools**: Agentic RAG (FAISS + Web Fetch)

**Output**:

- 기업별 사업 전략
- 핵심 제품 라인업
- 주요 파트너십
- 기술적 강점/약점
- 직면한 리스크

### Stock_Analyzer

분석 대상 기업들의 주가 데이터 및 재무 지표 수집/분석

**Tools**: yfinance API, Financial Data APIs

**Output**:

- 주가 히스토리 (1년간)
- 재무제표 지표 (매출, 영업이익, 부채비율 등)
- 밸류에이션 지표 (PER, PBR, PSR)
- 재무 건전성 평가

### Chart_Generator

주가 및 재무 데이터를 시각화

**Tools**: matplotlib, plotly

**Output**:

- 주가 추이 라인 차트
- 기업별 시가총액 비교 바 차트
- 섹터별 수익률 파이 차트

### Report_Compiler

모든 분석 결과를 통합하여 PDF 리포트 생성

**Tools**: ReportLab, FPDF

**Output**:

- Executive Summary
- 시장 분석 섹션
- 기업 분석 섹션
- 주가/재무 분석 섹션
- 차트 삽입
- 참고 문헌 목록

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Request                            │
│            "전기차 시장 동향과 주요 기업 분석해줘"           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  Supervisor Agent    │
            │  (작업 조율 및 분배) │
            └──────────┬───────────┘
                       │
       ┌───────────────┼───────────────┐
       │               │               │
       ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  Market     │ │  Company    │ │   Stock     │
│ Researcher  │ │  Analyzer   │ │  Analyzer   │
│             │ │             │ │             │
│ Web Search  │ │ Agentic RAG │ │             │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │
       └───────────────┼───────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  Chart Generator     │
            │  matplotlib/plotly   │
            └──────────┬───────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  Report Compiler     │
            │  PDF Generation      │
            └──────────┬───────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │   Final PDF Report   │
            └──────────────────────┘
```

## Directory Structure

```
ev-market-intelligence/
├── common/
│   ├── __init__.py
│   ├── agent/
│   │   ├── __init__.py
│   │   └── base_agent.py          # BaseAgent 추상 클래스
│   └── config/
│       ├── __init__.py
│       └── settings.py             # 환경 변수 로드
│
├── market_research/
│   ├── __init__.py
│   ├── agent/
│   │   ├── __init__.py
│   │   └── market_researcher.py   # Market Researcher Agent
│   ├── tools/
│   │   ├── __init__.py
│   │   └── web_search_tool.py     # Tavily Search Wrapper
│   └── test/
│       ├── __init__.py
│       └── market_researcher_test.py
│
├── company_analysis/
│   ├── __init__.py
│   ├── agent/
│   │   ├── __init__.py
│   │   └── company_analyzer.py    # Company Analyzer Agent
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── rag_tool.py            # FAISS RAG System
│   │   └── document_loader.py     # Web Fetch & Document Loading
│   └── test/
│       ├── __init__.py
│       └── company_analyzer_test.py
│
├── stock_analysis/
│   ├── __init__.py
│   ├── agent/
│   │   ├── __init__.py
│   │   └── stock_analyzer.py      # Stock Analyzer Agent
│   ├── tools/
│   │   ├── __init__.py
│   │   └── finance_api.py         # yfinance Wrapper
│   └── test/
│       ├── __init__.py
│       └── stock_analyzer_test.py
│
├── chart_generation/
│   ├── __init__.py
│   ├── agent/
│   │   ├── __init__.py
│   │   └── chart_generator.py     # Chart Generator Agent
│   ├── tools/
│   │   ├── __init__.py
│   │   └── visualization.py       # matplotlib/plotly utils
│   └── test/
│       ├── __init__.py
│       └── chart_generator_test.py
│
├── report_compilation/
│   ├── __init__.py
│   ├── agent/
│   │   ├── __init__.py
│   │   └── report_compiler.py     # Report Compiler Agent
│   ├── tools/
│   │   ├── __init__.py
│   │   └── pdf_generator.py       # ReportLab Wrapper
│   └── test/
│       ├── __init__.py
│       └── report_compiler_test.py
│
├── supervisor/
│   ├── __init__.py
│   ├── supervisor_agent.py        # Supervisor Agent (LangGraph)
│   └── workflow.py                # StateGraph Definition
│
├── data/
│   ├── raw/                       # 수집한 원본 데이터
│   ├── processed/                 # 전처리된 데이터
│   └── vectorstore/               # FAISS 인덱스
│
├── outputs/
│   ├── charts/                    # 생성된 차트 이미지
│   ├── reports/                   # 생성된 PDF 리포트
│   └── logs/                      # Agent 실행 로그
│
├── .env                           # 환경 변수 (생성 필요)
├── .gitignore
├── requirements.txt
├── main.py                        # 전체 시스템 실행 스크립트
└── README.md
```

## Installation

### Prerequisites

- Python 3.10 이상
- OpenAI API Key
- Tavily Search API Key

### Setup

```bash
# 1. 저장소 클론
git clone https://github.com/yourusername/ev-market-intelligence.git
cd ev-market-intelligence

# 2. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 패키지 설치
pip install -r requirements.txt

# 4. 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 API 키 입력
```

### .env 파일 설정

```
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
```

## Usage

### 전체 시스템 실행

```bash
python main.py
```

실행 시 Supervisor Agent가 자동으로:

1. 시장 조사 수행
2. 주요 기업 분석
3. 주가 데이터 수집
4. 차트 생성
5. PDF 리포트 작성

### 개별 Agent 테스트

```bash
# Market Researcher 테스트
python market_research/test/market_researcher_test.py

# Company Analyzer 테스트
python company_analysis/test/company_analyzer_test.py

# Stock Analyzer 테스트
python stock_analysis/test/stock_analyzer_test.py
```

## Output Example

생성되는 PDF 리포트 구조:

```
===================================
전기차 시장 투자 분석 리포트
2025년 10월 23일
===================================

[Executive Summary]
- 아래 내용을 종합한 요약본

[1. 시장 분석]
1.1 시장 규모 및 성장률
1.2 주요 트렌드
1.3 리튬 배터리 공급망

[2. 기업 분석]
2.1 Tesla
2.2 BYD
2.3 삼성SDI

[3. 주가 및 재무 분석]
3.1 주가 추이
3.2 밸류에이션
3.3 재무 건전성

[4. 차트 및 시각화]
- 주가 비교 차트
- 시가총액 분포

[참고 문헌]
```

## Implementation Status

- [o] BaseAgent 추상 클래스
- [o] Market_Researcher Agent
- [o] Company_Analyzer Agent
- [ ] Stock_Analyzer Agent
- [ ] Chart_Generator Agent
- [ ] Report_Compiler Agent
- [ ] Supervisor Agent
- [ ] LangGraph Workflow Integration

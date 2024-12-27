```mermaid
graph TB
    subgraph Supervisor_Layer
        SA[Supervisor Agent]
        Error[Error Handler]
        Logger[Logging System]
        Monitor[System Monitor]
    end

    subgraph Data_Layer
        subgraph Data_Collection
            Validation[Data Validation Agent]
            Scrapy[Scrapy Crawlers]
            Raw_DB[MongoDB: Raw Data]
        end

        subgraph Data_Storage
            SQL_DB[PostgreSQL: Processed Data]
            Cache[Redis: Results Cache]
        end
    end

    subgraph Processing_Pipeline
        DW[Data Wrangling Agent]
        DC[Data Cleaning Agent]
        FE[Feature Engineering Agent]
    end

    subgraph Analysis_Pipeline
        DA[Data Analyst Agent]
        ML[ML Modeling Agent]
        IA[Interpretability Agent]
    end

    %% Primary Data Flow
    Scrapy -->|Raw Data| Validation
    Validation -->|Validated Data| Raw_DB
    Raw_DB -->|Unprocessed| DW
    DW -->|Merged Data| DC
    DC -->|Clean Data| FE
    FE -->|ML-Ready Data| DA
    DA -->|Analyzed Data| ML
    ML -->|Model Results| IA

    %% Feedback Loops
    ML -.->|Feature Feedback| FE
    IA -.->|Analysis Insights| DA

    %% Storage Connections
    SQL_DB -->|Processed Data| DA & ML & IA
    Cache -->|Cached Results| DA & ML & IA

    %% Supervisor Controls
    SA --> Validation & DW & DC & FE & DA & ML & IA
    Error --> Validation & DW & DC & FE & DA & ML & IA
    Logger -->|Activity Logs| Monitor
    Monitor -->|Status| SA

    %% Status Legend
    style Validation fill:#90EE90,stroke:#333
    style DW fill:#90EE90,stroke:#333
    style DC fill:#90EE90,stroke:#333
    style FE fill:#90EE90,stroke:#333
    style DA fill:#D3D3D3,stroke:#333
    style ML fill:#D3D3D3,stroke:#333
    style IA fill:#D3D3D3,stroke:#333

    classDef storage fill:#FFE4B5,stroke:#333
    classDef supervisor fill:#ADD8E6,stroke:#333
    class Raw_DB,SQL_DB,Cache storage
    class SA,Error,Logger,Monitor supervisor
```
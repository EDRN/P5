# EDRN Portal Docker Architecture

```mermaid
graph TB
    subgraph "External Access via ALB"
        Internet[Internet/Users]
        Portal_Port[Port 443<br/>HTTP]
    end

    subgraph "Frontend Services"
        Portal[Portal<br/>edrn-portal<br/>Wagtail CMS<br/>Port 8000]
    end

    subgraph "Backend Services"
        DB[(PostgreSQL 17.6<br/>Database<br/>Port 5432)]
        Cache[(Redis 7.0<br/>Cache & MQ<br/>Port 6379)]
        Search[(Elasticsearch 8.10<br/>Search Engine<br/>Port 9200)]
        Worker[Celery Worker<br/>edrn-portal<br/>Background Tasks]
    end

    subgraph "Initialization"
        StaticInit[Static Initializer<br/>Copies static files]
    end

    subgraph "Volumes"
        StaticVol[(Static Volume<br/>CSS, JS, Images)]
        MediaVol[(Media Volume<br/>PDFs, Images)]
        DBVol[(Database Volume<br/>PostgreSQL Data)]
        ElasticVol[(Elasticsearch Volume<br/>Search Indexes)]
    end

    subgraph "Networks"
        Lattice[Lattice Network<br/>Bridge Network]
        Default[Default Network]
    end

    %% External connections
    Internet -->|HTTP| Portal_Port
    Portal_Port --> Portal

    %% Service dependencies
    StaticInit -->|initializes| StaticVol
    Portal -->|depends on| StaticInit
    Portal -->|connects to| DB
    Portal -->|connects to| Cache
    Portal -->|connects to| Search
    Portal -->|depends on| Worker
    Worker -->|connects to| DB
    Worker -->|connects to| Cache
    Worker -->|connects to| Search

    %% Volume attachments
    StaticInit -.->|writes| StaticVol
    Portal -.->|reads/writes| StaticVol
    Portal -.->|reads/writes| MediaVol
    DB -.->|persists| DBVol
    Search -.->|persists| ElasticVol
    Worker -.->|reads/writes| MediaVol

    %% Network connections
    Portal -.->|lattice + default| Lattice
    DB -.->|lattice| Lattice
    Cache -.->|lattice| Lattice
    Search -.->|lattice| Lattice
    Worker -.->|lattice| Lattice

    %% Styling
    classDef frontend fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef backend fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef volume fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef network fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef init fill:#fff9c4,stroke:#f57f17,stroke-width:2px

    class Portal frontend
    class DB,Cache,Search,Worker backend
    class StaticVol,MediaVol,DBVol,ElasticVol volume
    class Lattice,Default network
    class StaticInit init
```

## Service Details

### Frontend Services
- **Portal**: Main Wagtail CMS application (port 8000, published as 443)

### Backend Services
- **Database**: PostgreSQL 17.6 storing portal content
- **Cache**: Redis 7.0 for caching and message queue
- **Search**: Elasticsearch 8.10 for full-text search
- **Worker**: Celery worker for background task processing

### Volumes
- **Static Volume**: CSS, JavaScript, images (bind mount)
- **Media Volume**: User-uploaded files like PDFs and images (bind mount)
- **Database Volume**: PostgreSQL data persistence (bind mount)
- **Elasticsearch Volume**: Search indexes and data

### Networks
- **Lattice Network**: Internal bridge network for service communication
- **Default Network**: Default Docker network (used by Portal)

## Connection Flow

1. **External → Portal**: Direct HTTP access on port 443
2. **Portal ↔ Backend Services**: Connects to DB, Cache, and Search
3. **Worker ↔ Backend Services**: Processes background tasks using DB and Cache
4. **Static Initializer**: Prepares static files volume before Portal starts


# Data Engineer

## Role Overview

A Data Engineer is responsible for designing, building, and maintaining scalable data infrastructure that enables organizations to collect, process, store, and analyze large volumes of data efficiently. They serve as the bridge between raw data sources and data consumers (analysts, scientists, and business stakeholders), ensuring data is accessible, reliable, and secure. Data Engineers focus on creating robust data pipelines, implementing data quality frameworks, optimizing data warehouse performance, and ensuring compliance with data governance standards. Their work is foundational to modern data-driven organizations, enabling real-time analytics, machine learning, and business intelligence.

## Key Skills

### Technical Skills

- **Programming Languages**: Proficiency in Python (for scripting, data manipulation, and ETL pipelines), SQL (for querying and managing relational databases), and Java/Scala (for big data frameworks like Apache Spark)
- **Cloud Platforms**: Expertise in AWS (S3, Redshift, Glue, Lambda, EMR), Google Cloud Platform (BigQuery, Dataflow, Cloud Functions), Microsoft Azure (Data Factory, Synapse Analytics, Blob Storage), and Snowflake
- **Big Data Technologies**: Mastery of Apache Spark (distributed data processing), Apache Kafka (real-time streaming), Hadoop ecosystem (HDFS, Hive, MapReduce), and emerging tools like Dask and Ray
- **Database Management**: Experience with relational databases (PostgreSQL, MySQL, SQL Server), NoSQL databases (MongoDB, Cassandra, DynamoDB), and columnar databases (ClickHouse, Parquet)
- **Pipeline Orchestration**: Proficiency with Apache Airflow, Prefect, Dagster, and dbt (Data Build Tool) for workflow automation and data transformation
- **Streaming & Real-Time Processing**: Expertise in Kafka Streams, Apache Flink, AWS Kinesis, Google Pub/Sub, and Debezium for event-driven architectures and change data capture
- **Data Quality & Observability**: Implementation of automated testing frameworks (Great Expectations, Soda) and monitoring tools (Monte Carlo, Datadog)
- **Security & Governance**: Knowledge of data encryption, access controls, audit trails, and compliance regulations (GDPR, HIPAA, SOC 2)

### Soft Skills

- **Problem-Solving**: Strong analytical thinking and troubleshooting abilities for complex data systems
- **Communication**: Ability to translate technical concepts into plain language for cross-functional collaboration
- **Critical Thinking**: Capability to make informed decisions autonomously and evaluate architectural trade-offs
- **Adaptability**: Competence in managing changing priorities and requirements in dynamic environments
- **Collaboration**: Effective teamwork with data scientists, analysts, product managers, and other stakeholders

## Core Knowledge Areas

- **Data Architecture Patterns**: Understanding of lakehouse, warehouse, and hybrid architectures; ability to evaluate and choose between batch and streaming data ingestion strategies
- **ETL/ELT Processes**: Expertise in Extract, Transform, Load and Extract, Load, Transform workflows for data integration
- **Data Quality & Observability**: Implementation of automated testing, schema validation, freshness monitoring, and anomaly detection to ensure data integrity
- **Cost & Performance Optimization**: Skills in tuning data warehouse compute resources, managing auto-scaling policies, establishing data retention strategies, and monitoring cost per query
- **Security, Governance & Compliance**: Knowledge of data encryption (at rest and in transit), role-based access control, data lineage tracking, anonymization, tokenization, and regulatory compliance (GDPR, HIPAA, SOC 2, CCPA)
- **DevOps & Automation**: Experience with CI/CD pipelines for data, containerization (Docker, Kubernetes), deployment strategies (blue-green deployments), and infrastructure as code
- **Data Modeling**: Skills in dimensional modeling, indexing strategies, partitioning, clustering, and storage tiering for optimal query performance
- **Event-Driven Architectures**: Understanding of event schemas, backpressure handling, and millisecond-level real-time data processing

## Responsibilities

- **Design & Build Data Pipelines**: Create scalable, fault-tolerant data pipelines that efficiently move and transform data from source systems to data warehouses and data lakes
- **Implement Data Quality Frameworks**: Establish automated testing, monitoring, and alerting systems to detect schema changes, freshness issues, and data anomalies before they impact stakeholders
- **Optimize Data Warehouse Performance**: Tune query performance, manage compute resources, implement partitioning and clustering strategies, and optimize storage costs
- **Ensure Data Security & Compliance**: Implement access controls, encryption, audit trails, and data governance policies to meet regulatory requirements and protect sensitive information
- **Collaborate with Cross-Functional Teams**: Work closely with data scientists, analysts, product managers, and business stakeholders to translate requirements into data models and ensure alignment across the data value chain
- **Maintain & Monitor Data Infrastructure**: Continuously monitor pipeline health, system performance, and costs; troubleshoot issues and implement improvements
- **Document Data Processes**: Maintain comprehensive documentation of data pipelines, transformations, schemas, and data lineage for transparency and maintainability
- **Automate Workflows**: Implement CI/CD practices for data pipelines, containerize workflows, and establish deployment strategies for rapid iteration and system resilience

## Best Practices

- **Architecture-First Mindset**: Design scalable, fault-tolerant data platforms by evaluating architectural patterns (lakehouse, warehouse, hybrid) and making informed decisions between batch and streaming ingestion aligned with business growth
- **Automated Testing & Monitoring**: Implement automated testing frameworks (Great Expectations, Soda) and monitoring tools (Monte Carlo, Datadog) to detect schema changes, freshness issues, and anomalies proactively
- **Cost Optimization**: Monitor metrics like cost per query and pipeline runtime; establish data retention strategies, manage auto-scaling policies, and forecast cloud expenditures to maintain financial efficiency
- **Data Lineage & Cataloging**: Track data transformations and usage throughout the data stack for compliance, debugging, and impact analysis
- **CI/CD for Data Pipelines**: Manage continuous integration and deployment for data workflows, enabling rapid iteration and reducing deployment risks
- **Documentation & Observability**: Maintain comprehensive records of data processes, schemas, transformations, and system architecture to facilitate collaboration and troubleshooting
- **Security by Design**: Embed access controls, encryption, and audit trails throughout the data stack from the initial design phase
- **Performance Tuning**: Regularly optimize data warehouse compute resources, query performance, and storage strategies (tiering, partitioning, clustering) based on usage patterns
- **Cross-Functional Collaboration**: Translate stakeholder requirements into technical implementations and ensure alignment between business needs and data infrastructure capabilities

## Tools & Technologies

### Orchestration & Workflow Management
- **Apache Airflow**: Industry standard for automating and orchestrating data workflows
- **Prefect**: Modern workflow orchestration platform with Python-first design
- **Dagster**: Data orchestration platform with strong observability features
- **dbt (Data Build Tool)**: SQL-based transformation tool for cloud data warehouses

### Data Processing
- **Apache Spark**: Distributed data processing engine for large-scale analytics
- **Dask**: Parallel computing library for Python workloads
- **Ray**: Distributed computing framework for scalable Python applications
- **Hadoop Ecosystem**: HDFS, Hive, MapReduce for batch processing

### Streaming & Real-Time Processing
- **Apache Kafka**: Distributed streaming platform for event-driven architectures
- **Apache Flink**: Stream processing framework for real-time analytics
- **AWS Kinesis**: Managed streaming service for real-time data ingestion
- **Google Pub/Sub**: Messaging service for event-driven systems
- **Kafka Streams**: Library for building stream processing applications
- **Debezium**: Platform for change data capture (CDC) from databases

### Cloud Data Warehouses & Storage
- **Snowflake**: Cloud-based data warehousing solution
- **Amazon Redshift**: Fully managed data warehouse service
- **Google BigQuery**: Serverless, highly scalable data warehouse
- **Amazon S3**: Object storage service for data lakes
- **Azure Synapse Analytics**: Analytics service for data warehousing

### Data Quality & Testing
- **Great Expectations**: Python-based data validation framework
- **Soda**: Data quality platform for automated testing

### Monitoring & Observability
- **Monte Carlo**: Data observability platform for detecting data issues
- **Datadog**: Monitoring and analytics platform for infrastructure and applications

### Databases
- **Relational**: PostgreSQL, MySQL, Microsoft SQL Server
- **NoSQL**: MongoDB, Cassandra, DynamoDB
- **Columnar**: ClickHouse, Apache Parquet

### Cloud Platforms
- **AWS**: S3, Redshift, Glue, Lambda, EMR, Kinesis
- **Google Cloud**: BigQuery, Dataflow, Cloud Functions, Pub/Sub
- **Microsoft Azure**: Data Factory, Synapse Analytics, Blob Storage

## Approach to Tasks

Data Engineers approach tasks with a systematic, architecture-first mindset that prioritizes scalability, reliability, and cost-efficiency. When tackling a new problem, they:

1. **Evaluate Architecture Options**: Assess different architectural patterns (lakehouse, warehouse, hybrid) and data ingestion strategies (batch vs. streaming) to determine the best fit for business requirements and growth projections

2. **Design for Scale & Reliability**: Build fault-tolerant systems that can handle increasing data volumes and maintain performance under varying loads, considering factors like partitioning, clustering, and storage tiering

3. **Prioritize Data Quality**: Implement automated testing and monitoring from the start, ensuring data integrity through schema validation, freshness checks, and anomaly detection before issues impact downstream consumers

4. **Optimize Cost & Performance**: Continuously monitor and optimize data warehouse resources, query performance, and storage costs while balancing performance requirements with budget constraints

5. **Embrace Automation**: Leverage CI/CD practices, containerization, and infrastructure as code to enable rapid iteration, reduce manual errors, and improve system resilience

6. **Ensure Security & Compliance**: Embed security controls, encryption, and audit trails throughout the data stack, ensuring compliance with relevant regulations from the design phase

7. **Collaborate Effectively**: Translate business requirements into technical implementations, work closely with cross-functional teams, and maintain clear documentation to ensure alignment and knowledge sharing

8. **Monitor & Iterate**: Continuously monitor pipeline health, system performance, and costs; use observability tools to identify bottlenecks and opportunities for improvement

## Context-Specific Notes

<!-- Add any relevant notes for the Investment Platform project context here -->
<!-- Consider factors such as: -->
<!-- - Financial data requirements and compliance (SEC, FINRA regulations) -->
<!-- - Real-time market data ingestion and processing needs -->
<!-- - Historical data storage and time-series data optimization -->
<!-- - Integration with trading systems and portfolio management tools -->
<!-- - Data privacy and security requirements for financial information -->


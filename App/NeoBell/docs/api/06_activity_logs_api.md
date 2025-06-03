# Activity Logs API

## Overview
Provides a comprehensive activity feed for monitoring device events, user actions, and system notifications.

## API Handler
`NeoBellActivityLogHandler`

## Workflow Diagram

```mermaid
sequenceDiagram
    participant Device as NeoBell SBC
    participant IoT as IoT Core
    participant Lambda1 as EventLogger
    participant DDB as DynamoDB
    participant App as Mobile App
    participant API as API Gateway
    participant Lambda2 as ActivityHandler

    Note over Device,DDB: Event Logging
    Device->>IoT: Device event
    IoT->>Lambda1: Process event
    Lambda1->>DDB: Log event
    
    Note over App,DDB: Event Retrieval
    App->>API: GET /activity-logs
    API->>Lambda2: Fetch logs
    Lambda2->>DDB: Query EventLogs
    Lambda2-->>App: Return activity feed
```

## Endpoints

### 1. Get Activity Logs
- **Method**: GET
- **Path**: `/activity-logs`
- **Auth**: Required (Cognito JWT)
- **Query Parameters**:
  - `event_types`: Comma-separated list of event types
  - `sbc_id`: Filter by device
  - `start_date`: ISO8601 timestamp
  - `end_date`: ISO8601 timestamp
  - `limit`: Number of items
  - `last_evaluated_key`: Pagination key
- **Response (200 OK)**:
```json
{
    "items": [
        {
            "log_source_id": "sbc_device_id_1",
            "timestamp_uuid": "YYYY-MM-DDTHH:mm:ss.sssZ_unique_suffix",
            "event_type": "doorbell_pressed",
            "timestamp": "YYYY-MM-DDTHH:mm:ssZ",
            "summary": "Campainha tocada na Porta da Frente.",
            "sbc_id_related": "sbc_device_id_1",
            "user_id_related": "cognito_sub_uuid_related",
            "details": {
                "message_id_if_any": "message_uuid_for_video_recado"
            }
        }
    ],
    "last_evaluated_key": "optional_pagination_key_stringified_json_complex"
}
```

## Data Model

### EventLogs Table
```javascript
{
    "log_source_id": "string (PK)",
    "timestamp_uuid": "string (SK)",
    "event_type": "string",
    "timestamp": "string",
    "summary": "string",
    "sbc_id_related": "string",
    "user_id_related": "string",
    "details": {
        // Event-specific details
    }
}
```

### Event Types
1. Device Events
   - `doorbell_pressed`
   - `video_message_recorded`
   - `package_detected`
   - `visitor_detected`
   - `device_status_change`

2. User Events
   - `user_access_granted`
   - `user_access_removed`
   - `settings_changed`
   - `permission_updated`

3. System Events
   - `firmware_update`
   - `device_registered`
   - `device_removed`
   - `error_occurred`

## Integration Points

### AWS Services
- IoT Core: Device event ingestion
- DynamoDB: Log storage
- Lambda: Event processing
- API Gateway: REST API
- CloudWatch: Monitoring

### Related Workflows
1. Event Logging Process
   - Event detection
   - Event processing
   - Log storage
   - User notification

2. Log Retrieval Process
   - Query optimization
   - Data aggregation
   - Access control
   - Data presentation

## Error Handling

| Status Code | Description | Common Causes |
|------------|-------------|---------------|
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Invalid token |
| 403 | Forbidden | Access denied |
| 500 | Server Error | Processing error |

## Security Considerations

### Access Control
1. Device-specific access
2. User role validation
3. Time-based access
4. Data privacy

### Data Protection
1. Sensitive data handling
2. Retention policies
3. Access logging
4. Encryption

## Performance Optimization

### Query Patterns
1. Time-based partitioning
2. GSI optimization
3. Selective attribute projection
4. Efficient filtering

### Data Management
1. TTL implementation
2. Archival strategy
3. Hot/cold data separation
4. Compression

## Monitoring

### Metrics
1. Event ingestion rate
2. Query performance
3. Storage usage
4. Error rates
5. Access patterns

### Alerts
1. High error rates
2. Query timeouts
3. Storage thresholds
4. Access anomalies

## Best Practices

### Event Logging
1. Standardized format
2. Required fields
3. Validation rules
4. Error handling

### Data Lifecycle
1. Retention periods
2. Archival rules
3. Cleanup processes
4. Recovery procedures

### Query Optimization
1. Index design
2. Filter efficiency
3. Pagination strategy
4. Cache utilization

## Implementation Guidelines

### Event Processing
1. Asynchronous processing
2. Batch operations
3. Error recovery
4. Duplicate handling

### Data Access
1. Permission mapping
2. Data filtering
3. Response formatting
4. Cache strategy

### Maintenance
1. Index management
2. Cleanup routines
3. Performance monitoring
4. Capacity planning

## Integration Examples

### Device Integration
```javascript
// IoT Core message format
{
    "event_type": "doorbell_pressed",
    "sbc_id": "device_123",
    "timestamp": "2025-06-02T20:00:00Z",
    "details": {
        "visitor_detected": true,
        "video_recorded": true
    }
}
```

### Mobile App Integration
```javascript
// Activity feed query parameters
{
    "event_types": "doorbell_pressed,package_detected",
    "sbc_id": "device_123",
    "start_date": "2025-06-01T00:00:00Z",
    "end_date": "2025-06-02T23:59:59Z",
    "limit": 50
}
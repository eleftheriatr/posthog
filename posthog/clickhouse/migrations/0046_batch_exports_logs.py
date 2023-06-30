from posthog.clickhouse.batch_exports_logs import (
    BATCH_EXPORTS_LOGS_TABLE_MV_SQL,
    BATCH_EXPORTS_LOGS_TABLE_SQL,
    KAFKA_BATCH_EXPORTS_LOGS_TABLE_SQL,
)
from posthog.clickhouse.client.migration_tools import run_sql_with_exceptions

operations = [
    run_sql_with_exceptions(BATCH_EXPORTS_LOGS_TABLE_SQL()),
    run_sql_with_exceptions(KAFKA_BATCH_EXPORTS_LOGS_TABLE_SQL()),
    run_sql_with_exceptions(BATCH_EXPORTS_LOGS_TABLE_MV_SQL),
]

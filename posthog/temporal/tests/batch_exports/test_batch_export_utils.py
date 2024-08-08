import asyncio
import datetime as dt

import pytest
import pytest_asyncio

from posthog.batch_exports.models import BatchExportRun
from posthog.temporal.batch_exports.utils import set_status_to_running_task
from posthog.temporal.common.logger import bind_temporal_worker_logger
from posthog.temporal.tests.utils.models import (
    acreate_batch_export,
    adelete_batch_export,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.django_db]


@pytest_asyncio.fixture
async def s3_batch_export(
    ateam,
    temporal_client,
):
    """Provide a batch export for tests, not intended to be used."""
    destination_data = {
        "type": "S3",
        "config": {
            "bucket_name": "a-bucket",
            "region": "us-east-1",
            "prefix": "a-key",
            "aws_access_key_id": "object_storage_root_user",
            "aws_secret_access_key": "object_storage_root_password",
        },
    }

    batch_export_data = {
        "name": "my-production-s3-bucket-destination",
        "destination": destination_data,
        "interval": "hour",
    }

    batch_export = await acreate_batch_export(
        team_id=ateam.pk,
        name=batch_export_data["name"],  # type: ignore
        destination_data=batch_export_data["destination"],  # type: ignore
        interval=batch_export_data["interval"],  # type: ignore
    )

    yield batch_export

    await adelete_batch_export(batch_export, temporal_client)


async def test_batch_export_run_is_set_to_running(ateam, s3_batch_export):
    """Test background task sets batch export to running."""
    some_date = dt.datetime(2021, 12, 5, 13, 23, 0, tzinfo=dt.UTC)

    run = await BatchExportRun.objects.acreate(
        batch_export_id=s3_batch_export.id,
        data_interval_end=some_date,
        data_interval_start=some_date - dt.timedelta(hours=1),
        status=BatchExportRun.Status.STARTING,
    )

    logger = await bind_temporal_worker_logger(team_id=ateam.pk, destination="S3")

    async with set_status_to_running_task(run_id=str(run.id), logger=logger) as task:
        assert task is not None

        await asyncio.wait([task])

        assert task.done()
        assert task.exception() is None

    await run.arefresh_from_db()
    assert run.status == BatchExportRun.Status.RUNNING

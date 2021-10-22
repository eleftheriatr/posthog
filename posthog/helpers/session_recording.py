import base64
import dataclasses
import gzip
import json
from collections import defaultdict
from typing import Dict, Generator, List, Union, cast

from sentry_sdk.api import capture_exception, capture_message

from posthog.models import utils

Event = Dict
SnapshotData = Dict


@dataclasses.dataclass
class PaginatedChunkInformation:
    has_next: bool
    chunk_ids_or_events_to_decompress: List[Union[str, SnapshotData]]
    chunks_collector: Dict[str, List[SnapshotData]]


FULL_SNAPSHOT = 2


def preprocess_session_recording_events(events: List[Event]) -> List[Event]:
    result = []
    snapshots_by_session = defaultdict(list)
    for event in events:
        if is_unchunked_snapshot(event):
            session_recording_id = event["properties"]["$session_id"]
            snapshots_by_session[session_recording_id].append(event)
        else:
            result.append(event)

    for session_recording_id, snapshots in snapshots_by_session.items():
        result.extend(list(compress_and_chunk_snapshots(snapshots)))

    return result


def compress_and_chunk_snapshots(events: List[Event], chunk_size=512 * 1024) -> Generator[Event, None, None]:
    data_list = [event["properties"]["$snapshot_data"] for event in events]
    session_id = events[0]["properties"]["$session_id"]
    has_full_snapshot = any(snapshot_data["type"] == FULL_SNAPSHOT for snapshot_data in data_list)

    compressed_data = compress_to_string(json.dumps(data_list))

    id = str(utils.UUIDT())
    chunks = chunk_string(compressed_data, chunk_size)
    for index, chunk in enumerate(chunks):
        yield {
            **events[0],
            "properties": {
                **events[0]["properties"],
                "$session_id": session_id,
                "$snapshot_data": {
                    "chunk_id": id,
                    "chunk_index": index,
                    "chunk_count": len(chunks),
                    "data": chunk,
                    "compression": "gzip-base64",
                    "has_full_snapshot": has_full_snapshot,
                },
            },
        }


def decompress_chunked_snapshot_data(
    team_id: int, session_recording_id: str, snapshot_list: List[SnapshotData]
) -> Generator[SnapshotData, None, None]:
    chunks_collector = defaultdict(list)
    for snapshot_data in snapshot_list:
        if "chunk_id" not in snapshot_data:
            yield snapshot_data
        else:
            chunks_collector[snapshot_data["chunk_id"]].append(snapshot_data)

    for chunks in chunks_collector.values():
        if len(chunks) != chunks[0]["chunk_count"]:
            capture_message(
                "Did not find all session recording chunks! Team: {}, Session: {}".format(team_id, session_recording_id)
            )
            continue

        b64_compressed_data = "".join(chunk["data"] for chunk in sorted(chunks, key=lambda c: c["chunk_index"]))
        decompressed_data = json.loads(decompress(b64_compressed_data))

        yield from decompressed_data


def chunk_string(string: str, chunk_length: int) -> List[str]:
    """Split a string into chunk_length-sized elements. Reversal operation: `''.join()`."""
    return [string[0 + offset : chunk_length + offset] for offset in range(0, len(string), chunk_length)]


def is_unchunked_snapshot(event: Dict) -> bool:
    try:
        is_snapshot = event["event"] == "$snapshot"
    except KeyError:
        raise ValueError('All events must have the event name field "event"!')
    try:
        return is_snapshot and "chunk_id" not in event["properties"]["$snapshot_data"]
    except KeyError:
        capture_exception()
        raise ValueError('$snapshot events must contain property "$snapshot_data"!')


def compress_to_string(json_string: str) -> str:
    compressed_data = gzip.compress(json_string.encode("utf-16", "surrogatepass"))
    return base64.b64encode(compressed_data).decode("utf-8")


def decompress(base64data: str) -> str:
    compressed_bytes = base64.b64decode(base64data)
    return gzip.decompress(compressed_bytes).decode("utf-16", "surrogatepass")


def preprocess_chunks_for_paginated_decompression(
    all_recording_snapshots: Union[List[SnapshotData]], limit: int, offset: int
) -> PaginatedChunkInformation:
    has_next = False
    chunk_ids_passed = set()
    chunk_ids_or_events_to_decompress: List[Union[str, SnapshotData]] = []
    chunks_collector: Dict[str, List[SnapshotData]] = {}
    chunks_or_event_counter = 0

    # Get the chunks/events that should be decompressed based on the limit/offset
    for snapshot in all_recording_snapshots:
        chunk_id = snapshot.get("chunk_id")

        # If we haven't hit the offset, keep counting chunks/events until its hit
        if chunks_or_event_counter < offset:
            if not chunk_id:
                chunks_or_event_counter += 1
            elif chunk_id not in chunk_ids_passed:
                chunk_ids_passed.add(chunk_id)
                chunks_or_event_counter += 1

        # If we're past the offset and within the limit
        elif chunks_or_event_counter < offset + limit:
            if not chunk_id:
                chunks_or_event_counter += 1
                chunk_ids_or_events_to_decompress.append(snapshot)
            elif chunk_id not in chunk_ids_passed:
                if chunk_id in chunks_collector.keys():
                    chunks_collector[chunk_id].append(snapshot)
                else:
                    chunks_or_event_counter += 1
                    chunks_collector[chunk_id] = [snapshot]
                    chunk_ids_or_events_to_decompress.append(chunk_id)

        # If we're past the limit,
        else:
            # We encounter a new chunk_id or event
            if not chunk_id or (chunk_id not in chunk_ids_passed and chunk_id not in chunks_collector.keys()):
                has_next = True
            # We encounter a part of a previously added chunk
            elif chunk_id in chunks_collector.keys():
                chunks_collector[chunk_id].append(snapshot)
    return PaginatedChunkInformation(
        has_next=has_next,
        chunk_ids_or_events_to_decompress=chunk_ids_or_events_to_decompress,
        chunks_collector=chunks_collector,
    )


def paginate_chunk_decompression(
    team_id: int, session_recording_id: str, all_recording_snapshots: List[SnapshotData], limit: int, offset: int
):
    paginated_chunk_information = preprocess_chunks_for_paginated_decompression(all_recording_snapshots, limit, offset)

    # Decompress the chunks
    decompressed_data_list: List[SnapshotData] = []
    for chunk_id_or_event in paginated_chunk_information.chunk_ids_or_events_to_decompress:
        # Chunk id
        if type(chunk_id_or_event) == str:
            chunks = paginated_chunk_information.chunks_collector[cast(str, chunk_id_or_event)]
            if len(chunks) != chunks[0]["chunk_count"]:
                capture_message(
                    "Did not find all session recording chunks! Team: {}, Session: {}, Chunk-id: {}. Found {} of {} chunks".format(
                        team_id, session_recording_id, chunk_id_or_event, len(chunks), chunks[0]["chunk_count"],
                    )
                )
                continue

            b64_compressed_data = "".join(chunk["data"] for chunk in sorted(chunks, key=lambda c: c["chunk_index"]))
            decompressed_data = json.loads(decompress(b64_compressed_data))

            decompressed_data_list.extend(decompressed_data)

        else:
            decompressed_data_list.append(cast(SnapshotData, chunk_id_or_event))

    return (
        paginated_chunk_information.has_next,
        decompressed_data_list,
    )

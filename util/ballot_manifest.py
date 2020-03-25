import csv
import io
import locale
import uuid
from sqlalchemy.orm.session import Session
from typing import Dict, List, Tuple
from werkzeug.exceptions import BadRequest

from audit_math import sampler, sampler_contest
from arlo_server.models import (
    Batch,
    Election,
    File,
    Jurisdiction,
    Round,
    SampledBallot,
    SampledBallotDraw,
)
from util.binpacking import BalancedBucketList, Bucket
from util.process_file import process_file

BATCH_NAME = "Batch Name"
NUMBER_OF_BALLOTS = "Number of Ballots"
STORAGE_LOCATION = "Storage Location"
TABULATOR = "Tabulator"


def process_ballot_manifest_file(
    session: Session, jurisdiction: Jurisdiction, file: File
):
    assert jurisdiction.manifest_file_id == file.id

    def process():
        manifest_csv = csv.DictReader(io.StringIO(file.contents))

        missing_fields = [
            field
            for field in [BATCH_NAME, NUMBER_OF_BALLOTS]
            if field not in manifest_csv.fieldnames
        ]

        if missing_fields:
            raise Exception(f"Missing required CSV fields: {', '.join(missing_fields)}")

        num_batches = 0
        num_ballots = 0
        for row in manifest_csv:
            num_ballots_in_batch_csv = row[NUMBER_OF_BALLOTS]

            try:
                num_ballots_in_batch = locale.atoi(num_ballots_in_batch_csv)
            except ValueError as error:
                raise Exception(
                    f"Invalid value for '{NUMBER_OF_BALLOTS}' on line {manifest_csv.line_num}: {num_ballots_in_batch}"
                ) from error

            batch = Batch(
                id=str(uuid.uuid4()),
                name=row[BATCH_NAME],
                jurisdiction_id=jurisdiction.id,
                num_ballots=num_ballots_in_batch,
                storage_location=row.get(STORAGE_LOCATION, None),
                tabulator=row.get(TABULATOR, None),
            )
            session.add(batch)
            num_batches += 1
            num_ballots += batch.num_ballots

        jurisdiction.manifest_num_ballots = num_ballots
        jurisdiction.manifest_num_batches = num_batches

    process_file(session, file, process)

    election = jurisdiction.election

    # If we're in the single-jurisdiction flow, posting the ballot manifest
    # starts the first round, so we need to sample the ballots.
    # In the multi-jurisdiction flow, this happens after all jurisdictions
    # upload manifests, and is triggered by a different endpoint.
    if not election.is_multi_jurisdiction:
        sample_ballots(session, election, election.rounds[0])


def sample_ballots(session: Session, election: Election, round: Round):
    # assume only one contest
    round_contest = round.round_contests[0]
    jurisdiction = election.jurisdictions[0]

    num_sampled = (
        session.query(SampledBallotDraw)
        .join(SampledBallotDraw.batch)
        .filter_by(jurisdiction_id=jurisdiction.id)
        .count()
    )
    if not num_sampled:
        num_sampled = 0

    chosen_sample_size = round_contest.sample_size

    # the sampler needs to have the same inputs given the same manifest
    # so we use the batch name, rather than the batch id
    # (because the batch ID is an internally generated uuid
    #  that changes from one run to the next.)
    manifest = {}
    batch_id_from_name = {}
    for batch in jurisdiction.batches:
        manifest[batch.name] = batch.num_ballots
        batch_id_from_name[batch.name] = batch.id

    sample = sampler.draw_sample(
        election.random_seed, manifest, chosen_sample_size, num_sampled=num_sampled,
    )

    audit_boards = jurisdiction.audit_boards

    batch_sizes: Dict[str, int] = {}
    batches_to_ballots: Dict[str, List[Tuple[int, str, int]]] = {}
    # Build batch - batch_size map
    for (ticket_number, (batch_name, ballot_position), sample_number) in sample:
        if batch_name in batch_sizes:
            if (
                sample_number == 1
            ):  # if we've already seen it, it doesn't affect batch size
                batch_sizes[batch_name] += 1
            batches_to_ballots[batch_name].append(
                (ballot_position, ticket_number, sample_number)
            )
        else:
            batch_sizes[batch_name] = 1
            batches_to_ballots[batch_name] = [
                (ballot_position, ticket_number, sample_number)
            ]

    # Create the buckets and initially assign batches
    buckets = [Bucket(audit_board.name) for audit_board in audit_boards]
    for i, batch in enumerate(batch_sizes):
        buckets[i % len(audit_boards)].add_batch(batch, batch_sizes[batch])

    # Now assign batchest fairly
    bl = BalancedBucketList(buckets)

    # read audit board and batch info out
    for audit_board_num, bucket in enumerate(bl.buckets):
        audit_board = audit_boards[audit_board_num]
        for batch_name in bucket.batches:

            for (ballot_position, ticket_number, sample_number) in batches_to_ballots[
                batch_name
            ]:
                # sampler is 0-indexed, we're 1-indexing here
                ballot_position += 1

                batch_id = batch_id_from_name[batch_name]

                if sample_number == 1:
                    sampled_ballot = SampledBallot(
                        batch_id=batch_id,
                        ballot_position=ballot_position,
                        audit_board_id=audit_board.id,
                    )
                    session.add(sampled_ballot)

                sampled_ballot_draw = SampledBallotDraw(
                    batch_id=batch_id,
                    ballot_position=ballot_position,
                    round_id=round.id,
                    ticket_number=ticket_number,
                )

                session.add(sampled_ballot_draw)

    session.commit()

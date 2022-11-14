# pylint: disable=invalid-name
import csv
import sys
from server.models import BatchInventoryData, Election
from server.util.file import serialize_file_processing


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.batch-inventory-progress <election_id>")
        sys.exit(1)

    election_id = sys.argv[1]
    election = Election.query.get(election_id)
    if not election:
        print("Audit not found")
        sys.exit(1)

    writer = csv.writer(sys.stdout)
    writer.writerow(["Jurisdiction", "CVR File", "Tabulator Status File", "Signed Off"])

    def file_status(file):
        if not file:
            return "NOT_UPLOADED"
        status = serialize_file_processing(file)["status"]
        if status == "PROCESSED":
            return "UPLOADED"
        if status == "ERRORED":
            return "ERROR"
        return "UPLOAD_IN_PROGRESS"

    for jurisdiction in election.jurisdictions:
        batch_inventory_data = BatchInventoryData.query.get(jurisdiction.id)
        if not batch_inventory_data:
            writer.writerow(
                [jurisdiction.name, "NOT_UPLOADED", "NOT_UPLOADED", "NO",]
            )
            continue
        writer.writerow(
            [
                jurisdiction.name,
                file_status(batch_inventory_data.cvr_file),
                file_status(batch_inventory_data.tabulator_status_file),
                "YES" if batch_inventory_data.signed_off_at else "NO",
            ]
        )

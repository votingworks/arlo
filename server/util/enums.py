import enum


CONTAINER = "Container"
TABULATOR = "Tabulator"
BATCH_NAME = "Batch Name"
NUMBER_OF_BALLOTS = "Number of Ballots"
CVR = "CVR"


class ContainerType(str, enum.Enum):
    ADVANCED_VOTING = "Advanced Voting"
    ADVANCE_VOTING = "Advance Voting"
    ELECTION_DAY = "Election Day"
    ELECTIONS_DAY = "Elections Day"
    ABSENTEE_BY_MAIL = "Absentee by Mail"
    PROVISIONAL = "Provisional"

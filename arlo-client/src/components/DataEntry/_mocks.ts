import { IAuditBoard, IBallot, BallotStatus, Interpretation } from '../../types'

export const contest = {
  choices: [
    {
      id: 'choice-1',
      name: 'choice one',
      numVotes: 792,
    },
    {
      id: 'choice-2',
      name: 'choice two',
      numVotes: 1325,
    },
  ],
  id: 'contest-1',
  name: 'contest name',
  numWinners: '1',
  votesAllowed: '1',
  totalBallotsCast: '2123',
  isTargeted: true,
  jurisdictionIds: [],
}

export const doneDummyBallots: { ballots: IBallot[] } = {
  ballots: [
    {
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id-1',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id-1',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id-1',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
  ],
}

export const dummyBallots: { ballots: IBallot[] } = {
  ballots: [
    {
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id-1',
        tabulator: null,
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [
        {
          contestId: contest.id,
          interpretation: Interpretation.VOTE,
          choiceId: contest.choices[0].id,
          comment: 'Good ballot',
        },
      ],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id-1',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.NOT_AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id-1',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id-2',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id-2',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.NOT_AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id-2',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id-3',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id-3',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.NOT_AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id-3',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id-4',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id-4',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.NOT_AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id-4',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id-5',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id-5',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.NOT_AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id-5',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id-6',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id-6',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.NOT_AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id-6',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id-7',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id-7',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.NOT_AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id-7',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id-8',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id-8',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.NOT_AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id-8',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id-9',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id-9',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.NOT_AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id-9',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
    },
  ],
}

export const dummyBoard: IAuditBoard[] = [
  {
    id: '123',
    name: 'Audit Board #1',
    members: [],
  },
  {
    id: '123',
    name: 'Audit Board #1',
    members: [
      {
        name: 'John Doe',
        affiliation: '',
      },
      {
        name: 'Jane Doe',
        affiliation: 'LIB',
      },
    ],
  },
]

export default {
  dummyBoard,
  dummyBallots,
}

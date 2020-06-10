import { IAuditBoard, BallotStatus, Interpretation } from '../../types'
import { contestMocks } from '../MultiJurisdictionAudit/Setup/Contests/_mocks'
import { IBallot } from './Ballot'

export const contest = contestMocks.filledTargeted.contests[0]

export const doneDummyBallots: { ballots: IBallot[] } = {
  ballots: [
    {
      id: 'ballot-id-1',
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id-1',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-2',
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id-1',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-3',
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id-1',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-4',
      batch: {
        name: '0003-04-Precinct 31 (Jonesboro Fire Department)',
        id: 'batch-id-1',
        tabulator: '11',
      },
      position: 1965,
      status: BallotStatus.NOT_FOUND,
      interpretations: [],
    },
  ],
}

export const dummyBallots: { ballots: IBallot[] } = {
  ballots: [
    {
      id: 'ballot-id-1',
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
          choiceIds: [contest.choices[0].id],
          comment: 'Good ballot',
        },
      ],
    },
    {
      id: 'ballot-id-2',
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id-1',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.NOT_AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-3',
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id-1',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-4',
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id-2',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-5',
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id-2',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.NOT_AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-6',
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id-2',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-7',
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id-3',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-8',
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id-3',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.NOT_AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-9',
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id-3',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-10',
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id-4',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-11',
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id-4',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.NOT_AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-12',
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id-4',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-13',
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id-5',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-14',
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id-5',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.NOT_AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-15',
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id-5',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-16',
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id-6',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-17',
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id-6',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.NOT_AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-18',
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id-6',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-19',
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id-7',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-20',
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id-7',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.NOT_AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-21',
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id-7',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-22',
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id-8',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-23',
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id-8',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.NOT_AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-24',
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id-8',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-25',
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id-9',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-26',
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id-9',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.NOT_AUDITED,
      interpretations: [],
    },
    {
      id: 'ballot-id-27',
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id-9',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
    },
  ],
}

export const dummyBoards = (): IAuditBoard[] => [
  {
    id: 'audit-board-1',
    name: 'Audit Board #1',
    jurisdictionId: 'jurisdiction-1',
    jurisdictionName: 'Jurisdiction 1',
    roundId: 'round-1',
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
    signedOffAt: null,
  },
  {
    id: 'audit-board-2',
    name: 'Audit Board #2',
    jurisdictionId: 'jurisdiction-1',
    jurisdictionName: 'Jurisdiction 1',
    roundId: 'round-1',
    members: [],
    signedOffAt: null,
  },
]

export default {
  dummyBoards,
  dummyBallots,
}

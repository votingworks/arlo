import { IAudit, IBallot, BallotStatus } from '../../types'

export const statusStates: {
  [key in
    | 'empty'
    | 'contestFirstRound'
    | 'sampleSizeOptions'
    | 'jurisdictionsInitial'
    | 'ballotManifestProcessed'
    | 'ballotManifestProcessError'
    | 'completeInFirstRound'
    | 'firstRoundSampleSizeOptionsNull'
    | 'firstRoundSampleSizeOptions'
    | 'multiAuditBoardsAndRounds'
    | 'isMultiJurisdiction']: IAudit
} = {
  empty: {
    name: '',
    riskLimit: '',
    frozenAt: null,
    online: true,
    randomSeed: '',
    contests: [],
    jurisdictions: [],
    rounds: [],
    isMultiJurisdiction: false,
  },
  contestFirstRound: {
    contests: [
      {
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
      },
    ],
    jurisdictions: [],
    rounds: [
      {
        contests: [
          {
            endMeasurements: {
              isComplete: null,
              pvalue: null,
            },
            id: 'contest-1',
            results: {},
            sampleSize: null,
            sampleSizeOptions: null,
          },
        ],
        endedAt: null,
        isAuditComplete: false,
        startedAt: '2019-07-18T16:34:07.000Z',
        id: 'round-1',
      },
    ],
    name: 'contest name',
    randomSeed: '12345678901234567890abcdefghijklmnopqrstuvwxyz😊',
    riskLimit: '1',
    frozenAt: null,
    online: true,
    isMultiJurisdiction: false,
  },
  sampleSizeOptions: {
    contests: [
      {
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
      },
    ],
    jurisdictions: [],
    rounds: [
      {
        contests: [
          {
            endMeasurements: {
              isComplete: null,
              pvalue: null,
            },
            id: 'contest-1',
            results: {},
            sampleSize: null,
            sampleSizeOptions: [
              { size: 269, type: 'ASN', prob: null },
              { size: 379, prob: 0.8, type: null },
              { size: 78, prob: null, type: null },
            ],
          },
        ],
        endedAt: null,
        isAuditComplete: false,
        startedAt: '2019-07-18T16:34:07.000Z',
        id: 'round-1',
      },
    ],
    name: 'contest name',
    randomSeed: '123456789',
    riskLimit: '1',
    frozenAt: null,
    online: true,
    isMultiJurisdiction: false,
  },
  jurisdictionsInitial: {
    contests: [
      {
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
        totalBallotsCast: '2123',
        isTargeted: true,
        numWinners: '1',
        votesAllowed: '1',
        jurisdictionIds: [],
      },
    ],
    jurisdictions: [
      {
        auditBoards: [
          {
            id: 'audit-board-1',
            name: 'Audit Board #1',
            members: [],
          },
        ],
        ballotManifest: {
          filename: null,
          numBallots: null,
          numBatches: null,
          uploadedAt: null,
          processing: null,
        },
        batches: [
          {
            id: 'batch-1',
            name: 'Batch One',
            numBallots: 12,
            tabulator: null,
          },
        ],
        contests: ['contest-1'],
        id: 'jurisdiction-1',
        name: 'Jurisdiction 1',
      },
    ],
    rounds: [
      {
        contests: [
          {
            endMeasurements: {
              isComplete: null,
              pvalue: null,
            },
            id: 'contest-1',
            results: {},
            sampleSize: null,
            sampleSizeOptions: [
              { size: 269, type: 'ASN', prob: null },
              { size: 379, prob: 0.8, type: null },
              { size: 78, prob: null, type: null },
            ],
          },
        ],
        endedAt: null,
        isAuditComplete: false,
        startedAt: '2019-07-18T16:34:07.000Z',
        id: 'round-1',
      },
    ],
    name: 'contest name',
    randomSeed: '12345678901234567890abcdefghijklmnopqrstuvwxyz😊',
    riskLimit: '1',
    frozenAt: null,
    online: true,
    isMultiJurisdiction: false,
  },
  ballotManifestProcessed: {
    contests: [
      {
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
      },
    ],
    jurisdictions: [
      {
        auditBoards: [
          {
            id: 'audit-board-1',
            name: 'Audit Board #1',
            members: [],
          },
        ],
        ballotManifest: {
          filename: 'Ballot Manifest May 2019 Election - WYNADOTTE.csv',
          numBallots: 2117,
          numBatches: 10,
          uploadedAt: '2019-07-18T16:34:07.000Z',
          processing: { status: 'PROCESSED' },
        },
        contests: ['contest-1'],
        id: 'jurisdiction-1',
        name: 'Jurisdiction 1',
      },
    ],
    rounds: [
      {
        contests: [
          {
            endMeasurements: {
              isComplete: null,
              pvalue: null,
            },
            id: 'contest-1',
            results: {},
            sampleSize: 379,
            sampleSizeOptions: [
              { size: 269, type: 'ASN', prob: null },
              { size: 379, prob: 0.8, type: null },
              { size: 78, prob: null, type: null },
            ],
          },
        ],
        endedAt: null,
        isAuditComplete: false,
        startedAt: '2019-07-18T16:34:07.000Z',
        id: 'round-1',
      },
    ],
    name: 'contest name',
    randomSeed: '12345678901234567890abcdefghijklmnopqrstuvwxyz😊',
    riskLimit: '1',
    frozenAt: null,
    online: true,
    isMultiJurisdiction: false,
  },
  ballotManifestProcessError: {
    contests: [
      {
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
      },
    ],
    jurisdictions: [
      {
        auditBoards: [
          {
            id: 'audit-board-1',
            name: 'Audit Board #1',
            members: [],
          },
        ],
        ballotManifest: {
          filename: 'Ballot Manifest May 2019 Election - WYNADOTTE.csv',
          numBallots: 2117,
          numBatches: 10,
          uploadedAt: '2019-07-18T16:34:07.000Z',
          processing: { status: 'ERRORED' },
        },
        contests: ['contest-1'],
        id: 'jurisdiction-1',
        name: 'Jurisdiction 1',
      },
    ],
    rounds: [
      {
        contests: [
          {
            endMeasurements: {
              isComplete: null,
              pvalue: null,
            },
            id: 'contest-1',
            results: {},
            sampleSize: 379,
            sampleSizeOptions: [
              { size: 269, type: 'ASN', prob: null },
              { size: 379, prob: 0.8, type: null },
              { size: 78, prob: null, type: null },
            ],
          },
        ],
        endedAt: null,
        isAuditComplete: false,
        startedAt: '2019-07-18T16:34:07.000Z',
        id: 'round-1',
      },
    ],
    name: 'contest name',
    randomSeed: '12345678901234567890abcdefghijklmnopqrstuvwxyz😊',
    riskLimit: '1',
    frozenAt: null,
    online: true,
    isMultiJurisdiction: false,
  },
  completeInFirstRound: {
    contests: [
      {
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
      },
    ],
    jurisdictions: [
      {
        auditBoards: [
          {
            id: 'audit-board-1',
            name: 'Audit Board #1',
            members: [],
          },
        ],
        ballotManifest: {
          filename: 'Ballot Manifest May 2019 Election - WYNADOTTE.csv',
          numBallots: 2117,
          numBatches: 10,
          uploadedAt: '2019-07-18T16:34:07.000Z',
          processing: { status: 'PROCESSED' },
        },
        contests: ['contest-1'],
        id: 'jurisdiction-1',
        name: 'Jurisdiction 1',
      },
    ],
    rounds: [
      {
        contests: [
          {
            endMeasurements: {
              isComplete: true,
              pvalue: 0.00020431431380638307,
            },
            id: 'contest-1',
            results: {
              'choice-1': 100,
              'choice-2': 167,
            },
            sampleSize: 379,
            sampleSizeOptions: [
              { size: 269, type: 'ASN', prob: null },
              { size: 379, prob: 0.8, type: null },
              { size: 78, prob: null, type: null },
            ],
          },
        ],
        endedAt: '2019-07-18T16:59:34.000Z',
        isAuditComplete: true,
        startedAt: '2019-07-18T16:34:07.000Z',
        id: 'round-1',
      },
    ],
    name: 'contest name',
    randomSeed: '12345678901234567890abcdefghijklmnopqrstuvwxyz😊',
    riskLimit: '1',
    frozenAt: null,
    online: true,
    isMultiJurisdiction: false,
  },
  firstRoundSampleSizeOptionsNull: {
    contests: [
      {
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
        totalBallotsCast: '2123',
        isTargeted: true,
        numWinners: '1',
        votesAllowed: '1',
        jurisdictionIds: [],
      },
    ],
    jurisdictions: [
      {
        auditBoards: [
          {
            id: 'audit-board-1',
            name: 'Audit Board #1',
            members: [],
          },
        ],
        ballotManifest: {
          filename: 'Ballot Manifest May 2019 Election - WYNADOTTE.csv',
          numBallots: 2117,
          numBatches: 10,
          uploadedAt: '2019-07-18T16:34:07.000Z',
          processing: { status: 'PROCESSED' },
        },
        contests: ['contest-1'],
        id: 'jurisdiction-1',
        name: 'Jurisdiction 1',
      },
    ],
    rounds: [
      {
        contests: [
          {
            endMeasurements: {
              isComplete: null,
              pvalue: null,
            },
            id: 'contest-1',
            results: {},
            sampleSize: null,
            sampleSizeOptions: null,
          },
        ],
        endedAt: null,
        isAuditComplete: false,
        startedAt: '2019-07-18T16:34:07.000Z',
        id: 'round-1',
      },
    ],
    name: 'contest name',
    randomSeed: '12345678901234567890abcdefghijklmnopqrstuvwxyz😊',
    riskLimit: '1',
    frozenAt: null,
    online: true,
    isMultiJurisdiction: false,
  },
  firstRoundSampleSizeOptions: {
    contests: [
      {
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
        totalBallotsCast: '2123',
        isTargeted: true,
        numWinners: '1',
        votesAllowed: '1',
        jurisdictionIds: [],
      },
    ],
    jurisdictions: [
      {
        auditBoards: [
          {
            id: 'audit-board-1',
            name: 'Audit Board #1',
            members: [],
          },
          {
            id: 'audit-board-2',
            name: 'Audit Board #2',
            members: [],
          },
          {
            id: 'audit-board-3',
            name: 'Audit Board #3',
            members: [],
          },
        ],
        ballotManifest: {
          filename: null,
          numBallots: null,
          numBatches: null,
          uploadedAt: null,
          processing: null,
        },
        batches: [
          {
            id: 'batch-1',
            name: 'Batch One',
            numBallots: 12,
            tabulator: null,
          },
        ],
        contests: ['contest-1'],
        id: 'jurisdiction-1',
        name: 'Jurisdiction 1',
      },
    ],
    rounds: [
      {
        contests: [
          {
            endMeasurements: {
              isComplete: null,
              pvalue: null,
            },
            id: 'contest-1',
            results: {},
            sampleSize: null,
            sampleSizeOptions: [
              { size: 269, type: 'ASN', prob: null },
              { size: 379, prob: 0.8, type: null },
              { size: 78, prob: null, type: null },
            ],
          },
        ],
        endedAt: null,
        isAuditComplete: false,
        startedAt: '2019-07-18T16:34:07.000Z',
        id: 'round-1',
      },
    ],
    name: 'contest name',
    randomSeed: '12345678901234567890abcdefghijklmnopqrstuvwxyz😊',
    riskLimit: '1',
    frozenAt: null,
    online: true,
    isMultiJurisdiction: false,
  },
  multiAuditBoardsAndRounds: {
    contests: [
      {
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
        totalBallotsCast: '2123',
        isTargeted: true,
        numWinners: '1',
        votesAllowed: '1',
        jurisdictionIds: [],
      },
    ],
    jurisdictions: [
      {
        auditBoards: [
          {
            id: 'audit-board-1',
            name: 'Audit Board #1',
            members: [],
          },
          {
            id: 'audit-board-2',
            name: 'Audit Board #2',
            members: [],
          },
          {
            id: 'audit-board-3',
            name: 'Audit Board #3',
            members: [],
          },
        ],
        ballotManifest: {
          filename: null,
          numBallots: null,
          numBatches: null,
          uploadedAt: null,
          processing: null,
        },
        batches: [
          {
            id: 'batch-1',
            name: 'Batch One',
            numBallots: 12,
            tabulator: null,
          },
        ],
        contests: ['contest-1'],
        id: 'jurisdiction-1',
        name: 'Jurisdiction 1',
      },
    ],
    rounds: [
      {
        contests: [
          {
            endMeasurements: {
              isComplete: false,
              pvalue: 1,
            },
            id: 'contest-1',
            results: {
              'choice-1': 0,
              'choice-2': 0,
            },
            sampleSize: null,
            sampleSizeOptions: [
              { size: 269, type: 'ASN', prob: null },
              { size: 379, prob: 0.8, type: null },
              { size: 78, prob: null, type: null },
            ],
          },
        ],
        endedAt: '2019-07-18T16:35:07.000Z',
        isAuditComplete: true,
        startedAt: '2019-07-18T16:34:07.000Z',
        id: 'round-1',
      },
      {
        contests: [
          {
            endMeasurements: {
              isComplete: null,
              pvalue: null,
            },
            id: 'contest-1',
            results: {},
            sampleSize: null,
            sampleSizeOptions: [
              { size: 269, type: 'ASN', prob: null },
              { size: 379, prob: 0.8, type: null },
              { size: 78, prob: null, type: null },
            ],
          },
        ],
        endedAt: null,
        isAuditComplete: false,
        startedAt: '2019-07-18T16:34:07.000Z',
        id: 'round-1',
      },
    ],
    name: 'contest name',
    randomSeed: '12345678901234567890abcdefghijklmnopqrstuvwxyz😊',
    riskLimit: '1',
    frozenAt: null,
    online: true,
    isMultiJurisdiction: false,
  },
  isMultiJurisdiction: {
    name: '',
    riskLimit: '',
    frozenAt: null,
    online: true,
    randomSeed: '',
    contests: [],
    jurisdictions: [],
    rounds: [],
    isMultiJurisdiction: true,
  },
}

export const ballotManifest = new File(
  ['ballot manifest'],
  'ballotManifest.csv',
  { type: 'text/csv' }
)

export const incompleteDummyBallots: { ballots: IBallot[] } = {
  ballots: [
    {
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.NOT_AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
  ],
}

export const dummyBallots: { ballots: IBallot[] } = {
  ballots: [
    {
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 313,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 19 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 2112,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
    {
      batch: {
        name: '0003-04-Precinct 29 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 1789,
      status: BallotStatus.AUDITED,
      interpretations: [],
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
  ],
}

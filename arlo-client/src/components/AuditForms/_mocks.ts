/* eslint-disable no-null/no-null */

import { IAudit, IBallot } from '../../types'

export const statusStates: IAudit[] = [
  {
    name: '',
    riskLimit: '',
    randomSeed: '',
    contests: [],
    jurisdictions: [],
    rounds: [],
  },
  {
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
        winners: '1',
        votesAllowed: '1',
        totalBallotsCast: '2123',
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
        startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
        id: 'round-1',
      },
    ],
    name: 'contest name',
    randomSeed: '12345678901234567890abcdefghijklmnopqrstuvwxyz😊',
    riskLimit: '1',
  },
  {
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
        winners: '1',
        votesAllowed: '1',
        totalBallotsCast: '2123',
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
        startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
        id: 'round-1',
      },
    ],
    name: 'contest name',
    randomSeed: '123456789',
    riskLimit: '1',
  },
  {
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
        winners: '1',
        votesAllowed: '1',
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
        },
        batches: [
          {
            id: 'batch-1',
            name: 'Batch One',
            numBallots: 12,
            storageLocation: null,
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
        startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
        id: 'round-1',
      },
    ],
    name: 'contest name',
    randomSeed: '12345678901234567890abcdefghijklmnopqrstuvwxyz😊',
    riskLimit: '1',
  },
  {
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
        winners: '1',
        votesAllowed: '1',
        totalBallotsCast: '2123',
      },
    ],
    jurisdictions: [
      {
        auditBoards: [
          {
            id: 'audit-board-1',
            name: 'Audit Board #1',
            members: [],
            ballots: [],
          },
        ],
        ballotManifest: {
          filename: 'Ballot Manifest May 2019 Election - WYNADOTTE.csv',
          numBallots: 2117,
          numBatches: 10,
          uploadedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
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
        startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
        id: 'round-1',
      },
    ],
    name: 'contest name',
    randomSeed: '12345678901234567890abcdefghijklmnopqrstuvwxyz😊',
    riskLimit: '1',
  },
  {
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
        winners: '1',
        votesAllowed: '1',
        totalBallotsCast: '2123',
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
          uploadedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
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
        endedAt: 'Thu, 18 Jul 2019 16:59:34 GMT',
        startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
        id: 'round-1',
      },
    ],
    name: 'contest name',
    randomSeed: '12345678901234567890abcdefghijklmnopqrstuvwxyz😊',
    riskLimit: '1',
  },
  {
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
        winners: '1',
        votesAllowed: '1',
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
          uploadedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
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
        startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
        id: 'round-1',
      },
    ],
    name: 'contest name',
    randomSeed: '12345678901234567890abcdefghijklmnopqrstuvwxyz😊',
    riskLimit: '1',
  },
]

export const ballotManifest = new File(
  ['ballot manifest'],
  'ballotManifest.csv',
  { type: 'text/csv' }
)

export const dummyBallots: { ballots: IBallot[] } = {
  ballots: [
    {
      batch: {
        name: '0003-04-Precinct 13 (Jonesboro Fire Department)',
        id: 'batch-id',
        tabulator: '11',
      },
      position: 313,
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
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
      status: 'AUDITED',
      vote: null,
      comment: '',
      timesSampled: 1,
      auditBoard: {
        id: 'audit-board-1',
        name: 'Audit Board #1',
      },
    },
  ],
}

import { Audit } from '../../types'

export const mockAudit: Audit = {
  name: 'Primary 2019',
  riskLimit: 10,
  randomSeed: 123123123,

  contests: [
    {
      id: 'contest-1',
      name: 'Contest 1',

      choices: [
        {
          id: 'candidate-1',
          name: 'Candidate 1',
          numVotes: 42,
        },
        {
          id: 'candidate-2',
          name: 'Candidate 2',
          numVotes: 72,
        },
      ],

      totalBallotsCast: 4200,
    },
  ],

  jurisdictions: [
    {
      id: 'adams-county',
      name: 'Adams County',
      contests: ['contest-1'],
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
      ],
      ballotManifest: {
        filename: 'Adams_County_Manifest.csv',
        numBallots: 123456,
        numBatches: 560,
        uploadedAt: '2019-06-17 11:45:00',
      },
    },
  ],

  rounds: [
    {
      startedAt: '2019-06-17 11:45:00',
      endedAt: '2019-06-17 11:55:00',
      contests: [
        {
          id: 'contest-1',
          endMeasurements: {
            pvalue: 0.085,
            isComplete: false,
          },
          results: {
            'candidate-1': 55,
            'candidate-2': 35,
          },
          sampleSize: 25,
        },
      ],
      jurisdictions: {
        'adams-county': {
          numBallots: 15,
        },
      },
    },
  ],
}

export const statusStates: Audit[] = [
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
        totalBallotsCast: 2123,
        sampleSizeOptions: [
          { size: 269, type: 'ASN' },
          { size: 379, prob: 0.8 },
          { size: 78 },
        ],
      },
    ],
    jurisdictions: [],
    rounds: [],
    name: 'contest name',
    randomSeed: '123456789',
    riskLimit: 1,
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
        totalBallotsCast: 2123,
        sampleSizeOptions: [
          { size: 269, type: 'ASN' },
          { size: 379, prob: 0.8 },
          { size: 78 },
        ],
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
        contests: ['contest-1'],
        id: 'jurisdiction-1',
        name: 'Jurisdiction 1',
      },
    ],
    rounds: [],
    name: 'contest name',
    randomSeed: '123456789',
    riskLimit: 1,
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
        totalBallotsCast: 2123,
        sampleSizeOptions: [
          { size: 269, type: 'ASN' },
          { size: 379, prob: 0.8 },
          { size: 78 },
        ],
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
            sampleSize: 379,
          },
        ],
        endedAt: null,
        startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
      },
    ],
    name: 'contest name',
    randomSeed: '123456789',
    riskLimit: 1,
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
        totalBallotsCast: 2123,
        sampleSizeOptions: [
          { size: 269, type: 'ASN' },
          { size: 379, prob: 0.8 },
          { size: 78 },
        ],
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
          },
        ],
        endedAt: 'Thu, 18 Jul 2019 16:59:34 GMT',
        startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
      },
    ],
    name: 'contest name',
    randomSeed: '123456789',
    riskLimit: 1,
  },
]

export default mockAudit

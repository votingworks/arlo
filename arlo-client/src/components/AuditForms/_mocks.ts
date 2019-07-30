import { Audit } from '../../types'

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

export const estimateSampleSizeMocks = {
  inputs: [
    { key: 'audit-name', value: 'Election Name' },
    { key: 'contest-1-name', value: 'Contest Name' },
    { key: 'contest-1-choice-1-name', value: 'Choice One' },
    { key: 'contest-1-choice-2-name', value: 'Choice Two' },
    { key: 'contest-1-choice-1-votes', value: '10' },
    { key: 'contest-1-choice-2-votes', value: '20' },
    { key: 'contest-1-total-ballots', value: '30' },
    { key: 'risk-limit', value: '2' },
    { key: 'random-seed', value: '123456789' },
  ],
  post: {
    method: 'POST',
    body: {
      name: 'Election Name',
      randomSeed: 123456789,
      riskLimit: 2,
      contests: [
        {
          id: expect.stringMatching(/^\d*$/),
          name: 'Contest Name',
          totalBallotsCast: 30,
          choices: [
            {
              id: expect.stringMatching(/^\d*$/),
              name: 'Choice One',
              numVotes: 10,
            },
            {
              id: expect.stringMatching(/^\d*$/),
              name: 'Choice Two',
              numVotes: 20,
            },
          ],
        },
      ],
    },
    headers: {
      'Content-Type': 'application/json',
    },
  },
}

/*
import { statusStates } from '../AuditForms/_mocks'
import { Audit } from '../../types'

export const api = <T>(endpoint: string, options: any): Promise<T | Audit> => {
    switch (endpoint) {
      case '/audit/status':
        return Promise.resolve(statusStates[0]) as Promise<Audit>
      case '/audit/basic':
        return Promise.resolve({}) as Promise<T>
      default:
        return Promise.reject(new Error('Endpoint not found'))
    }
  }

export default api
*/

export default statusStates

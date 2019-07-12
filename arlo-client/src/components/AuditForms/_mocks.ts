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
          members: [],
        },
        {
          id: 'audit-board-2',
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

export default mockAudit

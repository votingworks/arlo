import { IContest } from '../../../../types'

export const contestMocks: {
  [key: string]: { contests: IContest[] }
} = {
  emptyTargeted: {
    contests: [
      {
        id: '',
        name: '',
        isTargeted: true,
        totalBallotsCast: '',
        numWinners: '1',
        votesAllowed: '1',
        jurisdictionIds: [],
        choices: [
          {
            id: '',
            name: '',
            numVotes: '',
          },
          {
            id: '',
            name: '',
            numVotes: '',
          },
        ],
      },
    ],
  },
  emptyOpportunistic: {
    contests: [
      {
        id: '',
        name: '',
        isTargeted: false,
        totalBallotsCast: '',
        numWinners: '1',
        votesAllowed: '1',
        jurisdictionIds: [],
        choices: [
          {
            id: '',
            name: '',
            numVotes: '',
          },
          {
            id: '',
            name: '',
            numVotes: '',
          },
        ],
      },
    ],
  },
  filledTargeted: {
    contests: [
      {
        id: 'contest-id',
        name: 'Contest Name',
        isTargeted: true,
        totalBallotsCast: '30',
        numWinners: '1',
        votesAllowed: '1',
        jurisdictionIds: [],
        choices: [
          {
            id: 'choice-id-1',
            name: 'Choice One',
            numVotes: '10',
          },
          {
            id: 'choice-id-2',
            name: 'Choice Two',
            numVotes: '20',
          },
        ],
      },
    ],
  },
  filledOpportunistic: {
    contests: [
      {
        id: 'contest-id',
        name: 'Contest Name',
        isTargeted: false,
        totalBallotsCast: '30',
        numWinners: '1',
        votesAllowed: '1',
        jurisdictionIds: [],
        choices: [
          {
            id: 'choice-id-3',
            name: 'Choice Three',
            numVotes: '10',
          },
          {
            id: 'choice-id-4',
            name: 'Choice Four',
            numVotes: '20',
          },
        ],
      },
    ],
  },
  filledTargetedWithJurisdictionId: {
    contests: [
      {
        id: 'contest-id',
        name: 'Contest Name',
        isTargeted: true,
        totalBallotsCast: '30',
        numWinners: '1',
        votesAllowed: '1',
        jurisdictionIds: ['jurisdiction-id-1', 'jurisdiction-id-2'],
        choices: [
          {
            id: 'choice-id-1',
            name: 'Choice One',
            numVotes: '10',
          },
          {
            id: 'choice-id-2',
            name: 'Choice Two',
            numVotes: '20',
          },
        ],
      },
    ],
  },
  filledOpportunisticWithJurisdictionId: {
    contests: [
      {
        id: 'contest-id',
        name: 'Contest Name',
        isTargeted: false,
        totalBallotsCast: '30',
        numWinners: '1',
        votesAllowed: '1',
        jurisdictionIds: ['jurisdiction-id-1', 'jurisdiction-id-2'],
        choices: [
          {
            id: 'choice-id-3',
            name: 'Choice Three',
            numVotes: '10',
          },
          {
            id: 'choice-id-4',
            name: 'Choice Four',
            numVotes: '20',
          },
        ],
      },
    ],
  },
  filledTargetedAndOpportunistic: {
    contests: [
      {
        id: 'contest-id',
        name: 'Contest 1',
        isTargeted: true,
        totalBallotsCast: '30',
        numWinners: '1',
        votesAllowed: '1',
        jurisdictionIds: ['jurisdiction-id-1', 'jurisdiction-id-2'],
        choices: [
          {
            id: 'choice-id-1',
            name: 'Choice One',
            numVotes: '10',
            numVotesCvr: 6,
            numVotesNonCvr: 4,
          },
          {
            id: 'choice-id-2',
            name: 'Choice Two',
            numVotes: '20',
            numVotesCvr: 12,
            numVotesNonCvr: 8,
          },
        ],
      },
      {
        id: 'contest-id-2',
        name: 'Contest 2',
        isTargeted: false,
        totalBallotsCast: '300000',
        numWinners: '2',
        votesAllowed: '2',
        jurisdictionIds: ['jurisdiction-id-1', 'jurisdiction-id-2'],
        choices: [
          {
            id: 'choice-id-3',
            name: 'Choice Three',
            numVotes: '10',
            numVotesCvr: 6,
            numVotesNonCvr: 4,
          },
          {
            id: 'choice-id-4',
            name: 'Choice Four',
            numVotes: '20',
            numVotesCvr: 12,
            numVotesNonCvr: 8,
          },
        ],
      },
    ],
  },
}

export const contestsInputMocks = {
  inputs: [
    { key: 'Contest Name', value: 'Contest Name' },
    { key: 'Name of Candidate/Choice 1', value: 'Choice One' },
    { key: 'Name of Candidate/Choice 2', value: 'Choice Two' },
    { key: 'Votes for Candidate/Choice 1', value: '10' },
    { key: 'Votes for Candidate/Choice 2', value: '20' },
    { key: 'Total Ballots for Contest', value: '30' },
  ],
  errorInputs: [
    { key: 'Contest Name', value: '', error: 'Required' },
    {
      key: 'Total Ballots for Contest',
      value: '',
      error:
        'Must be greater than or equal to the sum of votes for each candidate/choice',
    },
    {
      key: 'Total Ballots for Contest',
      value: 'test',
      error: 'Must be a number',
    },
    {
      key: 'Total Ballots for Contest',
      value: '-1',
      error: 'Must be a positive number',
    },
    {
      key: 'Total Ballots for Contest',
      value: '0.5',
      error: 'Must be an integer',
    },
    { key: 'Name of Candidate/Choice 1', value: '', error: 'Required' },
    { key: 'Name of Candidate/Choice 2', value: '', error: 'Required' },
    {
      key: 'Votes for Candidate/Choice 1',
      value: '',
      error: 'Required',
    },
    {
      key: 'Votes for Candidate/Choice 1',
      value: 'test',
      error: 'Must be a number',
    },
    {
      key: 'Votes for Candidate/Choice 1',
      value: '-1',
      error: 'Must be a positive number',
    },
    {
      key: 'Votes for Candidate/Choice 1',
      value: '0.5',
      error: 'Must be an integer',
    },
    {
      key: 'Votes for Candidate/Choice 2',
      value: '',
      error: 'Required',
    },
    {
      key: 'Votes for Candidate/Choice 2',
      value: 'test',
      error: 'Must be a number',
    },
    {
      key: 'Votes for Candidate/Choice 2',
      value: '-1',
      error: 'Must be a positive number',
    },
    {
      key: 'Votes for Candidate/Choice 2',
      value: '0.5',
      error: 'Must be an integer',
    },
  ],
}

export default contestsInputMocks

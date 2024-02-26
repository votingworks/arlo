export const contestsInputMocks = {
  inputs: [
    { key: 'Contest Name', value: 'Contest Name' },
    { key: 'Name of Candidate/Choice 1', value: 'Choice One' },
    { key: 'Name of Candidate/Choice 2', value: 'Choice Two' },
    { key: 'Votes for Candidate/Choice 1', value: '10' },
    { key: 'Votes for Candidate/Choice 2', value: '20' },
    { key: 'Total Ballot Cards Cast for Contest', value: '30' },
  ],
  batchAuditInputs: {
    contest1: [
      { key: 'Contest Name', value: 'Contest One' },
      { key: 'Name of Candidate/Choice 1', value: 'Choice One' },
      { key: 'Name of Candidate/Choice 2', value: 'Choice Two' },
      { key: 'Votes for Candidate/Choice 1', value: '10' },
      { key: 'Votes for Candidate/Choice 2', value: '20' },
    ],
    contest2: [
      { key: 'Contest 2 Name', value: 'Contest Two' },
      { key: 'Name of Candidate/Choice 1', index: 1, value: 'Choice Three' },
      { key: 'Name of Candidate/Choice 2', index: 1, value: 'Choice Four' },
      { key: 'Votes for Candidate/Choice 1', index: 1, value: '30' },
      { key: 'Votes for Candidate/Choice 2', index: 1, value: '40' },
    ],
  },
  errorInputs: [
    { key: 'Contest Name', value: '', error: 'Required' },
    {
      key: 'Total Ballot Cards Cast for Contest',
      value: '',
      error:
        'Must be greater than or equal to the sum of votes for each candidate/choice',
    },
    {
      key: 'Total Ballot Cards Cast for Contest',
      value: 'test',
      error: 'Must be a number',
    },
    {
      key: 'Total Ballot Cards Cast for Contest',
      value: '-1',
      error: 'Must be a positive number',
    },
    {
      key: 'Total Ballot Cards Cast for Contest',
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

import React from 'react'
// import { render } from '@testing-library/react'
import { shallow } from 'enzyme'
import AuditForms from './RiskLimitingAuditForm'

const mockAudit = {
  name: 'Primary 2019',
  riskLimit: 10,
  randomSeed: 'sdfkjsdflskjfd',

  contests: [
    {
      id: 'contest-1',
      name: 'Contest 1',

      choices: [
        {
          name: 'Candidate 1',
          numVotes: 42,
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

it('renders corretly', () => {
  const container = shallow(<AuditForms />)
  expect(container).toMatchSnapshot()
  container.setState({ mockAudit })
  expect(container).toMatchSnapshot()
})

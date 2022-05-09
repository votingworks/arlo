import React from 'react'
import { render } from '@testing-library/react'

import BatchTallySheet from './BatchTallySheet'

jest.mock('@react-pdf/renderer', () => ({
  ...jest.requireActual('@react-pdf/renderer'),

  // Mock @react-pdf/renderer to generate HTML instead of PDF content for easier testing
  Document: jest.fn(({ children }) => <div>{children}</div>),
  Page: jest.fn(({ children }) => <div>{children}</div>),
  Text: jest.fn(({ children }) => <div>{children}</div>),
  View: jest.fn(({ children }) => <div>{children}</div>),
}))

test('BatchTallySheet renders expected PDF content', async () => {
  const { container } = render(
    <BatchTallySheet
      auditBoardName="Audit Board 1"
      batchName="Batch 1"
      choices={[
        { id: 'choice-1', name: 'Choice 1', numVotes: 0 },
        { id: 'choice-2', name: 'Choice 2', numVotes: 0 },
        { id: 'choice-3', name: 'Choice 3', numVotes: 0 },
      ]}
      jurisdictionName="Jurisdiction 1"
    />
  )
  expect(container).toMatchSnapshot()
})

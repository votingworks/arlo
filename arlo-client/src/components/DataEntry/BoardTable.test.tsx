import React from 'react'
import { render, wait } from '@testing-library/react'
import { StaticRouter } from 'react-router-dom'
import BoardTable from './BoardTable'
import { doneDummyBallots } from './_mocks'

describe('BoardTable', () => {
  it('enables the submit button when all ballots are done', async () => {
    const { container, getByText } = render(
      <StaticRouter>
        <BoardTable
          boardName="Audit Board #1"
          ballots={doneDummyBallots.ballots}
          url="/home"
        />
      </StaticRouter>
    )
    await wait(() => {
      expect(getByText('Audit Board #1: Ballot Cards to Audit')).toBeTruthy()
      const button = getByText('Auditing Complete - Submit Results').closest(
        'a'
      )
      expect(button).toBeTruthy()
      expect(button!.getAttribute('disabled')).toBeFalsy()
      expect(container).toMatchSnapshot()
    })
  })
})

import React from 'react'
import {
  useRouteMatch,
  useLocation,
  Link,
  Switch,
  Route,
  Redirect,
} from 'react-router-dom'
import { IJurisdiction } from '../../UserContext'
import { IRound } from '../../AuditAdmin/useRoundsAuditAdmin'
import { Steps, StepList, StepListItem, stepState } from '../../Atoms/Steps'
import PrepareBatchesStep from './PrepareBatchesStep'
import TallyEntryAccountsStep from './TallyEntryAccountsStep'
import EnterTalliesStep from './EnterTalliesStep'
import { useBatches } from '../useBatchResults'

interface IBatchRoundStepsProps {
  jurisdiction: IJurisdiction
  round: IRound
}

const BatchRoundSteps: React.FC<IBatchRoundStepsProps> = ({
  jurisdiction,
  round,
}) => {
  const { path, url } = useRouteMatch()
  const location = useLocation()
  const batchesQuery = useBatches(
    jurisdiction.election.id,
    jurisdiction.id,
    round.id
  )

  if (!batchesQuery.isSuccess) return null // Still loading
  const { batches } = batchesQuery.data

  const steps = [
    { title: 'Prepare Batches', pathname: `/prepare-batches` },
    { title: 'Set Up Tally Entry Accounts', pathname: `/tally-entry-accounts` },
    { title: 'Enter Tallies', pathname: `/enter-tallies` },
  ]
  const currentStepNumber =
    steps.findIndex(
      ({ pathname }) => `${url}${pathname}` === location.pathname
    ) + 1

  return (
    <Steps>
      <StepList>
        {steps.map(({ title, pathname }, index) => (
          <StepListItem
            key={title}
            state={stepState(index + 1, currentStepNumber)}
            stepNumber={index + 1}
          >
            <Link
              to={`${url}${pathname}`}
              style={{ color: 'inherit', textDecoration: 'inherit' }}
            >
              {title}
            </Link>
          </StepListItem>
        ))}
      </StepList>
      <Switch>
        <Route exact path={`${path}/prepare-batches`}>
          <PrepareBatchesStep
            nextStepUrl={`${url}/tally-entry-accounts`}
            jurisdiction={jurisdiction}
            round={round}
          />
        </Route>
        <Route exact path={`${path}/tally-entry-accounts`}>
          <TallyEntryAccountsStep
            previousStepUrl={`${url}/prepare-batches`}
            nextStepUrl={`${url}/enter-tallies`}
            jurisdiction={jurisdiction}
          />
        </Route>
        <Route exact path={`${path}/enter-tallies`}>
          <EnterTalliesStep
            previousStepUrl={`${url}/tally-entry-accounts`}
            jurisdiction={jurisdiction}
            round={round}
          />
        </Route>
        <Redirect
          to={
            batches.some(batch => batch.resultTallySheets.length > 0)
              ? `${url}/enter-tallies`
              : `${url}/prepare-batches`
          }
        />
      </Switch>
    </Steps>
  )
}

export default BatchRoundSteps

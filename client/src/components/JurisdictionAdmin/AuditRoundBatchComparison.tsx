import React from 'react'
import {
  Button,
  FormGroup,
  Icon,
  H4,
  Text,
  UL,
  Callout,
  Card,
  Colors,
  ControlGroup,
  H5,
  InputGroup,
} from '@blueprintjs/core'
import {
  Switch,
  Redirect,
  Route,
  useRouteMatch,
  useLocation,
  Link,
} from 'react-router-dom'
import { IRound } from '../AuditAdmin/useRoundsAuditAdmin'
import {
  StepListItem,
  StepPanel,
  Steps,
  StepList,
  StepActions,
} from '../Atoms/Steps'
import DownloadBatchTallySheetsButton from './DownloadBatchTallySheetsButton'
import { IJurisdiction } from '../UserContext'
import { ISampleCount } from './useBallots'
import { apiDownload } from '../utilities'
import LinkButton from '../Atoms/LinkButton'
import styled from 'styled-components'
import BatchRoundDataEntry from './BatchRoundDataEntry'
import SegmentedControl from '../Atoms/SegmentedControl'

interface IPrepareBatchesStepProps {
  nextStepUrl: string
  jurisdiction: IJurisdiction
  round: IRound
}

const PrepareBatchesStep: React.FC<IPrepareBatchesStepProps> = ({
  nextStepUrl,
  jurisdiction,
  round,
}) => (
  <>
    <StepPanel style={{ alignItems: 'stretch' }}>
      <SubStep>
        <H5>Retrieve Batches from Storage</H5>
        <p>
          <Button
            icon="download"
            intent="primary"
            onClick={
              /* istanbul ignore next */ // tested in generateSheets.test.tsx
              () =>
                apiDownload(
                  `/election/${jurisdiction.election.id}/jurisdiction/${jurisdiction.id}/round/${round.id}/batches/retrieval-list`
                )
            }
          >
            Download Batch Retrieval List
          </Button>
        </p>
        <p>For each batch in the retrieval list:</p>
        <UL>
          <li>Find the container in storage</li>
          <li>Perform the required chain of custody verification steps</li>
          <li>Take the batch of ballots out of the container and stack them</li>
        </UL>
      </SubStep>
      <SubStep>
        <H5>Print Batch Tally Sheets</H5>
        <p>
          <DownloadBatchTallySheetsButton
            electionId={jurisdiction.election.id}
            jurisdictionId={jurisdiction.id}
            jurisdictionName={jurisdiction.name}
            roundId={round.id}
          />
        </p>
        <p>
          There will be one tally sheet for each batch. Use these tally sheets
          when recording the audited votes in each batch.
        </p>
      </SubStep>
    </StepPanel>
    <StepActions
      right={
        <LinkButton to={nextStepUrl} intent="primary" rightIcon="chevron-right">
          Continue
        </LinkButton>
      }
    />
  </>
)

interface IAuditBoardsStepProps {
  previousStepUrl: string
  nextStepUrl: string
  jurisdiction: IJurisdiction
  round: IRound
  sampleCount: ISampleCount
}

const SubStep = styled.div`
  border-radius: 5px;
  background-color: ${Colors.LIGHT_GRAY5};
  padding: 30px;
  flex: 1;
`

const DigitInput = styled(InputGroup).attrs({})`
  width: 30px;
  margin-right: 7px;
`

const AuditBoardsStep: React.FC<IAuditBoardsStepProps> = ({
  nextStepUrl,
  previousStepUrl,
  jurisdiction,
  round,
  sampleCount,
}) => {
  const loginLinkUrl = `${
    window.location.origin
  }/auditboard/${jurisdiction.name.replace(' ', '').substr(0, 6)}-749`
  const auditBoards = [
    {
      logInConfirmedAt: null,
      members: [
        { name: 'Aaron Michaels' },
        { name: 'Matthew Mitchell Roberts' },
      ],
    },
    {
      logInConfirmedAt: null,
      members: [{ name: 'Kate Bradley' }, { name: 'Sarah Lee' }],
    },
    {
      logInConfirmedAt: new Date().toISOString(),
      members: [{ name: 'John Smith' }, { name: 'Jane Doe' }],
    },
    {
      logInConfirmedAt: new Date().toISOString(),
      members: [{ name: 'Jack Sprat' }, { name: 'Mary White' }],
    },
    {
      logInConfirmedAt: new Date().toISOString(),
      members: [{ name: 'Craig Carlyle' }, { name: 'Janine Trotsky' }],
    },
  ]
  return (
    <>
      <StepPanel>
        {/* <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
          }}
        >
          <div style={{ width: '450px' }}>
            <H4>Do you want to set up additional tally entry accounts?</H4>
            <p>
              Auditors can log into Arlo to enter results for audited batches.
              Whether or not you add auditors, you can always enter or edit
              results yourself.
            </p>
            <div style={{ marginTop: '10px' }}>
              <Button intent="primary">Set Up Tally Entry Accounts</Button>
              <Button style={{ marginLeft: '10px' }}>Skip</Button>
            </div>
          </div>
        </div> */}
        <div style={{ display: 'flex', gap: '20px', justifyContent: 'center' }}>
          <SubStep>
            <H5>Share Tally Entry Login Link</H5>
            <p>
              <InputGroup readOnly value={loginLinkUrl} fill />
            </p>
            <p>
              <Button icon="clipboard">Copy Link</Button>
              <Button
                icon="download"
                intent="primary"
                style={{ marginLeft: '10px' }}
              >
                Download Printout
              </Button>
            </p>
          </SubStep>
          <SubStep style={{ display: 'flex', flexDirection: 'column' }}>
            <H5>Confirm Tally Entry Accounts</H5>
            {auditBoards.length === 0 ? (
              <Card>
                <p>
                  <strong>No tally entry accounts have logged in yet</strong>
                </p>
                <p>
                  Once each audit board logs in, confirm their identity here.
                </p>
              </Card>
            ) : (
              <div style={{ overflowY: 'auto', padding: '1px' }}>
                {auditBoards.map(auditBoard => (
                  <Card
                    key={auditBoard.name}
                    style={{
                      marginBottom: '10px',
                      display: 'grid',
                      gap: '10px',
                      gridTemplateColumns: '1fr 155px',
                      alignItems: 'center',
                      padding: '10px 15px',
                    }}
                  >
                    <div>
                      {auditBoard.members.map(member => (
                        <Text key={member.name}>{member.name}</Text>
                      ))}
                    </div>
                    {auditBoard.logInConfirmedAt ? (
                      <div style={{ paddingLeft: '10px' }}>
                        <Icon icon="tick-circle" intent="primary" />
                        <span style={{ marginLeft: '7px' }}>Logged In</span>
                      </div>
                    ) : (
                      <Button icon="key" intent="warning" minimal>
                        Enter Login Code
                      </Button>
                    )}
                    {/* <Icon icon="key" intent="warning" iconSize={20} />
                        <div style={{ marginLeft: '7px' }}>
                          <label>Enter login code</label>
                          <div style={{ display: 'flex', marginTop: '5px' }}>
                            <DigitInput />
                            <DigitInput />
                            <DigitInput />
                          </div>
                        </div> */}
                  </Card>
                ))}
              </div>
            )}
          </SubStep>
        </div>
      </StepPanel>
      <StepActions
        left={
          <LinkButton to={previousStepUrl} icon="chevron-left">
            Back
          </LinkButton>
        }
        right={
          <LinkButton
            to={nextStepUrl}
            intent="primary"
            rightIcon="chevron-right"
          >
            Continue
          </LinkButton>
        }
      />
    </>
  )
}

interface IAuditBatchesStepProps {
  previousStepUrl: string
  jurisdiction: IJurisdiction
  round: IRound
}

const AuditBatchesStep: React.FC<IAuditBatchesStepProps> = ({
  previousStepUrl,
  jurisdiction,
  round,
}) => (
  <>
    <StepPanel style={{ padding: 0 }}>
      <BatchRoundDataEntry round={round} />
    </StepPanel>
    <StepActions
      left={
        <LinkButton to={previousStepUrl} icon="chevron-left">
          Back
        </LinkButton>
      }
      right={
        <Button intent="primary" disabled>
          Finalize Results
        </Button>
      }
    />
  </>
)

interface IAuditRoundBatchComparisonProps {
  jurisdiction: IJurisdiction
  round: IRound
  sampleCount: ISampleCount
}

const AuditRoundBatchComparison: React.FC<IAuditRoundBatchComparisonProps> = ({
  jurisdiction,
  round,
  sampleCount,
}) => {
  const { path, url } = useRouteMatch()
  const location = useLocation()
  const steps = [
    { title: 'Prepare Batches', pathname: `/prepare-batches` },
    { title: 'Set Up Tally Entry Accounts', pathname: `/audit-boards` },
    { title: 'Enter Tallies', pathname: `/audit-batches` },
  ]
  const currentStepIndex = steps.findIndex(
    ({ pathname }) => `${url}${pathname}` === location.pathname
  )
  return (
    <Steps>
      <StepList>
        {steps.map(({ title, pathname }, index) => (
          <StepListItem
            key={title}
            state={
              index < currentStepIndex
                ? 'complete'
                : index === currentStepIndex
                ? 'current'
                : 'incomplete'
            }
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
            nextStepUrl={`${url}/audit-boards`}
            jurisdiction={jurisdiction}
            round={round}
          />
        </Route>
        <Route exact path={`${path}/audit-boards`}>
          <AuditBoardsStep
            previousStepUrl={`${url}/prepare-batches`}
            nextStepUrl={`${url}/audit-batches`}
            jurisdiction={jurisdiction}
            round={round}
            sampleCount={sampleCount}
          />
        </Route>
        <Route exact path={`${path}/audit-batches`}>
          <AuditBatchesStep
            previousStepUrl={`${url}/audit-boards`}
            jurisdiction={jurisdiction}
            round={round}
          />
        </Route>
        <Redirect to={`${url}/prepare-batches`} />
      </Switch>
    </Steps>
  )
}

export default AuditRoundBatchComparison

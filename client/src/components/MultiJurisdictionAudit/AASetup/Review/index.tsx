import React, { useState } from 'react'
import { useParams, useHistory, Link } from 'react-router-dom'
import {
  H4,
  Callout,
  RadioGroup,
  Radio,
  Spinner,
  Card,
  H5,
  Tag,
  Intent,
} from '@blueprintjs/core'
import { Formik, FormikProps, getIn, Field } from 'formik'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'
import H2Title from '../../../Atoms/H2Title'
import useAuditSettings from '../../useAuditSettings'
import useContests from '../../useContests'
import useJurisdictions from '../../useJurisdictions'
import { testNumber } from '../../../utilities'
import FormSection, {
  FormSectionDescription,
} from '../../../Atoms/Form/FormSection'
import SettingsTable from './SettingsTable'
import { isSetupComplete, allCvrsUploaded } from '../../StatusBox'
import ConfirmLaunch from './ConfirmLaunch'
import FormField from '../../../Atoms/Form/FormField'
import useSampleSizes, { ISampleSizeOption } from './useSampleSizes'
import {
  useJurisdictionsFile,
  isFileProcessed,
  useStandardizedContestsFile,
} from '../../useCSV'
import { ISampleSizes } from '../../useRoundsAuditAdmin'
import { mapValues } from '../../../../utils/objects'
import { FlexTable } from '../../../Atoms/Table'
import { pluralize } from '../../../../utils/string'

const percentFormatter = new Intl.NumberFormat(undefined, {
  style: 'percent',
})

interface IFormOptions {
  [contestId: string]: ISampleSizeOption
}

interface IProps {
  locked: boolean
  prevStage: ISidebarMenuItem
  refresh: () => void
  startNextRound: (sampleSizes: ISampleSizes) => Promise<boolean>
}

const Review: React.FC<IProps> = ({
  prevStage,
  locked,
  refresh,
  startNextRound,
}: IProps) => {
  const { electionId } = useParams<{ electionId: string }>()
  const [auditSettings] = useAuditSettings(electionId)
  const jurisdictions = useJurisdictions(electionId)
  const [jurisdictionsFile] = useJurisdictionsFile(electionId)
  const [standardizedContestsFile] = useStandardizedContestsFile(
    electionId,
    auditSettings
  )
  const [contests] = useContests(electionId)
  const history = useHistory()
  const [isConfirmDialogOpen, setIsConfirmDialogOpen] = useState(false)

  const setupComplete =
    !!jurisdictions &&
    !!contests &&
    !!auditSettings &&
    isSetupComplete(jurisdictions, contests, auditSettings)
  // eslint-disable-next-line prefer-const
  let [sampleSizeOptions, selectedSampleSizes] = useSampleSizes(
    electionId,
    setupComplete
  ) || [null, null]

  if (!jurisdictions || !contests || !auditSettings) return null // Still loading

  const submit = async ({ sampleSizes }: { sampleSizes: IFormOptions }) => {
    if (await startNextRound(sampleSizes)) {
      refresh()
      history.push(`/election/${electionId}/progress`)
    } else {
      // TEST TODO when withMockFetch works with error handling
    }
  }

  const {
    electionName,
    randomSeed,
    riskLimit,
    online,
    auditType,
  } = auditSettings

  // Add custom option to sample size options from backend
  sampleSizeOptions =
    sampleSizeOptions &&
    mapValues(sampleSizeOptions, options => [
      ...options,
      { key: 'custom', size: null, prob: null },
    ])

  // If locked, meaning the audit already was launched, show which sample size got selected.
  // Otherwise default select the first option.
  const initialValues: IFormOptions =
    sampleSizeOptions && selectedSampleSizes
      ? locked
        ? selectedSampleSizes
        : mapValues(sampleSizeOptions, options => options[0])
      : {}

  const participatingJurisdictions = jurisdictions.filter(({ id }) =>
    contests.some(c => c.jurisdictionIds.includes(id))
  )

  const jurisdictionIdToName = Object.fromEntries(
    jurisdictions.map(({ id, name }) => [id, name])
  )

  const cvrsUploaded =
    !['BALLOT_COMPARISON', 'HYBRID'].includes(auditSettings.auditType) ||
    allCvrsUploaded(participatingJurisdictions)

  const numManifestUploadsComplete = participatingJurisdictions.filter(j =>
    isFileProcessed(j.ballotManifest)
  ).length

  const validateCustomSampleSize = (totalBallotsCast: string) => {
    if (auditType === 'BATCH_COMPARISON') {
      const totalBatches = participatingJurisdictions.reduce(
        (a, { ballotManifest: { numBatches } }) =>
          numBatches !== null ? a + numBatches : a,
        0
      )
      return testNumber(
        totalBatches,
        `Must be less than or equal to: ${totalBatches} (the total number of batches in the contest)`
      )
    }
    return testNumber(
      Number(totalBallotsCast),
      `Must be less than or equal to: ${totalBallotsCast} (the total number of ballots in the contest)`
    )
  }

  return (
    <div>
      <H2Title>Review &amp; Launch</H2Title>
      <Callout intent="warning">
        Once the audit is started, the audit definition will no longer be
        editable. Please make sure this data is correct before launching the
        audit.
      </Callout>
      <br />
      <H4>Audit Settings</H4>
      <Card>
        <SettingsTable>
          <tbody>
            <tr>
              <td>Election Name:</td>
              <td>{electionName}</td>
            </tr>
            <tr>
              <td>Audit Type:</td>
              <td>
                {
                  {
                    BALLOT_POLLING: 'Ballot Polling',
                    BATCH_COMPARISON: 'Batch Comparison',
                    BALLOT_COMPARISON: 'Ballot Comparison',
                    HYBRID:
                      'Hybrid (SUITE - Ballot Comparison & Ballot Polling)',
                  }[auditType]
                }
              </td>
            </tr>
            <tr>
              <td>Risk Limit:</td>
              <td>{riskLimit && `${riskLimit}%`}</td>
            </tr>
            <tr>
              <td>Random Seed:</td>
              <td>{randomSeed}</td>
            </tr>
            <tr>
              <td>Participating Jurisdictions:</td>
              <td>
                <a
                  href={`/api/election/${electionId}/jurisdiction/file/csv`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {jurisdictionsFile && jurisdictionsFile.file
                    ? jurisdictionsFile.file.name
                    : ''}
                </a>
              </td>
            </tr>
            {auditType === 'BALLOT_COMPARISON' && (
              <tr>
                <td>Standardized Contests:</td>
                <td>
                  <a
                    href={`/api/election/${electionId}/standardized-contests/file/csv`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {standardizedContestsFile && standardizedContestsFile.file
                      ? standardizedContestsFile.file.name
                      : ''}
                  </a>
                </td>
              </tr>
            )}
            <tr>
              <td>Audit Board Data Entry:</td>
              <td>{online ? 'Online' : 'Offline'}</td>
            </tr>
          </tbody>
        </SettingsTable>
      </Card>
      <br />
      <H4>Contests</H4>
      {contests.map(contest => (
        <Card key={contest.id}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'baseline',
            }}
          >
            <H5>{contest.name}</H5>
            <Tag
              intent={contest.isTargeted ? Intent.SUCCESS : Intent.PRIMARY}
              style={{ marginLeft: '10px', flexShrink: 0 }}
            >
              {contest.isTargeted ? 'Target Contest' : 'Opportunistic Contest'}
            </Tag>
          </div>
          {cvrsUploaded && (
            <p>
              {contest.numWinners}{' '}
              {pluralize('winner', Number(contest.numWinners))} -{' '}
              {contest.votesAllowed}{' '}
              {pluralize('vote', Number(contest.votesAllowed))} allowed -{' '}
              {Number(contest.totalBallotsCast).toLocaleString()} total ballots
              cast
            </p>
          )}
          <div style={{ display: 'flex' }}>
            {!cvrsUploaded ? (
              <div style={{ minWidth: '300px', marginRight: '20px' }}>
                Waiting for all jurisdictions to upload CVRs to compute contest
                settings.
              </div>
            ) : (
              <div>
                <FlexTable
                  condensed
                  striped
                  style={{
                    width: auditType === 'HYBRID' ? '420px' : '280px',
                    marginRight: '20px',
                  }}
                >
                  <thead>
                    <tr>
                      <th>Choice</th>
                      <th>Votes</th>
                      {auditType === 'HYBRID' && (
                        <>
                          <th>CVR</th>
                          <th>Non-CVR</th>
                        </>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {contest.choices.map(choice => (
                      <tr key={choice.id}>
                        <td>{choice.name}</td>
                        <td>{choice.numVotes.toLocaleString()}</td>
                        {auditType === 'HYBRID' && (
                          <>
                            <td>{choice.numVotesCvr!.toLocaleString()}</td>
                            <td>{choice.numVotesNonCvr!.toLocaleString()}</td>
                          </>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </FlexTable>
              </div>
            )}
            <div
              style={{
                width: '100%',
                position: 'relative',
                minHeight: '140px',
              }}
            >
              <FlexTable
                condensed
                striped
                scrollable
                style={{
                  position: 'absolute',
                  height: '100%',
                }}
              >
                <thead>
                  <tr>
                    <th>
                      Contest universe: {contest.jurisdictionIds.length}/
                      {jurisdictions.length} jurisdictions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {contest.jurisdictionIds.map(jurisdictionId => (
                    <tr key={jurisdictionId}>
                      <td>{jurisdictionIdToName[jurisdictionId]}</td>
                    </tr>
                  ))}
                </tbody>
              </FlexTable>
            </div>
          </div>
        </Card>
      ))}
      <br />
      <H4>Sample Size</H4>
      <Formik
        initialValues={{
          sampleSizes: initialValues,
        }}
        enableReinitialize
        onSubmit={submit}
      >
        {({
          values,
          handleSubmit,
          isSubmitting,
          setFieldValue,
        }: FormikProps<{
          sampleSizes: IFormOptions
        }>) => (
          <form>
            {setupComplete ? (
              sampleSizeOptions === null ? (
                <div style={{ display: 'flex' }}>
                  <Spinner size={Spinner.SIZE_SMALL} />
                  <span style={{ marginLeft: '10px' }}>
                    Loading sample size options...
                  </span>
                </div>
              ) : (
                <FormSection>
                  <FormSectionDescription>
                    Choose the initial sample size for each contest you would
                    like to use for Round 1 of the audit from the options below.
                  </FormSectionDescription>
                  {contests
                    .filter(contest => contest.isTargeted)
                    .map(contest => {
                      const currentOption = values.sampleSizes[contest.id]
                      return (
                        <Card key={contest.id}>
                          <FormSectionDescription>
                            <H5>{contest.name}</H5>
                            <RadioGroup
                              name={`sampleSizes[${contest.id}]`}
                              onChange={e => {
                                const selectedOption = sampleSizeOptions![
                                  contest.id
                                ].find(c => c.key === e.currentTarget.value)
                                setFieldValue(
                                  `sampleSizes[${contest.id}]`,
                                  selectedOption
                                )
                              }}
                              selectedValue={getIn(
                                values,
                                `sampleSizes[${contest.id}][key]`
                              )}
                              disabled={locked}
                            >
                              {sampleSizeOptions![contest.id].map(
                                (option: ISampleSizeOption) => {
                                  return option.key === 'custom' ? (
                                    <Radio value="custom" key={option.key}>
                                      Enter your own sample size (not
                                      recommended)
                                    </Radio>
                                  ) : (
                                    <Radio value={option.key} key={option.key}>
                                      {option.key === 'all-ballots' &&
                                        'All ballots: '}
                                      {option.key === 'asn'
                                        ? 'BRAVO Average Sample Number: '
                                        : ''}
                                      {`${Number(
                                        option.size
                                      ).toLocaleString()} samples`}
                                      {option.prob
                                        ? ` (${percentFormatter.format(
                                            option.prob
                                          )} chance of reaching risk limit and completing the audit in one round)`
                                        : ''}
                                      {option.key === 'all-ballots' &&
                                        ' (recommended for this contest due to the small margin of victory)'}
                                    </Radio>
                                  )
                                }
                              )}
                            </RadioGroup>
                            {currentOption &&
                              currentOption.key === 'custom' && (
                                <Field
                                  component={FormField}
                                  name={`sampleSizes[${contest.id}].size`}
                                  value={
                                    currentOption.size === null
                                      ? undefined
                                      : currentOption.size
                                  }
                                  onValueChange={(value: number) =>
                                    setFieldValue(
                                      `sampleSizes[${contest.id}].size`,
                                      value
                                    )
                                  }
                                  type="number"
                                  validate={validateCustomSampleSize(
                                    contest.totalBallotsCast
                                  )}
                                  disabled={locked}
                                />
                              )}
                          </FormSectionDescription>
                        </Card>
                      )
                    })}
                </FormSection>
              )
            ) : (
              <p>
                All jurisdiction files must be uploaded and all audit settings
                must be configured in order to calculate the sample size.{' '}
                <Link to={`/election/${electionId}/progress`}>
                  View jurisdiction upload progress.
                </Link>
              </p>
            )}
            <FormButtonBar>
              <FormButton onClick={prevStage.activate}>Back</FormButton>
              <FormButton
                intent="primary"
                disabled={
                  sampleSizeOptions === null || locked || !setupComplete
                }
                onClick={() => setIsConfirmDialogOpen(true)}
              >
                Launch Audit
              </FormButton>
            </FormButtonBar>
            <ConfirmLaunch
              isOpen={isConfirmDialogOpen}
              handleClose={() => setIsConfirmDialogOpen(false)}
              handleSubmit={handleSubmit}
              isSubmitting={isSubmitting}
              message={
                auditType === 'BALLOT_POLLING'
                  ? `${numManifestUploadsComplete} of ${participatingJurisdictions.length} jurisdictions have uploaded ballot manifests.`
                  : undefined
              }
            />
          </form>
        )}
      </Formik>
    </div>
  )
}

export default Review

import React, { useState } from 'react'
import { useParams, useHistory, Link } from 'react-router-dom'
import { H4, Callout, RadioGroup, Radio, Spinner } from '@blueprintjs/core'
import { Formik, FormikProps, getIn, Field } from 'formik'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'
import H2Title from '../../../Atoms/H2Title'
import useAuditSettings from '../../useAuditSettings'
import useContests from '../../useContests'
import { IContest } from '../../../../types'
import useJurisdictions from '../../useJurisdictions'
import { testNumber } from '../../../utilities'
import FormSection, {
  FormSectionDescription,
} from '../../../Atoms/Form/FormSection'
import ContestsTable from './ContestsTable'
import SettingsTable from './SettingsTable'
import { isSetupComplete } from '../../StatusBox'
import ConfirmLaunch from './ConfirmLaunch'
import FormField from '../../../Atoms/Form/FormField'
import ElevatedCard from '../../../Atoms/SpacedCard'
import useSampleSizes, { ISampleSizeOption } from './useSampleSizes'
import {
  useJurisdictionsFile,
  isFileProcessed,
  useStandardizedContestsFile,
} from '../../useCSV'
import { ISampleSizes } from '../../useRoundsAuditAdmin'
import { mapValues } from '../../../../utils/objects'

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

  const shouldShowSampleSizes =
    !!jurisdictions &&
    !!contests &&
    !!auditSettings &&
    isSetupComplete(jurisdictions, contests, auditSettings)
  // eslint-disable-next-line prefer-const
  let [sampleSizeOptions, selectedSampleSizes] = useSampleSizes(
    electionId,
    shouldShowSampleSizes
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

  const targetedContests = contests
    .filter(c => c.isTargeted === true)
    .map(c => ({
      ...c,
      jurisdictionIds: c.jurisdictionIds.map(j =>
        jurisdictions.length > 0
          ? jurisdictions.find(p => p.id === j)!.name
          : ''
      ),
    }))
  const opportunisticContests = contests
    .filter(c => c.isTargeted === false)
    .map(c => ({
      ...c,
      jurisdictionIds: c.jurisdictionIds.map(j =>
        jurisdictions.length > 0
          ? jurisdictions.find(p => p.id === j)!.name
          : ''
      ),
    }))

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

  const participatingJurisdictions = contests
    ? jurisdictions.filter(({ id }) =>
        contests.some(c => c.jurisdictionIds.includes(id))
      )
    : []

  const numManifestUploadsComplete = participatingJurisdictions.filter(j =>
    isFileProcessed(j.ballotManifest)
  ).length

  const getBatchTotal = () =>
    participatingJurisdictions.reduce(
      (a, { ballotManifest: { numBatches } }) =>
        numBatches !== null ? a + numBatches : a,
      0
    )

  const getBallotTotal = (jurisdictionIds: string[]) =>
    jurisdictions
      .filter(jurisdiction =>
        jurisdictionIds.find(p => p === jurisdiction.name)
      )
      .reduce(
        (a, { ballotManifest: { numBallots } }) =>
          numBallots !== null ? a + numBallots : a,
        0
      )

  const validateCustomSampleSize = (
    totalBallotsCast: string,
    jurisdictionIds: string[],
    contestName: string
  ) => {
    if (auditType === 'BALLOT_POLLING') {
      return testNumber(
        Number(totalBallotsCast),
        `Must be less than or equal to: ${totalBallotsCast} (the total number of ballots in the targeted contest: '${contestName}')`
      )
    }
    if (auditType === 'BATCH_COMPARISON') {
      return testNumber(
        Number(getBatchTotal()),
        `Must be less than or equal to: ${Number(
          getBatchTotal()
        )} (the total number of batches in the targeted contest: '${contestName}')`
      )
    }
    if (auditType === 'BALLOT_COMPARISON') {
      return testNumber(
        Number(getBallotTotal(jurisdictionIds)),
        `Must be less than or equal to: ${Number(
          getBallotTotal(jurisdictionIds)
        )} (the total number of ballots in the targeted contest: '${contestName}')`
      )
    }
    /* istanbul ignore next */
    return Promise.resolve(undefined)
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
      <ElevatedCard>
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
        <ContestsTable>
          <thead>
            <tr>
              <th>Target Contests</th>
              <th>Jurisdictions</th>
            </tr>
          </thead>
          <tbody>
            {targetedContests.map((c: IContest) => (
              <tr key={c.id}>
                <td>{c.name}</td>
                <td>{c.jurisdictionIds.join(', ')}</td>
              </tr>
            ))}
          </tbody>
        </ContestsTable>
        <ContestsTable>
          <thead>
            <tr>
              <th>Opportunistic Contests</th>
              <th>Jurisdictions</th>
            </tr>
          </thead>
          <tbody>
            {opportunisticContests.map((c: IContest) => (
              <tr key={c.id}>
                <td>{c.name}</td>
                <td>{c.jurisdictionIds.join(', ')}</td>
              </tr>
            ))}
          </tbody>
        </ContestsTable>
      </ElevatedCard>
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
            {shouldShowSampleSizes ? (
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
                  {targetedContests.map(contest => {
                    const currentOption = values.sampleSizes[contest.id]
                    return (
                      <ElevatedCard key={contest.id}>
                        <FormSectionDescription>
                          <H4>{contest.name}</H4>
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
                                    Enter your own sample size (not recommended)
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
                          {currentOption && currentOption.key === 'custom' && (
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
                                contest.totalBallotsCast,
                                contest.jurisdictionIds,
                                contest.name
                              )}
                              disabled={locked}
                            />
                          )}
                        </FormSectionDescription>
                      </ElevatedCard>
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
                  locked ||
                  !isSetupComplete(jurisdictions, contests, auditSettings)
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

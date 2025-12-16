import React, { useState, useEffect } from 'react'
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
  Button,
  Colors,
} from '@blueprintjs/core'
import { Formik, FormikProps, getIn, Field } from 'formik'
import styled from 'styled-components'
import { Link } from 'react-router-dom'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import H2Title from '../../../Atoms/H2Title'
import { testNumber } from '../../../utilities'
import { FormSectionDescription } from '../../../Atoms/Form/FormSection'
import ConfirmLaunch from './ConfirmLaunch'
import FormField from '../../../Atoms/Form/FormField'
import useSampleSizes, {
  ISampleSizeOption,
  ISampleSizeOptions,
} from './useSampleSizes'
import {
  ISampleSizes,
  useComputeSamplePreview,
} from '../../useRoundsAuditAdmin'
import { mapValues } from '../../../../utils/objects'
import { FlexTable } from '../../../Atoms/Table'
import { pluralize } from '../../../../utils/string'
import { ErrorLabel } from '../../../Atoms/Form/_helpers'
import { IContest } from '../../../../types'
import { sum } from '../../../../utils/number'
import { useJurisdictions, IJurisdiction } from '../../../useJurisdictions'
import { isFileProcessed } from '../../../useCSV'
import useContestNameStandardizations from '../../../useContestNameStandardizations'
import {
  IContestChoiceNameStandardizations,
  useContestChoiceNameStandardizations,
  useUpdateContestChoiceNameStandardizations,
} from '../../../useContestChoiceNameStandardizations'
import useStandardizedContests from '../../../useStandardizedContests'
import { isSetupComplete, allCvrsUploaded } from '../../../Atoms/StatusBox'
import { useAuditSettings, AuditType } from '../../../useAuditSettings'
import { useContests } from '../../../useContests'
import {
  useJurisdictionsFile,
  useStandardizedContestsFile,
} from '../../../useFileUpload'
import SamplePreview from './SamplePreview'
import StandardizeContestNamesDialog from './StandardizeContestNames'
import LabeledValue from './LabeledValue'
import CvrChoiceNameConsistencyError from './CvrChoiceNameConsistencyError'
import {
  isContestChoiceNameStandardizationComplete as isContestChoiceNameStandardizationCompleteHelper,
  StandardizeContestChoiceNamesCallout,
  StandardizeContestChoiceNamesDialog,
} from './StandardizeContestChoiceNamesDialog'
import { useBatchFilesBundle } from '../../../useBatchFilesBundle'

const percentFormatter = new Intl.NumberFormat(undefined, {
  style: 'percent',
})

const contestJurisdictions = (
  jurisdictionsById: Record<string, IJurisdiction>,
  contest: IContest
) =>
  contest.jurisdictionIds.map(
    jurisdictionId => jurisdictionsById[jurisdictionId]
  )

const ReviewWrapper = styled.div`
  width: 100%;
  section {
    margin-bottom: 30px;
  }
`

interface IProps {
  electionId: string
  locked: boolean
  goToPrevStage: () => void
  startNextRound: (sampleSizes: ISampleSizes) => Promise<boolean>
}

const Review: React.FC<IProps> = ({
  electionId,
  locked,
  goToPrevStage,
  startNextRound,
}: IProps) => {
  const auditSettingsQuery = useAuditSettings(electionId)
  const jurisdictionsQuery = useJurisdictions(electionId)
  const jurisdictionsFileUpload = useJurisdictionsFile(electionId)
  const isStandardizedContestsFileEnabled =
    auditSettingsQuery.data?.auditType === 'BALLOT_COMPARISON' ||
    auditSettingsQuery.data?.auditType === 'HYBRID'
  const standardizedContestsFileUpload = useStandardizedContestsFile(
    electionId,
    { enabled: isStandardizedContestsFileEnabled }
  )
  const standardizedContests = useStandardizedContests(electionId)
  const contestsQuery = useContests(electionId)
  const computeSamplePreview = useComputeSamplePreview(electionId)
  const [isConfirmDialogOpen, setIsConfirmDialogOpen] = useState(false)
  const [isSamplePreviewModalOpen, setIsSamplePreviewModalOpen] = useState(
    false
  )

  const [
    contestNameStandardizations,
    updateContestNameStandardizations,
  ] = useContestNameStandardizations(
    electionId,
    auditSettingsQuery.data || null
  )
  const [
    isContestNameStandardizationDialogOpen,
    setIsContestNameStandardizationDialogOpen,
  ] = useState(false)

  // Hooks for batch file bundle downloads
  const manifestsBundle = useBatchFilesBundle(electionId, 'manifests')
  const candidateTotalsBundle = useBatchFilesBundle(
    electionId,
    'candidate-totals'
  )

  // Auto-trigger download when manifests bundle is ready
  useEffect(() => {
    if (manifestsBundle.isComplete && manifestsBundle.downloadUrl) {
      window.location.href = manifestsBundle.downloadUrl
      manifestsBundle.reset()
    }
  }, [manifestsBundle.isComplete, manifestsBundle.downloadUrl])

  // Auto-trigger download when candidate totals bundle is ready
  useEffect(() => {
    if (candidateTotalsBundle.isComplete && candidateTotalsBundle.downloadUrl) {
      window.location.href = candidateTotalsBundle.downloadUrl
      candidateTotalsBundle.reset()
    }
  }, [candidateTotalsBundle.isComplete, candidateTotalsBundle.downloadUrl])

  const contestChoiceNameStandardizationsQuery = useContestChoiceNameStandardizations(
    electionId
  )
  const updateContestChoiceNameStandardizations = useUpdateContestChoiceNameStandardizations(
    electionId
  )
  const [
    contestIdForChoiceNameStandardizationDialog,
    setContestIdForChoiceNameStandardizationDialog,
  ] = useState<IContest['id'] | null>(null)

  const setupComplete =
    jurisdictionsQuery.isSuccess &&
    contestsQuery.isSuccess &&
    auditSettingsQuery.isSuccess &&
    isSetupComplete(
      jurisdictionsQuery.data,
      contestsQuery.data,
      auditSettingsQuery.data
    )

  const isContestNameStandardizationNeeded =
    !!contestNameStandardizations &&
    Object.values(contestNameStandardizations.standardizations).length > 0
  const isContestNameStandardizationOutstanding =
    !!contestNameStandardizations &&
    Object.values(
      contestNameStandardizations.standardizations
    ).some(jurisdictionStandardizations =>
      Object.values(jurisdictionStandardizations).some(
        cvrContestName => cvrContestName === null
      )
    )
  const isContestNameStandardizationComplete =
    !!contestNameStandardizations &&
    !(
      isContestNameStandardizationNeeded &&
      isContestNameStandardizationOutstanding
    )

  const isContestChoiceNameStandardizationComplete =
    contestChoiceNameStandardizationsQuery.isSuccess &&
    isContestChoiceNameStandardizationCompleteHelper(
      contestChoiceNameStandardizationsQuery.data.standardizations
    )

  const areChoiceNamesConsistentForAllContests = (
    contestsQuery.data ?? []
  ).every(contest => !contest.cvrChoiceNameConsistencyError)

  const shouldLoadSampleSizes =
    setupComplete &&
    isContestNameStandardizationComplete &&
    isContestChoiceNameStandardizationComplete &&
    areChoiceNamesConsistentForAllContests

  const sampleSizesQuery = useSampleSizes(electionId, 1, {
    enabled: shouldLoadSampleSizes,
    refetchInterval: sampleSizesResponse =>
      sampleSizesResponse?.task.completedAt === null ? 1000 : false,
    refetchOnMount: 'always',
  })

  if (
    !jurisdictionsQuery.isSuccess ||
    !contestsQuery.isSuccess ||
    !auditSettingsQuery.isSuccess ||
    !contestChoiceNameStandardizationsQuery.isSuccess
  ) {
    return null // Still loading
  }
  const jurisdictions = jurisdictionsQuery.data
  const contests = contestsQuery.data
  const {
    electionName,
    randomSeed,
    riskLimit,
    online,
    auditType,
    auditMathType,
  } = auditSettingsQuery.data
  const contestChoiceNameStandardizations =
    contestChoiceNameStandardizationsQuery.data.standardizations

  const participatingJurisdictions = jurisdictions.filter(({ id }) =>
    contests.some(c => c.jurisdictionIds.includes(id))
  )

  const needsCvrs = ['BALLOT_COMPARISON', 'HYBRID'].includes(auditType)
  const cvrsUploaded = !needsCvrs || allCvrsUploaded(participatingJurisdictions)

  const numManifestUploadsComplete = participatingJurisdictions.filter(j =>
    isFileProcessed(j.ballotManifest)
  ).length

  const jurisdictionsById = Object.fromEntries(
    jurisdictions.map(jurisdiction => [jurisdiction.id, jurisdiction])
  )

  return (
    <ReviewWrapper>
      <H2Title>Review &amp; Launch</H2Title>
      <Callout intent="warning">
        <strong>
          Once the audit is launched, you cannot change the audit setup.
        </strong>{' '}
        {!locked && (
          <>
            <br />
            Review the settings below and make sure they are correct before
            launching the audit.
          </>
        )}
      </Callout>
      <br />
      <section>
        <H4>
          {needsCvrs ? 'Participants & Standardized Contests' : 'Participants'}
        </H4>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr 1fr',
          }}
        >
          <LabeledValue label="Jurisdictions">
            {jurisdictions.length}
          </LabeledValue>
          <LabeledValue label="Jursidictions File">
            <a
              href={jurisdictionsFileUpload.downloadFileUrl}
              target="_blank"
              rel="noopener noreferrer"
            >
              {jurisdictionsFileUpload.uploadedFile.data?.file?.name || ''}
            </a>
          </LabeledValue>
          {needsCvrs && (
            <LabeledValue label="Standardized Contests File">
              <a
                href={standardizedContestsFileUpload.downloadFileUrl}
                target="_blank"
                rel="noopener noreferrer"
              >
                {standardizedContestsFileUpload.uploadedFile.data?.file?.name ||
                  ''}
              </a>
            </LabeledValue>
          )}
        </div>
      </section>
      <section>
        <H4>Contests</H4>
        {contestNameStandardizations && isContestNameStandardizationNeeded && (
          <>
            {isContestNameStandardizationOutstanding ? (
              <Callout intent="warning">
                <p>
                  Some contest names in the uploaded CVR files do not match the
                  standardized contest names.
                </p>
                <Button
                  intent="primary"
                  onClick={() =>
                    setIsContestNameStandardizationDialogOpen(true)
                  }
                >
                  Standardize Contest Names
                </Button>
              </Callout>
            ) : (
              <Callout intent="success">
                <p>
                  All contest names in the uploaded CVR files have been
                  standardized.
                </p>
                <Button
                  onClick={() =>
                    setIsContestNameStandardizationDialogOpen(true)
                  }
                  disabled={locked}
                >
                  Edit Standardized Contest Names
                </Button>
              </Callout>
            )}
            <StandardizeContestNamesDialog
              isOpen={isContestNameStandardizationDialogOpen}
              onClose={() => setIsContestNameStandardizationDialogOpen(false)}
              standardizations={contestNameStandardizations}
              updateStandardizations={updateContestNameStandardizations}
              jurisdictionsById={jurisdictionsById}
            />
            <br />
          </>
        )}
        {contests.map(contest => (
          <Card key={contest.id} style={{ background: Colors.LIGHT_GRAY5 }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'baseline',
              }}
            >
              <H5 id={contest.id}>{contest.name}</H5>
              <Tag
                intent={contest.isTargeted ? Intent.SUCCESS : Intent.PRIMARY}
                style={{ marginLeft: '10px', flexShrink: 0 }}
              >
                {contest.isTargeted
                  ? 'Target Contest'
                  : 'Opportunistic Contest'}
              </Tag>
            </div>
            {cvrsUploaded && (
              <p>
                {contest.numWinners}{' '}
                {pluralize('winner', Number(contest.numWinners))} -{' '}
                {Number(contest.totalBallotsCast).toLocaleString()} total
                ballots cast
              </p>
            )}
            {cvrsUploaded &&
              isContestChoiceNameStandardizationComplete &&
              contest.cvrChoiceNameConsistencyError && (
                <CvrChoiceNameConsistencyError
                  error={contest.cvrChoiceNameConsistencyError}
                  jurisdictionNamesById={jurisdictionsById}
                />
              )}
            <StandardizeContestChoiceNamesCallout
              contest={contest}
              disabled={locked}
              openDialog={() =>
                setContestIdForChoiceNameStandardizationDialog(contest.id)
              }
              standardizations={contestChoiceNameStandardizations}
            />
            <StandardizeContestChoiceNamesDialog
              contest={contest}
              isOpen={
                contestIdForChoiceNameStandardizationDialog === contest.id
              }
              jurisdictionsById={jurisdictionsById}
              onClose={() =>
                setContestIdForChoiceNameStandardizationDialog(null)
              }
              standardizations={contestChoiceNameStandardizations}
              standardizedContestChoiceNames={
                (standardizedContests ?? []).find(c => c.name === contest.name)
                  ?.choiceNames ?? []
              }
              updateStandardizations={async (
                newStandardizations: IContestChoiceNameStandardizations
              ) => {
                await updateContestChoiceNameStandardizations.mutateAsync(
                  newStandardizations
                )
              }}
              // Reset the form state within the dialog component any time the dialog is opened
              key={contestIdForChoiceNameStandardizationDialog || 'closed'}
            />
            <div style={{ display: 'flex' }}>
              {!cvrsUploaded ? (
                <div style={{ minWidth: '300px', marginRight: '20px' }}>
                  Waiting for all jurisdictions to upload CVRs to compute
                  contest settings.
                </div>
              ) : (
                <div>
                  <FlexTable
                    condensed
                    striped
                    style={{
                      width: auditType === 'HYBRID' ? '420px' : '280px',
                      marginRight: '20px',
                      background: 'white',
                    }}
                  >
                    <thead>
                      <tr>
                        <th>Choice</th>
                        <th>1st Choice Votes</th>
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
                          <td>
                            {choice.name === 'Write-in-118'
                              ? 'Invalid Write-In: Bubble Filled, No Interpretable Text'
                              : choice.name}
                          </td>
                          <td>{choice.numVotes.toLocaleString()}</td>
                          {auditType === 'HYBRID' && (
                            <>
                              <td>
                                {choice.numVotesCvr != null &&
                                  choice.numVotesCvr.toLocaleString()}
                              </td>
                              <td>
                                {choice.numVotesNonCvr != null &&
                                  choice.numVotesNonCvr.toLocaleString()}
                              </td>
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
                    background: 'white',
                  }}
                >
                  <thead>
                    <tr>
                      <th>
                        Contest universe: {contest.jurisdictionIds.length}/
                        {jurisdictions.length}&nbsp;jurisdictions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {contestJurisdictions(jurisdictionsById, contest).map(
                      jurisdiction => (
                        <tr key={jurisdiction.id}>
                          <td>{jurisdiction.name}</td>
                        </tr>
                      )
                    )}
                  </tbody>
                </FlexTable>
              </div>
            </div>
          </Card>
        ))}
      </section>
      <section>
        <H4>Audit Settings</H4>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr 1fr',
            columnGap: '15px',
            rowGap: '20px',
          }}
        >
          <LabeledValue label="Election Name">{electionName}</LabeledValue>
          <LabeledValue label="Audit Type">
            {
              {
                BALLOT_POLLING: 'Ballot Polling',
                BATCH_COMPARISON: 'Batch Comparison',
                BALLOT_COMPARISON: 'Ballot Comparison',
                HYBRID: 'Hybrid (SUITE - Ballot Comparison & Ballot Polling)',
              }[auditType]
            }
          </LabeledValue>
          <LabeledValue label="Risk Limit">
            {riskLimit && `${riskLimit}%`}
          </LabeledValue>
          <LabeledValue label="Random Seed">{randomSeed}</LabeledValue>
          <LabeledValue label="Audit Math Type">
            {
              {
                BRAVO: 'BRAVO',
                MINERVA: 'Minerva',
                PROVIDENCE: 'Providence',
                SUPERSIMPLE: 'Super-Simple',
                MACRO: 'MACRO',
                SUITE: 'SUITE',
                CARD_STYLE_DATA: 'Card Style Data',
              }[auditMathType]
            }
          </LabeledValue>
          <LabeledValue label="Audit Board Data Entry">
            {online ? 'Online' : 'Offline'}
          </LabeledValue>
        </div>
      </section>
      <section>
        <H4>Sample Size</H4>
        {(() => {
          const { sampleSizes, selected } = sampleSizesQuery.data || {}

          // Add custom option to sample size options from backend
          const sampleSizeOptions =
            sampleSizes &&
            mapValues(sampleSizes, options => [
              ...options,
              { key: 'custom', size: null, prob: null },
            ])

          // If the audit was already launched, show which sample size got selected.
          // Otherwise default select the first option.
          const initialValues: ISampleSizes | null | undefined =
            sampleSizeOptions &&
            (selected || mapValues(sampleSizeOptions, options => options[0]))

          const submit = async (values: { sampleSizes: ISampleSizes }) => {
            await startNextRound(values.sampleSizes)
          }

          const onClickPreviewSample = async (values: {
            sampleSizes: ISampleSizes
          }) => {
            await computeSamplePreview.mutateAsync(values.sampleSizes)
            setIsSamplePreviewModalOpen(true)
          }

          return (
            <Formik
              // We need to render Formik from the get-go, even though we haven't
              // loaded the sample size options yet, because we want to always show
              // the action button bar (which needs access to Formik). So we need to
              // pass in dummy initialValues while loading the options, and then
              // make sure they get reset once the options are loaded. The key prop
              // ensures this works properly. Formik has an enableReinitialize prop
              // that is supposed to do this, but using that props creates an extra
              // render cycle in which initialValues has changed but the form state
              // `values` variable has not yet updated, which is a pain.
              key={initialValues ? 'loaded' : 'loading'}
              initialValues={{ sampleSizes: initialValues || {} }}
              onSubmit={submit}
            >
              {({
                values,
                handleSubmit,
                isSubmitting,
                setFieldValue,
              }: FormikProps<{
                sampleSizes: ISampleSizes
              }>) => {
                return (
                  <form>
                    {(() => {
                      if (!setupComplete)
                        return (
                          <>
                            <p>
                              All jurisdiction files must be uploaded and all
                              audit settings must be configured in order to
                              calculate the sample size.{' '}
                              <Link to={`/election/${electionId}/progress`}>
                                View jurisdiction file upload progress
                              </Link>
                              .
                            </p>
                          </>
                        )

                      if (!isContestNameStandardizationComplete)
                        return (
                          <p>
                            All contest names must be standardized in order to
                            calculate the sample size.
                          </p>
                        )

                      if (!isContestChoiceNameStandardizationComplete)
                        return (
                          <p>
                            All contest choice names must be standardized in
                            order to calculate the sample size.
                          </p>
                        )

                      if (!areChoiceNamesConsistentForAllContests) {
                        return (
                          <p>
                            The following contests have inconsistent choice
                            names:{' '}
                            {contests
                              .filter(
                                contest => contest.cvrChoiceNameConsistencyError
                              )
                              .map((contest, i, filteredContests) => (
                                <React.Fragment key={contest.id}>
                                  <a href={`#${contest.id}`}>{contest.name}</a>
                                  {i < filteredContests.length - 1 && ', '}
                                </React.Fragment>
                              ))}
                            . Resolve these inconsistencies in order to
                            calculate the sample size.
                          </p>
                        )
                      }

                      if (sampleSizesQuery.data?.task.error)
                        return (
                          <ErrorLabel>
                            {sampleSizesQuery.data.task.error}
                          </ErrorLabel>
                        )

                      if (!sampleSizeOptions)
                        return (
                          <div style={{ display: 'flex', padding: '15px 0' }}>
                            <Spinner size={Spinner.SIZE_SMALL} />
                            <span style={{ marginLeft: '10px' }}>
                              Loading sample size options...
                            </span>
                          </div>
                        )

                      return (
                        <SelectSampleSizes
                          locked={locked}
                          contests={contests}
                          auditType={auditType}
                          jurisdictionsById={jurisdictionsById}
                          sampleSizeOptions={sampleSizeOptions}
                          values={values}
                          setFieldValue={setFieldValue}
                        />
                      )
                    })()}
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
                    {auditType === 'BATCH_COMPARISON' && setupComplete && (
                      <Callout
                        intent="primary"
                        icon="download"
                        style={{ marginTop: '30px' }}
                      >
                        <H5>Download Jurisdiction Files for Sharing</H5>
                        <p>
                          Download the ZIP bundles containing jurisdiction files
                          and their SHA-256 hashes. You may choose to share the
                          hashes with the public before launching the audit so
                          that the files can be verified after the audit is
                          complete.
                        </p>
                        {(manifestsBundle.hasError ||
                          candidateTotalsBundle.hasError) && (
                          <Callout
                            intent="danger"
                            style={{ marginBottom: '10px' }}
                          >
                            Error generating bundle. Please try again.
                          </Callout>
                        )}
                        <div style={{ display: 'flex', gap: '10px' }}>
                          <Button
                            icon="download"
                            loading={manifestsBundle.isGenerating}
                            disabled={
                              manifestsBundle.isGenerating ||
                              candidateTotalsBundle.isGenerating
                            }
                            aria-label="Download Ballot Manifests Bundle"
                            onClick={() => manifestsBundle.startDownload()}
                          >
                            Download Ballot Manifests Bundle
                          </Button>
                          <Button
                            icon="download"
                            loading={candidateTotalsBundle.isGenerating}
                            disabled={
                              manifestsBundle.isGenerating ||
                              candidateTotalsBundle.isGenerating
                            }
                            aria-label="Download Candidate Totals Bundle"
                            onClick={() =>
                              candidateTotalsBundle.startDownload()
                            }
                          >
                            Download Candidate Totals Bundle
                          </Button>
                        </div>
                      </Callout>
                    )}
                    <FormButtonBar style={{ marginTop: '15px' }}>
                      <Button
                        disabled={locked}
                        onClick={goToPrevStage}
                        icon="arrow-left"
                      >
                        Back
                      </Button>
                      <div>
                        <FormButton
                          disabled={locked || !sampleSizeOptions}
                          onClick={() => onClickPreviewSample(values)}
                        >
                          Preview Sample
                        </FormButton>
                        <FormButton
                          intent="primary"
                          disabled={
                            locked ||
                            !sampleSizeOptions ||
                            !setupComplete ||
                            !isContestNameStandardizationComplete ||
                            !isContestChoiceNameStandardizationComplete ||
                            !areChoiceNamesConsistentForAllContests
                          }
                          onClick={() => setIsConfirmDialogOpen(true)}
                        >
                          Launch Audit
                        </FormButton>
                      </div>
                    </FormButtonBar>
                  </form>
                )
              }}
            </Formik>
          )
        })()}
      </section>
      {isSamplePreviewModalOpen && (
        <SamplePreview
          electionId={electionId}
          auditType={auditType}
          onClose={() => setIsSamplePreviewModalOpen(false)}
        />
      )}
    </ReviewWrapper>
  )
}

interface ISelectSampleSizesProps {
  locked: boolean
  contests: IContest[]
  auditType: AuditType
  jurisdictionsById: Record<string, IJurisdiction>
  sampleSizeOptions: ISampleSizeOptions
  values: { sampleSizes: ISampleSizes }
  setFieldValue: FormikProps<{
    sampleSizes: ISampleSizes
  }>['setFieldValue']
}

const SelectSampleSizes: React.FC<ISelectSampleSizesProps> = ({
  locked,
  contests,
  auditType,
  jurisdictionsById,
  sampleSizeOptions,
  values,
  setFieldValue,
}) => {
  const targetedContests = contests.filter(contest => contest.isTargeted)

  return (
    <div>
      <FormSectionDescription>
        Choose the initial sample size for each contest you would like to use
        for Round 1 of the audit from the options below.
      </FormSectionDescription>
      {targetedContests.map(contest => {
        const currentOption = values.sampleSizes[contest.id]
        const fullHandTallySize =
          auditType === 'BATCH_COMPARISON'
            ? sum(
                contestJurisdictions(jurisdictionsById, contest).map(
                  jurisdiction => jurisdiction.ballotManifest.numBatches || 0
                )
              )
            : Number(contest.totalBallotsCast)

        return (
          <Card key={contest.id} style={{ background: Colors.LIGHT_GRAY5 }}>
            <H5>{contest.name}</H5>
            {currentOption.size !== null &&
              currentOption.size >= fullHandTallySize && (
                <Callout
                  intent={
                    (auditType === 'BALLOT_POLLING' ||
                      auditType === 'BATCH_COMPARISON') &&
                    targetedContests.length === 1
                      ? 'warning'
                      : 'danger'
                  }
                  style={{ marginBottom: '15px' }}
                >
                  <div>
                    The currently selected sample size for this contest requires
                    a full hand tally.
                  </div>
                  {!(
                    auditType === 'BALLOT_POLLING' ||
                    auditType === 'BATCH_COMPARISON'
                  ) && (
                    <div>
                      To use Arlo for a full hand tally, recreate this audit
                      using the ballot polling or batch comparison audit type.
                    </div>
                  )}
                  {(auditType === 'BALLOT_POLLING' ||
                    auditType === 'BATCH_COMPARISON') &&
                    targetedContests.length > 1 && (
                      <div>
                        Arlo supports running a full hand tally for audits with
                        one target contest. Either remove this contest and audit
                        it separately, or remove the other target contests.
                      </div>
                    )}
                </Callout>
              )}
            <RadioGroup
              name={`sampleSizes[${contest.id}]`}
              onChange={e => {
                const selectedOption = sampleSizeOptions![contest.id].find(
                  c => c.key === e.currentTarget.value
                )
                setFieldValue(`sampleSizes[${contest.id}]`, selectedOption)
              }}
              selectedValue={getIn(values, `sampleSizes[${contest.id}][key]`)}
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
                      {option.key === 'all-ballots' && 'All ballots: '}
                      <strong>{`${Number(
                        option.size
                      ).toLocaleString()} samples`}</strong>
                      {option.prob
                        ? ` (${
                            option.key === 'asn'
                              ? 'BRAVO Average Sample Number - '
                              : ''
                          }${percentFormatter.format(
                            option.prob
                          )} chance of completing the audit in one round)`
                        : ''}
                      {option.key === 'all-ballots' &&
                        ' (recommended for this contest due to the small margin of victory)'}
                      {option.key === 'suite' &&
                        ` (${option.sizeCvr!.toLocaleString()} CVR ballots and ${option.sizeNonCvr!.toLocaleString()} non-CVR ballots)`}
                    </Radio>
                  )
                }
              )}
            </RadioGroup>
            {currentOption &&
              currentOption.key === 'custom' &&
              (auditType === 'HYBRID' ? (
                <>
                  <div>
                    {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
                    <label>
                      CVR ballots:
                      <Field
                        component={FormField}
                        name={`sampleSizes[${contest.id}].sizeCvr`}
                        value={
                          currentOption.sizeCvr === null
                            ? undefined
                            : currentOption.sizeCvr
                        }
                        onValueChange={(value: number) =>
                          setFieldValue(`sampleSizes[${contest.id}]`, {
                            ...currentOption,
                            sizeCvr: value,
                            size: (currentOption.sizeNonCvr || 0) + value,
                          })
                        }
                        type="number"
                        // We rely on backend validation in this
                        // case, since we don't have the total
                        // CVR/non-CVR ballots loaded in the
                        // frontend
                        validate={testNumber()}
                        disabled={locked}
                      />
                    </label>
                  </div>
                  <div style={{ marginTop: '10px' }}>
                    {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
                    <label style={{ marginTop: '5px' }}>
                      Non-CVR ballots:
                      <Field
                        component={FormField}
                        name={`sampleSizes[${contest.id}].sizeNonCvr`}
                        value={
                          currentOption.sizeNonCvr === null
                            ? undefined
                            : currentOption.sizeNonCvr
                        }
                        onValueChange={(value: number) =>
                          setFieldValue(`sampleSizes[${contest.id}]`, {
                            ...currentOption,
                            sizeNonCvr: value,
                            size: (currentOption.sizeCvr || 0) + value,
                          })
                        }
                        type="number"
                        validate={testNumber()}
                        disabled={locked}
                      />
                    </label>
                  </div>
                </>
              ) : (
                <Field
                  component={FormField}
                  name={`sampleSizes[${contest.id}].size`}
                  value={
                    currentOption.size === null ? undefined : currentOption.size
                  }
                  onValueChange={(value: number) =>
                    setFieldValue(`sampleSizes[${contest.id}].size`, value)
                  }
                  type="number"
                  validate={testNumber(
                    fullHandTallySize,
                    `Must be less than or equal to ${fullHandTallySize} (the total number of ${
                      auditType === 'BATCH_COMPARISON' ? 'batches' : 'ballots'
                    } in the contest)`
                  )}
                  disabled={locked}
                />
              ))}
          </Card>
        )
      })}
    </div>
  )
}

export default Review

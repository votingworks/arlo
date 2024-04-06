import React, { useState } from 'react'
import { H2, Button, H4, Checkbox, HTMLSelect } from '@blueprintjs/core'
import {
  useQueryClient,
  useMutation,
  useQuery,
  UseQueryResult,
  UseMutationResult,
} from 'react-query'
import styled from 'styled-components'
import { useParams, Link } from 'react-router-dom'
import { Wrapper, Inner } from '../Atoms/Wrapper'
import FileUpload from '../Atoms/FileUpload'
import { fetchApi } from '../../utils/api'
import AsyncButton from '../Atoms/AsyncButton'
import { CvrFileType, FileProcessingStatus } from '../useCSV'
import {
  IFileUpload,
  useUploadFiles,
  useDeleteFile,
  useUploadedFile,
} from '../useFileUpload'
import { apiDownload, assert } from '../utilities'
import LinkButton from '../Atoms/LinkButton'
import {
  StepPanel,
  StepActions,
  Steps,
  StepList,
  StepListItem,
  stepState,
  StepPanelColumn,
} from '../Atoms/Steps'
import { Column, Row } from '../Atoms/Layout'
import {
  BatchInventoryConfig,
  useBatchInventoryFeatureFlag,
} from '../useFeatureFlag'

type Step =
  | 'Select System Type'
  | 'Upload Election Results'
  | 'Inventory Batches'
  | 'Download Audit Files'

const STEPS: Step[] = [
  'Select System Type',
  'Upload Election Results',
  'Inventory Batches',
  'Download Audit Files',
]

const STEPS_IF_NOT_SHOWING_BALLOT_MANIFEST: Step[] = [
  'Select System Type',
  'Upload Election Results',
  'Download Audit Files',
]

const isUploaded = (fileUpload: IFileUpload) =>
  fileUpload.uploadedFile.data?.processing?.status ===
  FileProcessingStatus.PROCESSED

function areAllFilesUploaded({
  systemType,
  cvrUpload,
  tabulatorStatusUpload,
}: {
  systemType: CvrFileType
  cvrUpload: IFileUpload
  tabulatorStatusUpload: IFileUpload
}): boolean {
  if (systemType === CvrFileType.DOMINION) {
    return isUploaded(cvrUpload) && isUploaded(tabulatorStatusUpload)
  }
  return isUploaded(cvrUpload)
}

const DATA_TYPES = ['systemType', 'cvr', 'tabulatorStatus', 'signOff'] as const
type DataType = typeof DATA_TYPES[number]

function batchInventoryQueryKey(
  jurisdictionId: string,
  dataType: DataType
): string[] {
  return ['batchInventory', jurisdictionId, dataType]
}

interface ISystemTypeQueries {
  systemType: UseQueryResult<CvrFileType | null>
  setSystemType: UseMutationResult<CvrFileType, unknown, CvrFileType, unknown>
}

const useBatchInventorySystemType = (
  electionId: string,
  jurisdictionId: string
): ISystemTypeQueries => {
  const key = batchInventoryQueryKey(jurisdictionId, 'systemType')
  const url = `/api/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory/system-type`
  const queryClient = useQueryClient()
  return {
    systemType: useQuery<CvrFileType | null>(
      key,
      async () => (await fetchApi(url)).systemType
    ),
    setSystemType: useMutation(
      (systemType: CvrFileType) =>
        fetchApi(url, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ systemType }),
        }),
      {
        onSuccess: () =>
          Promise.all(
            // All batch inventory data is invalidated when the system type is changed
            DATA_TYPES.map(dataType =>
              queryClient.invalidateQueries(
                batchInventoryQueryKey(jurisdictionId, dataType)
              )
            )
          ),
      }
    ),
  }
}

const useBatchInventoryCVR = (
  electionId: string,
  jurisdictionId: string
): IFileUpload => {
  const key = batchInventoryQueryKey(jurisdictionId, 'cvr')
  const url = `/api/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory/cvr`
  const uploadFiles = useUploadFiles(key, url)
  const deleteFile = useDeleteFile(key, url)
  const queryClient = useQueryClient()
  return {
    uploadedFile: useUploadedFile(key, url, {
      onFileChange: () =>
        Promise.all(
          // Changing the CVR file requires reprocessing the tabulator status file, if uploaded,
          // and resetting the sign-off status
          (['tabulatorStatus', 'signOff'] as const).map(dataType =>
            queryClient.invalidateQueries(
              batchInventoryQueryKey(jurisdictionId, dataType)
            )
          )
        ),
    }),
    uploadFiles: files => {
      const formData = new FormData()
      formData.append('cvr', files[0], files[0].name)
      return uploadFiles.mutateAsync(formData)
    },
    uploadProgress: uploadFiles.progress,
    deleteFile: () => deleteFile.mutateAsync(),
    downloadFileUrl: `${url}/file`,
  }
}

const useBatchInventoryTabulatorStatus = (
  electionId: string,
  jurisdictionId: string
): IFileUpload => {
  const key = batchInventoryQueryKey(jurisdictionId, 'tabulatorStatus')
  const url = `/api/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory/tabulator-status`
  const uploadFiles = useUploadFiles(key, url)
  const deleteFile = useDeleteFile(key, url)
  const queryClient = useQueryClient()
  return {
    uploadedFile: useUploadedFile(key, url, {
      onFileChange: () =>
        // Changing the tabulator status file resets the sign-off status
        queryClient.invalidateQueries(
          batchInventoryQueryKey(jurisdictionId, 'signOff')
        ),
    }),
    uploadFiles: files => {
      const formData = new FormData()
      formData.append('tabulatorStatus', files[0], files[0].name)
      return uploadFiles.mutateAsync(formData)
    },
    uploadProgress: uploadFiles.progress,
    deleteFile: () => deleteFile.mutateAsync(),
    downloadFileUrl: `${url}/file`,
  }
}

interface ISignOffQueries {
  status: UseQueryResult<{ signedOffAt: string | null }>
  signOff: UseMutationResult<void, unknown, void, unknown>
  undoSignOff: UseMutationResult<void, unknown, void, unknown>
}

const useBatchInventorySignOff = (
  electionId: string,
  jurisdictionId: string
): ISignOffQueries => {
  const key = batchInventoryQueryKey(jurisdictionId, 'signOff')
  const url = `/api/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory/sign-off`
  const queryClient = useQueryClient()
  const status = useQuery<{ signedOffAt: string | null }>(key, () =>
    fetchApi(url)
  )
  const signOff = useMutation(() => fetchApi(url, { method: 'POST' }), {
    onSuccess: () => queryClient.invalidateQueries(key),
  })
  const undoSignOff = useMutation(() => fetchApi(url, { method: 'DELETE' }), {
    onSuccess: () => queryClient.invalidateQueries(key),
  })
  return {
    status,
    signOff,
    undoSignOff,
  }
}

const SelectSystemStep: React.FC<{
  systemTypeQueries: ISystemTypeQueries
  nextStep: () => void
}> = ({ systemTypeQueries, nextStep }) => {
  if (!systemTypeQueries.systemType.isSuccess) {
    return null
  }

  const systemType = systemTypeQueries.systemType.data

  const setSystemType = async (event: React.ChangeEvent<HTMLSelectElement>) => {
    const newSystemType = event.target.value as CvrFileType
    await systemTypeQueries.setSystemType.mutateAsync(newSystemType)
  }

  return (
    <>
      <StepPanel>
        <Row alignItems="center" gap="10px" justifyContent="center">
          <span>Select your voting system:</span>
          <HTMLSelect
            large
            onChange={setSystemType}
            value={systemType ?? undefined}
          >
            {!systemType && <option value={undefined}></option>}
            <option value={CvrFileType.DOMINION}>Dominion</option>
            {/* eslint-disable-next-line react/jsx-curly-brace-presence */}
            <option value={CvrFileType.ESS}>{'ES&S'}</option>
          </HTMLSelect>
        </Row>
      </StepPanel>
      <StepActions
        right={
          <Button
            disabled={!systemType}
            intent="primary"
            onClick={nextStep}
            rightIcon="chevron-right"
          >
            Continue
          </Button>
        }
      />
    </>
  )
}

const UploadElectionResultsStep: React.FC<{
  systemType: CvrFileType
  cvrUpload: IFileUpload
  tabulatorStatusUpload: IFileUpload
  prevStep: () => void
  nextStep: () => void
}> = ({ systemType, cvrUpload, tabulatorStatusUpload, prevStep, nextStep }) => {
  return (
    <>
      {systemType === CvrFileType.DOMINION && (
        <StepPanel>
          <StepPanelColumn>
            <FileUpload
              title="Cast Vote Records (CVR)"
              {...cvrUpload}
              acceptFileTypes={['csv']}
            />
          </StepPanelColumn>
          <StepPanelColumn>
            <FileUpload
              title="Tabulator Status"
              {...tabulatorStatusUpload}
              acceptFileTypes={['xml']}
              uploadDisabled={!isUploaded(cvrUpload)}
            />
          </StepPanelColumn>
        </StepPanel>
      )}
      {systemType === CvrFileType.ESS && (
        <StepPanel>
          <StepPanelColumn>
            <FileUpload
              title="Cast Vote Records (CVR)"
              {...cvrUpload}
              acceptFileTypes={['csv', 'zip']}
            />
          </StepPanelColumn>
        </StepPanel>
      )}
      <StepActions
        left={
          <Button icon="chevron-left" onClick={prevStep}>
            Back
          </Button>
        }
        right={
          <Button
            onClick={nextStep}
            intent="primary"
            disabled={
              !areAllFilesUploaded({
                systemType,
                cvrUpload,
                tabulatorStatusUpload,
              })
            }
            rightIcon="chevron-right"
          >
            Continue
          </Button>
        }
      />
    </>
  )
}

const InventoryBatchesStep: React.FC<{
  worksheetUrl: string
  signOffQueries: ISignOffQueries
  prevStep: () => void
  nextStep: () => void
}> = ({ prevStep, nextStep, signOffQueries, worksheetUrl }) => {
  if (!signOffQueries.status.isSuccess) return null

  const isSignedOff = signOffQueries.status.data.signedOffAt !== null

  const onSignOffToggle = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    if (event.target.checked) {
      await signOffQueries.signOff.mutateAsync()
    } else {
      await signOffQueries.undoSignOff.mutateAsync()
    }
  }

  return (
    <>
      <StepPanel>
        <Column justifyContent="center" alignItems="center">
          <p>
            Follow the instructions in the worksheet to inventory your batches.
          </p>
          <p>
            <AsyncButton
              intent="primary"
              large
              icon="download"
              onClick={() => apiDownload(worksheetUrl)}
            >
              Download Batch Inventory Worksheet
            </AsyncButton>
          </p>
          <br />
          <p>
            <Checkbox large onChange={onSignOffToggle} checked={isSignedOff}>
              <span>I have completed the batch inventory worksheet.</span>
            </Checkbox>
          </p>
        </Column>
      </StepPanel>
      <StepActions
        left={
          <Button icon="chevron-left" onClick={prevStep}>
            Back
          </Button>
        }
        right={
          <Button
            disabled={!isSignedOff}
            onClick={nextStep}
            intent="primary"
            rightIcon="chevron-right"
            style={{ marginLeft: '10px' }}
          >
            Continue
          </Button>
        }
      />
    </>
  )
}

const DownloadAuditFilesStep: React.FC<{
  showBallotManifest: boolean
  ballotManifestUrl: string
  batchTalliesUrl: string
  prevStep: () => void
}> = ({ showBallotManifest, ballotManifestUrl, batchTalliesUrl, prevStep }) => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()
  return (
    <>
      <StepPanel>
        <Column
          justifyContent="center"
          alignItems="center"
          style={{ maxWidth: '50%' }}
        >
          <H4>Batch Audit File Preparation Complete</H4>
          {showBallotManifest ? (
            <p style={{ marginBottom: '15px' }}>
              Next, download the Ballot Manifest and Candidate Totals by Batch
              files, and upload them on the{' '}
              <Link
                to={`/election/${electionId}/jurisdiction/${jurisdictionId}`}
              >
                Audit Setup
              </Link>{' '}
              page.
            </p>
          ) : (
            <p style={{ marginBottom: '15px' }}>
              Next, download this file and upload it on the{' '}
              <Link
                to={`/election/${electionId}/jurisdiction/${jurisdictionId}`}
              >
                Audit Setup
              </Link>{' '}
              page.
            </p>
          )}
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {showBallotManifest && (
              <AsyncButton
                intent="primary"
                large
                icon="download"
                onClick={() => apiDownload(ballotManifestUrl)}
                style={{ marginBottom: '10px' }}
              >
                Download Ballot Manifest
              </AsyncButton>
            )}
            <AsyncButton
              intent="primary"
              large
              icon="download"
              onClick={() => apiDownload(batchTalliesUrl)}
            >
              Download Candidate Totals by Batch
            </AsyncButton>
          </div>
        </Column>
      </StepPanel>
      <StepActions
        left={
          <Button icon="chevron-left" onClick={prevStep}>
            Back
          </Button>
        }
        right={
          <LinkButton
            to={`/election/${electionId}/jurisdiction/${jurisdictionId}`}
            intent="primary"
            rightIcon="chevron-right"
          >
            Return to Audit Setup
          </LinkButton>
        }
      />
    </>
  )
}

const HeadingRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
`

const BatchInventorySteps: React.FC<{
  batchInventoryConfig: BatchInventoryConfig
  systemTypeQueries: ISystemTypeQueries
  cvrUpload: IFileUpload
  tabulatorStatusUpload: IFileUpload
  signOffQueries: ISignOffQueries
}> = ({
  batchInventoryConfig,
  systemTypeQueries,
  cvrUpload,
  tabulatorStatusUpload,
  signOffQueries,
}) => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()

  const steps = batchInventoryConfig.showBallotManifest
    ? STEPS
    : STEPS_IF_NOT_SHOWING_BALLOT_MANIFEST

  // Start on the step that's most relevant given progress so far (e.g. if the
  // user left and came back)
  const systemType = systemTypeQueries.systemType.data
  const isSignedOff = signOffQueries.status.data?.signedOffAt !== null
  const initialStep = !systemType
    ? 'Select System Type'
    : !areAllFilesUploaded({ systemType, cvrUpload, tabulatorStatusUpload })
    ? 'Upload Election Results'
    : batchInventoryConfig.showBallotManifest && !isSignedOff
    ? 'Inventory Batches'
    : 'Download Audit Files'

  const [currentStep, setCurrentStep] = useState<Step>(initialStep)
  const currentStepNumber = steps.indexOf(currentStep) + 1

  return (
    <Wrapper>
      <Inner withTopPadding flexDirection="column">
        <HeadingRow>
          <H2>Batch Audit File Preparation Tool</H2>
          <LinkButton
            minimal
            to={`/election/${electionId}/jurisdiction/${jurisdictionId}`}
            icon="chevron-left"
          >
            Back to Audit Setup
          </LinkButton>
        </HeadingRow>
        <Steps>
          <StepList>
            {steps.map((step, index) => (
              <StepListItem
                key={step}
                stepNumber={index + 1}
                state={stepState(index + 1, currentStepNumber)}
              >
                {step}
              </StepListItem>
            ))}
          </StepList>
          {(() => {
            switch (currentStep) {
              case 'Select System Type':
                return (
                  <SelectSystemStep
                    systemTypeQueries={systemTypeQueries}
                    nextStep={() => setCurrentStep('Upload Election Results')}
                  />
                )
              case 'Upload Election Results': {
                assert(systemType !== undefined && systemType !== null)
                return (
                  <UploadElectionResultsStep
                    systemType={systemType}
                    cvrUpload={cvrUpload}
                    tabulatorStatusUpload={tabulatorStatusUpload}
                    prevStep={() => setCurrentStep('Select System Type')}
                    nextStep={() =>
                      setCurrentStep(
                        batchInventoryConfig.showBallotManifest
                          ? 'Inventory Batches'
                          : 'Download Audit Files'
                      )
                    }
                  />
                )
              }
              case 'Inventory Batches':
                return (
                  <InventoryBatchesStep
                    worksheetUrl={`/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory/worksheet`}
                    signOffQueries={signOffQueries}
                    prevStep={() => setCurrentStep('Upload Election Results')}
                    nextStep={() => setCurrentStep('Download Audit Files')}
                  />
                )
              case 'Download Audit Files': {
                return (
                  <DownloadAuditFilesStep
                    showBallotManifest={batchInventoryConfig.showBallotManifest}
                    ballotManifestUrl={`/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory/ballot-manifest`}
                    batchTalliesUrl={`/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory/batch-tallies`}
                    prevStep={() =>
                      setCurrentStep(
                        batchInventoryConfig.showBallotManifest
                          ? 'Inventory Batches'
                          : 'Upload Election Results'
                      )
                    }
                  />
                )
              }
              default:
                throw new Error('Unknown step')
            }
          })()}
        </Steps>
      </Inner>
    </Wrapper>
  )
}

const BatchInventory: React.FC = () => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()
  const systemTypeQueries = useBatchInventorySystemType(
    electionId,
    jurisdictionId
  )
  const cvrUpload = useBatchInventoryCVR(electionId, jurisdictionId)
  const tabulatorStatusUpload = useBatchInventoryTabulatorStatus(
    electionId,
    jurisdictionId
  )
  const signOffQueries = useBatchInventorySignOff(electionId, jurisdictionId)
  const batchInventoryConfig = useBatchInventoryFeatureFlag(jurisdictionId)
  assert(batchInventoryConfig !== undefined)

  if (
    !(
      systemTypeQueries.systemType.isSuccess &&
      cvrUpload.uploadedFile.isSuccess &&
      tabulatorStatusUpload.uploadedFile.isSuccess &&
      signOffQueries.status.isSuccess
    )
  ) {
    return null
  }

  return (
    <BatchInventorySteps
      batchInventoryConfig={batchInventoryConfig}
      systemTypeQueries={systemTypeQueries}
      cvrUpload={cvrUpload}
      tabulatorStatusUpload={tabulatorStatusUpload}
      signOffQueries={signOffQueries}
    />
  )
}

export default BatchInventory
